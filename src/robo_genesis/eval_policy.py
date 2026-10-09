"""Policy-agnostic closed-loop evaluation of a trained LeRobot policy.

Runs a trained policy (ACT, SmolVLA, or another compatible LeRobot policy) in
the project Genesis pick-and-place scene. The command audits the dataset,
checkpoint, and rollout protocol before initializing Genesis; sharing a scene
builder with recording is not treated as proof that every condition matches.

The script is deliberately *policy-agnostic*: it never hard-codes ACT- or
SmolVLA-specific logic. Instead it relies on lerobot's generic interfaces, and
is organized as a few thin layers:

  1. Policy layer   -- load any checkpoint via ``PreTrainedConfig`` + ``make_policy``
                       + ``make_pre_post_processors``. The only per-policy detail
                       (normalization, image resize, temporal ensembling, language
                       conditioning) lives inside the loaded processors/policy.
  2. Observation    -- ``build_observation`` reads the sim into the exact feature
     layer            keys the dataset used (state + camera images), as raw numpy.
                       ``predict_action`` (lerobot) then converts/normalizes them.
  3. Action layer   -- the policy emits the dataset's action vector (9-D joint
                       targets); ``apply_action`` position-controls the arm+gripper.
  4. Rollout layer  -- ``run_episode`` steps the sim, decimating the 100 Hz control
                       loop down to the policy's fps, and checks task success.

The dataset the policy was trained on is used only to recover feature shapes,
normalization stats and fps (via ``LeRobotDatasetMetadata``); no episodes are read.

Usage:
    uv run python -m robo_genesis.eval_policy \
        --policy-path outputs/train/act_banana/checkpoints/last/pretrained_model \
        --repo-id genesis/banana_pick \
        --dataset-root datasets/banana_pick \
        --episodes 20 --pick 011_banana

    # SmolVLA is identical -- only the checkpoint changes:
    uv run python -m robo_genesis.eval_policy \
        --policy-path outputs/train/smolvla_banana/checkpoints/last/pretrained_model \
        --repo-id genesis/banana_pick --dataset-root .../banana_pick --episodes 20
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import torch

import genesis as gs
from lerobot.common.control_utils import predict_action
from lerobot.configs.policies import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDatasetMetadata
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.utils.device_utils import get_safe_torch_device

from .build_scene import build_scene
from .evaluation_contract import (
    DwellTracker,
    EvaluationContractError,
    audit_dataset_contract,
    build_condition_spec,
    build_evaluation_report,
    dwell_frame_count,
    git_identity,
    normalize_policy_action,
    require_requested_device,
    validate_evaluation_protocol,
    validate_output_targets,
)
from .grasp_demo import TaskSpec, check_success
from .paths import DATASETS_DIR, EVAL_RESULTS_DIR, EVAL_VIDEOS_DIR, PROJECT_ROOT, resolve_cli_path
from .randomize import DomainRandomizationConfig, EnvRandomizer, RandomizationConfig
from .record_dataset import CONTROL_FPS, task_description
from .scene_config import YCB_LAYOUT
from .stats import wilson
from .training_contract import audit_checkpoint

STATE_KEY = "observation.state"

# After success is declared, keep recording (and holding the last action) for this long
# so the saved video shows the object resting in the bowl instead of cutting off the
# instant placement is confirmed. Purely cosmetic: does not affect success/step counts.
POST_SUCCESS_SECONDS = 0.8


@dataclass
class PolicyBundle:
    """A loaded policy plus everything needed to run inference on it."""

    policy: object
    preprocessor: object
    postprocessor: object
    device: torch.device
    fps: int
    image_keys: list[str]
    image_hw: tuple[int, int]  # (height, width) the dataset stored images at
    use_amp: bool = False
    policy_type: str = "unknown"

    def reset(self) -> None:
        self.policy.reset()

    def select_action(self, observation: dict[str, np.ndarray], task: str | None) -> np.ndarray:
        """Run one inference step; returns the action as a 1-D numpy array."""
        action = predict_action(
            observation,
            self.policy,
            self.device,
            self.preprocessor,
            self.postprocessor,
            use_amp=self.use_amp,
            task=task,
            robot_type="franka",
        )
        raw_action = action.detach().cpu().numpy()
        values = normalize_policy_action(raw_action)
        return np.asarray(values, dtype=np.float32)


def _load_rename_map(policy_path: str) -> dict:
    """Best-effort recovery of the training-time camera rename_map from a checkpoint.

    Policies fine-tuned from a base with canonical camera keys (e.g. SmolVLA's
    ``camera1/2/3``) are trained with a ``rename_map`` that is baked into the saved
    preprocessor, so at inference the raw dataset keys (``world``/``wrist``) are
    renamed transparently. ``make_policy``'s feature-consistency check, however,
    must be given the same map or it rejects the raw keys. We read it back from the
    checkpoint's ``train_config.json`` so eval needs no extra flags.
    """
    p = Path(policy_path) / "train_config.json"
    if p.is_file():
        try:
            return json.loads(p.read_text()).get("rename_map") or {}
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def load_policy(
    policy_path: str,
    repo_id: str,
    dataset_root: str | None,
    device_str: str,
    *,
    use_amp: bool = False,
    rename_map: dict | None = None,
) -> PolicyBundle:
    """Generically load any lerobot policy checkpoint for closed-loop inference.

    ``dataset_root`` points at the *local* dataset the policy was trained on; its
    metadata supplies feature shapes, normalization stats and fps. This keeps the
    eval consistent with training without re-reading any episode data.
    """
    device = get_safe_torch_device(device_str, log=True)

    ds_meta = LeRobotDatasetMetadata(repo_id, root=dataset_root)

    cfg = PreTrainedConfig.from_pretrained(policy_path)
    cfg.pretrained_path = policy_path
    cfg.device = str(device)

    # Recover the training-time camera rename (if any). Passing it to make_policy
    # both skips the raw-key feature-consistency check and matches how the model was
    # trained; the rename itself is already baked into the loaded preprocessor.
    if rename_map is None:
        rename_map = _load_rename_map(policy_path)
    if rename_map:
        print(f"[eval] camera rename_map: {rename_map}")

    policy = make_policy(cfg=cfg, ds_meta=ds_meta, rename_map=rename_map)
    policy.eval()

    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=cfg,
        pretrained_path=policy_path,
        preprocessor_overrides={"device_processor": {"device": str(device)}},
    )

    image_keys = [k for k in ds_meta.features if k.startswith("observation.images")]
    if not image_keys:
        raise RuntimeError(f"No image features found in dataset {repo_id!r}.")
    h, w, _ = ds_meta.features[image_keys[0]]["shape"]

    print(
        f"[eval] loaded {cfg.type} policy from {policy_path}\n"
        f"       device={device} fps={ds_meta.fps} images={image_keys} @ {w}x{h}"
    )
    return PolicyBundle(
        policy=policy,
        preprocessor=preprocessor,
        postprocessor=postprocessor,
        device=device,
        fps=ds_meta.fps,
        image_keys=image_keys,
        image_hw=(h, w),
        use_amp=use_amp,
        policy_type=cfg.type,
    )


def _to_np(x) -> np.ndarray:
    if hasattr(x, "detach"):
        x = x.detach().cpu().numpy()
    return np.asarray(x)


def _render_camera(cam, size_wh: tuple[int, int]) -> np.ndarray:
    img = _to_np(cam.render(rgb=True)[0])
    w, h = size_wh
    if (img.shape[1], img.shape[0]) != (w, h):
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    return np.ascontiguousarray(img, dtype=np.uint8)


def build_observation(bundle, pb: PolicyBundle) -> dict[str, np.ndarray]:
    """Read the current sim state into the dataset's raw feature layout (numpy).

    Images are returned HWC uint8 and the state is a float32 vector -- exactly the
    format ``predict_action`` expects before it tensorizes / normalizes them.
    """
    h, w = pb.image_hw
    obs: dict[str, np.ndarray] = {
        STATE_KEY: _to_np(bundle.franka.get_qpos()).reshape(-1).astype(np.float32),
    }
    cam_for_key = {
        "observation.images.world": bundle.world_cam,
        "observation.images.wrist": bundle.wrist_cam,
    }
    for key in pb.image_keys:
        cam = cam_for_key.get(key)
        if cam is None:
            raise RuntimeError(f"Dataset expects camera {key!r} but the scene has no such camera.")
        obs[key] = _render_camera(cam, (w, h))
    return obs


def _record_frame(bundle, pb: PolicyBundle, obs: dict[str, np.ndarray]) -> np.ndarray:
    """Compose one saved-video frame as a 1x3 row: the policy's primary (world) camera,
    the wrist (eye-in-hand) camera, and the cosmetic third-person ``video_cam`` -- side by
    side, each resized to the primary panel's size. Cameras that are absent are skipped
    (so this gracefully degrades to fewer panels). The wrist/video panels are only for
    visualization; the video camera is never part of the observation fed to the policy.
    """
    primary = obs[pb.image_keys[0]]
    h, w = primary.shape[:2]
    panels = [primary]
    if bundle.wrist_cam is not None:
        panels.append(_render_camera(bundle.wrist_cam, (w, h)))
    if bundle.video_cam is not None:
        panels.append(_render_camera(bundle.video_cam, (w, h)))
    if len(panels) == 1:
        return primary.copy()
    return np.ascontiguousarray(np.hstack(panels))


def apply_action(bundle, action: np.ndarray, n_sim_steps: int) -> None:
    """Position-control the arm+gripper to the policy's target for ``n_sim_steps``."""
    action = np.asarray(action, dtype=np.float64)
    for _ in range(n_sim_steps):
        bundle.franka.control_dofs_position(action)
        bundle.scene.step()
        bundle.update_wrist_cam()


@dataclass
class EpisodeResult:
    success: bool
    frames: list[np.ndarray] = field(default_factory=list)
    n_policy_steps: int = 0
    termination_reason: str = "timeout"
    error: str | None = None
    dwell_frames: int = 0
    max_success_streak: int = 0


def run_episode(
    bundle,
    pb: PolicyBundle,
    task: TaskSpec,
    *,
    task_text: str | None,
    max_seconds: float,
    dwell_seconds: float = 0.4,
    record_video: bool = False,
) -> EpisodeResult:
    """Run one closed-loop rollout and return whether the task succeeded.

    The policy is queried at ``pb.fps``; between queries the commanded action is
    held while the sim advances at ``CONTROL_FPS``. A fractional accumulator keeps
    the average control:policy step ratio exact (e.g. 100/30).
    """
    pb.reset()

    steps_per_frame = CONTROL_FPS / pb.fps
    max_frames = max(1, int(np.ceil(max_seconds * pb.fps)))

    settle_frames = dwell_frame_count(dwell_seconds, pb.fps)
    result = EpisodeResult(success=False, dwell_frames=settle_frames)
    accum = 0.0
    # Require the (containment) success condition to hold for a short dwell (~0.4 s)
    # before declaring success, so we only stop once the object has actually come to
    # rest inside the bowl -- not during the fly-by/descent. This also keeps the
    # recorded video running through the settle, so the placement is visible.
    dwell = DwellTracker(settle_frames)
    for _ in range(max_frames):
        obs = build_observation(bundle, pb)
        if record_video:
            result.frames.append(_record_frame(bundle, pb, obs))

        try:
            action = pb.select_action(obs, task_text)
        except (EvaluationContractError, TypeError, ValueError, OverflowError) as exc:
            result.termination_reason = "invalid_action"
            result.error = str(exc)
            break

        accum += steps_per_frame
        n_sub = int(accum)
        accum -= n_sub
        apply_action(bundle, action, max(1, n_sub))
        result.n_policy_steps += 1

        if dwell.update(bool(check_success(bundle, task))):
            result.success = True
            result.termination_reason = "success"
            break

    result.max_success_streak = dwell.max_streak

    # Cosmetic tail: after a successful placement, hold the last action and keep
    # recording for a short window so the resting object is clearly visible in the video.
    if result.success and record_video:
        hold_frames = max(1, int(round(POST_SUCCESS_SECONDS * pb.fps)))
        for _ in range(hold_frames):
            apply_action(bundle, action, max(1, int(round(steps_per_frame))))
            obs = build_observation(bundle, pb)
            result.frames.append(_record_frame(bundle, pb, obs))

    return result


def _save_video(frames: list[np.ndarray], path: Path, fps: int) -> None:
    """Write an H.264 (yuv420p) mp4 so the file plays in browsers / VSCode's viewer.

    The old cv2 ``mp4v`` (MPEG-4 Part 2) codec is not decodable by the HTML5 video
    player VSCode uses, so we encode with libx264 via imageio-ffmpeg. H.264 + yuv420p
    also requires even frame dimensions, so odd width/height are cropped by one pixel.
    """
    if not frames:
        return
    import imageio.v2 as imageio

    path.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames[0].shape[:2]
    h_even, w_even = h - (h % 2), w - (w % 2)
    writer = imageio.get_writer(
        str(path),
        fps=fps,
        codec="libx264",
        format="ffmpeg",
        pixelformat="yuv420p",
        macro_block_size=None,
    )
    try:
        for f in frames:
            writer.append_data(np.ascontiguousarray(f[:h_even, :w_even]))
    finally:
        writer.close()


def _domain_draw(randomizer: EnvRandomizer) -> dict[str, object] | None:
    """Return the runtime-domain values actually sampled for the current episode."""
    friction = getattr(randomizer, "last_friction_ratio", None)
    masses = getattr(randomizer, "last_mass_ratio", None)
    camera = getattr(randomizer, "last_world_camera_pose", None)
    if friction is None and not masses and camera is None:
        return None
    return {
        "friction_ratio": friction,
        "mass_ratios": dict(masses or {}),
        "world_camera_pose": camera,
    }


def evaluate_policy(
    bundle,
    pb: PolicyBundle,
    *,
    episodes: int,
    seed: int = 1000,
    max_seconds: float = 15.0,
    dwell_seconds: float = 0.4,
    pick: list[str] | tuple[str, ...] = ("011_banana",),
    place: str = "024_bowl",
    tol: float = 0.06,
    no_task: bool = False,
    jitter: float = 0.03,
    balanced: bool = True,
    randomizer: EnvRandomizer | None = None,
    save_video: bool = False,
    video_dir: Path | None = None,
    label: str = "",
    protocol: dict | None = None,
) -> dict:
    """Run ``episodes`` closed-loop rollouts and return a structured results dict.

    Reusing ``seed`` and all other protocol fields gives matched scheduled task
    instances across checkpoints or conditions. It controls one source of variation;
    it does not imply identical trajectories or isolate every training difference.

    ``balanced`` (default) assigns objects via a stratified schedule so each object gets
    an (almost) equal number of episodes -- ``episodes // len(pick)`` each, with any
    remainder handed to a ``seed``-drawn subset -- then ``seed``-shuffles the order. This
    equalizes per-object sample sizes (and hence per-object CI widths) instead of leaving
    them to a Multinomial draw. Set ``balanced=False`` to recover the legacy i.i.d.
    ``pick_rng.choice`` sampling (needed to reproduce sweeps run before this option).
    """
    if protocol is None:
        protocol = validate_evaluation_protocol(
            episodes=episodes,
            policy_fps=pb.fps,
            control_fps=CONTROL_FPS,
            dwell_seconds=dwell_seconds,
            max_seconds=max_seconds,
            tolerance=tol,
            pick_objects=pick,
            place_target=place,
            available_objects=tuple(bundle.ycb),
            base_seed=seed,
            balanced=balanced,
            condition_name=(label or "reference").replace(":", "-"),
            render_enabled=True,
        )
    if randomizer is None:
        randomizer = EnvRandomizer(
            bundle, RandomizationConfig(pos_jitter=jitter, randomize_pick=False, seed=seed)
        )
    pick_rng = np.random.default_rng(seed)
    pick_choices = list(pick)
    # Balanced mode: build a stratified, seed-shuffled schedule up front (equal n per object,
    # remainder distributed to a seeded subset). Legacy mode leaves schedule=None and draws
    # i.i.d. inside the loop, preserving the exact sequence of earlier runs.
    schedule = protocol["sampling"]["object_schedule"] if balanced else None
    prefix = f"[eval:{label}]" if label else "[eval]"

    n_success = 0
    n_diverged = 0
    n_invalid_action = 0
    per_object: dict[str, list[int]] = {}
    episodes_detail: list[dict] = []
    for ep in range(episodes):
        episode_seed = seed + ep
        # Pick is drawn from its own RNG (independent of the randomizer), so sampling it up
        # front keeps the sequence identical while making pick_object available even if the
        # reset/rollout below raises. Balanced mode reads the pre-built schedule; legacy mode
        # draws i.i.d. here (byte-identical to pre-`balanced` runs).
        pick_object = str(schedule[ep]) if schedule is not None else str(pick_rng.choice(pick_choices))
        task = TaskSpec(pick_object=pick_object, place_target=place, success_tol=tol)
        task_text = None if no_task else task_description(pick_object)

        try:
            randomizer.reset(seed=episode_seed)
            domain_draw = _domain_draw(randomizer)
            result = run_episode(
                bundle, pb, task,
                task_text=task_text,
                max_seconds=max_seconds,
                dwell_seconds=dwell_seconds,
                record_video=save_video,
            )
        except gs.GenesisException as exc:
            # A physics divergence (NaN forces/accelerations, e.g. a stiff contact under
            # aggressive Layer-B friction/mass DR) must abort only this episode -- not the whole
            # sweep. It is counted as a failure and flagged. The next episode's randomizer.reset()
            # rewrites all poses to finite values with zero velocity and clears the solver error
            # flag, so the sim self-heals without a rebuild.
            n_diverged += 1
            per_object.setdefault(pick_object, []).append(0)
            episodes_detail.append(
                {
                    "ep": ep,
                    "seed": episode_seed,
                    "pick": pick_object,
                    "steps": 0,
                    "success": False,
                    "diverged": True,
                    "termination_reason": "diverged",
                    "error": str(exc),
                    "condition": label or "reference",
                    "domain_draw": _domain_draw(randomizer),
                    "video": None,
                }
            )
            print(
                f"{prefix} ep {ep:03d} seed={episode_seed} pick={pick_object} "
                f"-> DIVERGED ({exc}); counted as failure"
            )
            continue

        n_success += int(result.success)
        n_invalid_action += int(result.termination_reason == "invalid_action")
        per_object.setdefault(pick_object, []).append(int(result.success))
        video_path: Path | None = None
        if save_video and video_dir is not None:
            tag = "success" if result.success else result.termination_reason
            video_path = Path(video_dir) / f"ep{ep:03d}_{pick_object}_{tag}.mp4"
            _save_video(result.frames, video_path, pb.fps)

        episodes_detail.append(
            {
                "ep": ep,
                "seed": episode_seed,
                "pick": pick_object,
                "steps": result.n_policy_steps,
                "success": bool(result.success),
                "diverged": False,
                "termination_reason": result.termination_reason,
                "error": result.error,
                "condition": label or "reference",
                "domain_draw": domain_draw,
                "dwell_frames": result.dwell_frames,
                "max_success_streak": result.max_success_streak,
                "video": str(video_path) if video_path is not None else None,
            }
        )

        print(
            f"{prefix} ep {ep:03d} seed={episode_seed} pick={pick_object} "
            f"steps={result.n_policy_steps} -> {result.termination_reason}"
        )

    rate = n_success / max(1, episodes)
    ci_lo, ci_hi = wilson(n_success, episodes)  # 95% Wilson score interval over the episodes
    diverged_note = f" ({n_diverged} diverged)" if n_diverged else ""
    print(
        f"{prefix} success rate: {n_success}/{episodes} = {rate:.1%} "
        f"[95% CI {ci_lo:.1%}, {ci_hi:.1%}]{diverged_note}"
    )
    per_object_summary = {}
    for obj, hits in sorted(per_object.items()):
        o_lo, o_hi = wilson(int(sum(hits)), len(hits))
        per_object_summary[obj] = {
            "n": len(hits), "success": int(sum(hits)), "rate": sum(hits) / len(hits),
            "ci": [o_lo, o_hi],
        }
    if len(per_object_summary) > 1:
        for obj, s in per_object_summary.items():
            print(
                f"{prefix}   {obj}: {s['success']}/{s['n']} = {s['rate']:.1%} "
                f"[{s['ci'][0]:.1%}, {s['ci'][1]:.1%}]"
            )

    return {
        "episodes": episodes,
        "n_success": n_success,
        "n_diverged": n_diverged,
        "n_invalid_action": n_invalid_action,
        "success_rate": rate,
        "success_ci": [ci_lo, ci_hi],
        "per_object": per_object_summary,
        "episodes_detail": episodes_detail,
        "params": {
            "seed": seed,
            "max_seconds": max_seconds,
            "dwell_seconds": dwell_seconds,
            "pick": list(pick_choices),
            "place": place,
            "tol": tol,
            "no_task": no_task,
            "jitter": jitter,
        },
        "protocol": protocol,
    }


def checkpoint_label(policy_path: str) -> str:
    """Best-effort short label for a checkpoint (e.g. the step dir '002000')."""
    p = Path(policy_path)
    # Typical layout: .../checkpoints/<step>/pretrained_model
    if p.name == "pretrained_model" and p.parent.name:
        return p.parent.name
    return p.name


def write_results(results: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[eval] results -> {out_path}")


def _str2bool(v: str) -> bool:
    """Parse a truthy/falsy string so ``--balanced=false`` works as expected."""
    if isinstance(v, bool):
        return v
    if v.lower() in ("true", "t", "yes", "y", "1"):
        return True
    if v.lower() in ("false", "f", "no", "n", "0"):
        return False
    raise argparse.ArgumentTypeError(f"expected a boolean, got {v!r}")


def _checkpoint_evidence(policy_path: Path, repo_id: str) -> dict[str, object]:
    config_path = policy_path / "config.json"
    if not config_path.is_file():
        raise EvaluationContractError(f"checkpoint config does not exist: {config_path}")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvaluationContractError(f"cannot read checkpoint config {config_path}: {exc}") from exc
    policy_type = config.get("type") if isinstance(config, dict) else None
    if not isinstance(policy_type, str) or not policy_type:
        raise EvaluationContractError(f"checkpoint config has no policy type: {config_path}")
    try:
        evidence = audit_checkpoint(policy_path, expected_policy_type=policy_type)
    except ValueError as exc:
        raise EvaluationContractError(str(exc)) from exc
    if evidence.get("dataset_repo_id") != repo_id:
        raise EvaluationContractError(
            "checkpoint training dataset does not match --repo-id: "
            f"{evidence.get('dataset_repo_id')!r} != {repo_id!r}"
        )
    return evidence


def _condition_config(
    args: argparse.Namespace,
) -> tuple[DomainRandomizationConfig, dict[str, object]]:
    """Build the reference or one-factor runtime condition used by L13."""
    factor = args.changed_factor
    evaluation_range = args.evaluation_range
    if args.condition_label == "reference":
        if factor is not None or args.training_support is not None or evaluation_range is not None:
            raise EvaluationContractError(
                "reference conditions must not declare a changed factor or support ranges"
            )
    else:
        if factor not in {"friction_ratio", "mass_ratio"}:
            raise EvaluationContractError(
                "non-reference conditions support one factor: friction_ratio or mass_ratio"
            )
        if evaluation_range is None:
            raise EvaluationContractError(
                "a non-reference condition requires --evaluation-range LO HI"
            )
        if any(value <= 0.0 for value in evaluation_range):
            raise EvaluationContractError("evaluation range values must be positive")

    condition = build_condition_spec(
        name=args.condition_name,
        declared_label=args.condition_label,
        changed_factor=factor,
        training_support=args.training_support,
        evaluation_range=evaluation_range,
        held_constant=args.held_constant,
    )
    friction_range = tuple(evaluation_range) if factor == "friction_ratio" else (1.0, 1.0)
    mass_range = tuple(evaluation_range) if factor == "mass_ratio" else (1.0, 1.0)
    runtime_dr = DomainRandomizationConfig(
        enabled=args.condition_label != "reference",
        friction_ratio_range=friction_range,
        mass_ratio_range=mass_range,
    )
    condition["configuration"] = {
        "runtime": {
            "enabled": runtime_dr.enabled,
            "friction_ratio_range": list(runtime_dr.friction_ratio_range),
            "mass_ratio_range": list(runtime_dr.mass_ratio_range),
        },
        "position_jitter_m": args.jitter,
    }
    return runtime_dr, condition


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _environment_evidence(args: argparse.Namespace, pb: PolicyBundle) -> dict[str, object]:
    cuda_name = None
    if pb.device.type == "cuda" and torch.cuda.is_available():
        cuda_name = torch.cuda.get_device_name(pb.device)
    return {
        "code": git_identity(PROJECT_ROOT),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "genesis": _package_version("genesis-world"),
        "lerobot": _package_version("lerobot"),
        "torch": torch.__version__,
        "torch_hip": torch.version.hip,
        "requested_policy_device": args.device,
        "actual_policy_device": str(pb.device),
        "accelerator_name": cuda_name,
        "simulation_backend": "cpu" if args.cpu else "gpu",
        "render_backend": os.environ.get("PYOPENGL_PLATFORM"),
        "viewer": args.vis,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Policy-agnostic closed-loop eval.")
    parser.add_argument("--policy-path", required=True, help="Checkpoint dir (contains config.json + model.safetensors).")
    parser.add_argument("--repo-id", required=True, help="Repo id of the dataset the policy trained on.")
    parser.add_argument(
        "--dataset-root",
        default=None,
        help="Local dataset directory (default: configured datasets/<repo-name>).",
    )
    parser.add_argument("--device", default="cuda", help="cuda | cpu | mps (unavailable requests fail).")
    parser.add_argument("--use-amp", action="store_true", help="Enable autocast on CUDA inference.")
    parser.add_argument(
        "--rename-map",
        default=None,
        help="JSON dict mapping dataset image keys to the policy's expected keys. "
        "Default: auto-recovered from the checkpoint's train_config.json (e.g. SmolVLA world/wrist -> camera1/camera2).",
    )
    parser.add_argument("-c", "--cpu", action="store_true", help="Run the Genesis sim on CPU backend.")
    parser.add_argument("-v", "--vis", action="store_true", help="Show the Genesis viewer.")
    parser.add_argument("--episodes", type=int, default=10, help="Number of eval episodes.")
    parser.add_argument("--seed", type=int, default=1000, help="Base RNG seed (offset from training seeds).")
    parser.add_argument("--max-seconds", type=float, default=15.0, help="Max wall-clock per episode (sim time).")
    parser.add_argument(
        "--dwell-seconds",
        type=float,
        default=0.4,
        help="Required consecutive containment time before success (default: 0.4 s).",
    )
    parser.add_argument(
        "--pick",
        nargs="+",
        default=["011_banana"],
        help="Object(s) to evaluate on; one is sampled per episode.",
    )
    parser.add_argument("--place", default="024_bowl", help="Place target object name.")
    parser.add_argument("--tol", type=float, default=0.06, help="Success tolerance (m).")
    parser.add_argument("--no-task", action="store_true", help="Send an empty task string (ignore language conditioning).")
    parser.add_argument("--jitter", type=float, default=0.03, help="Per-episode object position jitter (m).")
    parser.add_argument(
        "--balanced",
        type=_str2bool,
        nargs="?",
        const=True,
        default=True,
        help="Assign objects with a stratified (near-equal per object) seed-shuffled schedule "
        "so per-object sample sizes/CI widths match. Use --balanced=false for the legacy "
        "i.i.d. (Multinomial) sampling that pre-`balanced` sweeps used.",
    )
    parser.add_argument(
        "--save-video",
        action="store_true",
        help="Save each episode's rollout to mp4 (1x3: world + wrist + third-person view side by side).",
    )
    parser.add_argument(
        "--video-dir",
        default=None,
        help="Rollout video directory (default: configured outputs/eval_videos/<repo>).",
    )
    parser.add_argument(
        "--results-out",
        default=None,
        help="Write a structured results JSON here "
        "(default: configured outputs/eval_results/<repo>/<condition>/<checkpoint>.json). "
        "Pass 'none' to skip.",
    )
    parser.add_argument("--condition-name", default="reference")
    parser.add_argument(
        "--condition-label",
        choices=("reference", "unseen-in-support", "shifted", "ood"),
        default="reference",
    )
    parser.add_argument(
        "--changed-factor",
        choices=("friction_ratio", "mass_ratio"),
        default=None,
        help="Single runtime factor changed by a non-reference condition.",
    )
    parser.add_argument("--training-support", type=float, nargs=2, metavar=("LO", "HI"))
    parser.add_argument("--evaluation-range", type=float, nargs=2, metavar=("LO", "HI"))
    parser.add_argument("--held-constant", action="append", default=[])
    args = parser.parse_args()

    repo_name = args.repo_id.split("/")[-1]
    policy_path = resolve_cli_path(args.policy_path)
    dataset_root = resolve_cli_path(args.dataset_root, default=DATASETS_DIR / repo_name)
    dataset_evidence = audit_dataset_contract(dataset_root, repo_id=args.repo_id)
    checkpoint_evidence = _checkpoint_evidence(policy_path, args.repo_id)
    require_requested_device(
        args.device,
        cuda_available=torch.cuda.is_available(),
        mps_available=bool(
            hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        ),
    )
    if not args.cpu and not torch.cuda.is_available():
        raise EvaluationContractError(
            "Genesis GPU execution was requested but no CUDA/ROCm device is available; "
            "pass --cpu only for an explicitly CPU-scoped run"
        )

    runtime_dr, condition = _condition_config(args)
    protocol = validate_evaluation_protocol(
        episodes=args.episodes,
        policy_fps=dataset_evidence["fps"],
        control_fps=CONTROL_FPS,
        dwell_seconds=args.dwell_seconds,
        max_seconds=args.max_seconds,
        tolerance=args.tol,
        pick_objects=args.pick,
        place_target=args.place,
        available_objects=tuple(YCB_LAYOUT),
        base_seed=args.seed,
        balanced=args.balanced,
        condition_name=args.condition_name,
        render_enabled=True,
    )

    label = checkpoint_label(str(policy_path))
    default_result = EVAL_RESULTS_DIR / repo_name / args.condition_name / f"{label}.json"
    results_out = (
        None
        if args.results_out == "none"
        else resolve_cli_path(args.results_out, default=default_result)
    )
    video_dir = resolve_cli_path(
        args.video_dir,
        default=EVAL_VIDEOS_DIR / repo_name / args.condition_name / label,
    )
    validate_output_targets(
        results_path=results_out,
        video_dir=video_dir,
        save_video=args.save_video,
    )

    rename_map = json.loads(args.rename_map) if args.rename_map else None
    if rename_map is not None and rename_map != checkpoint_evidence["rename_map"]:
        raise EvaluationContractError(
            "--rename-map does not match the mapping saved with the checkpoint"
        )

    # All protocol, path, artifact, and device checks above happen before Genesis starts.
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)
    bundle = build_scene(
        show_viewer=args.vis, n_envs=1, add_world_cam=True, add_wrist_cam=True,
        add_video_cam=args.save_video,
    )

    pb = load_policy(
        str(policy_path),
        args.repo_id,
        str(dataset_root),
        args.device,
        use_amp=args.use_amp,
        rename_map=rename_map,
    )
    if pb.device.type != args.device.split(":", maxsplit=1)[0].lower():
        raise EvaluationContractError(
            f"requested policy device {args.device!r}, but loader selected {str(pb.device)!r}"
        )

    randomizer = EnvRandomizer(
        bundle,
        RandomizationConfig(
            pos_jitter=args.jitter,
            randomize_pick=False,
            seed=args.seed,
            dr=runtime_dr,
        ),
    )

    results = evaluate_policy(
        bundle, pb,
        episodes=args.episodes,
        seed=args.seed,
        max_seconds=args.max_seconds,
        dwell_seconds=args.dwell_seconds,
        pick=args.pick,
        place=args.place,
        tol=args.tol,
        no_task=args.no_task,
        jitter=args.jitter,
        balanced=args.balanced,
        randomizer=randomizer,
        save_video=args.save_video,
        video_dir=video_dir,
        label=args.condition_name,
        protocol=protocol,
    )
    if args.save_video:
        print(f"[eval] rollout videos -> {video_dir}")

    if results_out is not None:
        protocol["observation"] = {
            "state_key": STATE_KEY,
            "image_keys": list(dataset_evidence["image_shapes"]),
            "image_shapes": dataset_evidence["image_shapes"],
            "third_person_is_policy_input": False,
            "camera_rename": checkpoint_evidence["rename_map"],
        }
        report = build_evaluation_report(
            generated_at=datetime.now().astimezone().isoformat(timespec="seconds"),
            environment=_environment_evidence(args, pb),
            dataset=dataset_evidence,
            checkpoint=checkpoint_evidence,
            protocol=protocol,
            condition=condition,
            episode_rows=results["episodes_detail"],
            outputs={
                "results": str(results_out),
                "video_dir": str(video_dir) if args.save_video else None,
                "log": None,
            },
            limitations=(
                "The Wilson interval covers finite-sample uncertainty under this protocol only.",
                "This simulation run does not establish physical-robot performance.",
                f"These {args.episodes} episodes are an integration run, not a stable performance ranking.",
            ),
        )
        write_results(report, results_out)


if __name__ == "__main__":
    main()
