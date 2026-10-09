"""Dependency-light contracts for closed-loop policy evaluation.

This module deliberately avoids Genesis, Torch, LeRobot, NumPy, and video imports.
It owns the protocol and report rules that can be checked before an expensive scene
is initialized, while :mod:`robo_genesis.eval_policy` owns the live rollout.
"""

from __future__ import annotations

import json
import math
import random
import re
import subprocess
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .stats import wilson

EVALUATION_PROTOCOL_SCHEMA_VERSION = 1
EVALUATION_REPORT_SCHEMA_VERSION = 1
EXPECTED_ACTION_DIM = 9
CONDITION_LABELS = ("reference", "unseen-in-support", "shifted", "ood")
TERMINATION_REASONS = ("success", "timeout", "diverged", "invalid_action")

_CONDITION_NAME = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")


class EvaluationContractError(ValueError):
    """Raised when an evaluation protocol, outcome, or report is not auditable."""


def _finite_float(name: str, value: object) -> float:
    if isinstance(value, bool):
        raise EvaluationContractError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise EvaluationContractError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise EvaluationContractError(f"{name} must be a finite number")
    return number


def _positive_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise EvaluationContractError(f"{name} must be a positive integer")
    return value


def _range(name: str, values: Sequence[float]) -> tuple[float, float]:
    if isinstance(values, (str, bytes)) or len(values) != 2:
        raise EvaluationContractError(f"{name} must contain exactly two values")
    low = _finite_float(f"{name}[0]", values[0])
    high = _finite_float(f"{name}[1]", values[1])
    if low > high:
        raise EvaluationContractError(f"{name} lower bound must not exceed its upper bound")
    return low, high


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvaluationContractError(f"Cannot read JSON object from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvaluationContractError(f"Expected a JSON object in {path}")
    return value


def dwell_frame_count(dwell_seconds: float, policy_fps: float) -> int:
    """Return the number of consecutive checks required for at least ``dwell_seconds``."""
    dwell = _finite_float("dwell_seconds", dwell_seconds)
    fps = _finite_float("policy_fps", policy_fps)
    if dwell <= 0.0:
        raise EvaluationContractError("dwell_seconds must be positive")
    if fps <= 0.0:
        raise EvaluationContractError("policy_fps must be positive")
    return max(1, math.ceil(dwell * fps))


@dataclass
class DwellTracker:
    """Track consecutive predicate hits without a timeout-only success exception."""

    required_frames: int
    streak: int = 0
    max_streak: int = 0
    succeeded: bool = False

    def __post_init__(self) -> None:
        _positive_int("required_frames", self.required_frames)

    def update(self, predicate: bool) -> bool:
        if not isinstance(predicate, bool):
            raise EvaluationContractError("predicate values must be booleans")
        self.streak = self.streak + 1 if predicate else 0
        self.max_streak = max(self.max_streak, self.streak)
        self.succeeded = self.succeeded or self.streak >= self.required_frames
        return self.succeeded


def evaluate_predicate_trace(
    trace: Iterable[bool], *, dwell_seconds: float, policy_fps: float
) -> dict[str, int | bool | str]:
    """Reduce a finite predicate trace to one success or timeout outcome."""
    tracker = DwellTracker(dwell_frame_count(dwell_seconds, policy_fps))
    steps = 0
    for steps, predicate in enumerate(trace, start=1):
        if tracker.update(predicate):
            return {
                "success": True,
                "termination_reason": "success",
                "steps": steps,
                "dwell_frames": tracker.required_frames,
                "max_streak": tracker.max_streak,
            }
    return {
        "success": False,
        "termination_reason": "timeout",
        "steps": steps,
        "dwell_frames": tracker.required_frames,
        "max_streak": tracker.max_streak,
    }


def balanced_object_schedule(
    pick_objects: Sequence[str], *, episodes: int, seed: int
) -> list[str]:
    """Return a deterministic, near-equal object schedule using only the stdlib."""
    count = _positive_int("episodes", episodes)
    if isinstance(pick_objects, (str, bytes)):
        raise EvaluationContractError("pick_objects must be a non-empty sequence")
    objects = [str(value).strip() for value in pick_objects]
    if not objects or any(not value for value in objects):
        raise EvaluationContractError("pick_objects must contain non-empty names")
    if len(set(objects)) != len(objects):
        raise EvaluationContractError("pick_objects must not contain duplicates")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise EvaluationContractError("seed must be an integer")

    rng = random.Random(seed)
    base, remainder = divmod(count, len(objects))
    schedule = [name for name in objects for _ in range(base)]
    if remainder:
        schedule.extend(rng.sample(objects, remainder))
    rng.shuffle(schedule)
    return schedule


def validate_action_vector(action: object, *, expected_dim: int = EXPECTED_ACTION_DIM) -> tuple[float, ...]:
    """Validate one flat, finite joint target before it reaches the controller."""
    dimension = _positive_int("expected_dim", expected_dim)
    shape = getattr(action, "shape", None)
    if shape is not None and tuple(shape) != (dimension,):
        raise EvaluationContractError(
            f"action shape must be ({dimension},), got {tuple(shape)!r}"
        )
    if isinstance(action, (str, bytes)):
        raise EvaluationContractError("action must be a numeric vector")
    try:
        values = list(action)  # type: ignore[arg-type]
    except TypeError as exc:
        raise EvaluationContractError("action must be an iterable numeric vector") from exc
    if len(values) != dimension:
        raise EvaluationContractError(
            f"action shape must be ({dimension},), got ({len(values)},)"
        )

    normalized: list[float] = []
    for index, value in enumerate(values):
        if isinstance(value, bool):
            raise EvaluationContractError(f"action[{index}] must be numeric, not boolean")
        normalized.append(_finite_float(f"action[{index}]", value))
    return tuple(normalized)


def normalize_policy_action(
    action: object, *, expected_dim: int = EXPECTED_ACTION_DIM
) -> tuple[float, ...]:
    """Remove one explicit policy batch axis, then validate one controller action."""
    dimension = _positive_int("expected_dim", expected_dim)
    shape = getattr(action, "shape", None)
    if shape is not None:
        action_shape = tuple(shape)
        if action_shape == (1, dimension):
            action = action[0]  # type: ignore[index]
        elif action_shape != (dimension,):
            raise EvaluationContractError(
                f"policy action shape must be ({dimension},) or (1, {dimension}), "
                f"got {action_shape!r}"
            )
    return validate_action_vector(action, expected_dim=dimension)


def classify_condition(
    *,
    is_reference: bool,
    training_support: Sequence[float] | None = None,
    evaluation_range: Sequence[float] | None = None,
) -> str:
    """Classify a condition relative to documented support for one named factor."""
    if not isinstance(is_reference, bool):
        raise EvaluationContractError("is_reference must be boolean")
    if is_reference:
        return "reference"
    if training_support is None or evaluation_range is None:
        return "shifted"

    train_low, train_high = _range("training_support", training_support)
    eval_low, eval_high = _range("evaluation_range", evaluation_range)
    if train_low <= eval_low and eval_high <= train_high:
        return "unseen-in-support"
    if eval_high < train_low or eval_low > train_high:
        return "ood"
    return "shifted"


def build_condition_spec(
    *,
    name: str,
    declared_label: str,
    changed_factor: str | None = None,
    training_support: Sequence[float] | None = None,
    evaluation_range: Sequence[float] | None = None,
    held_constant: Sequence[str] = (),
) -> dict[str, Any]:
    """Validate one predeclared evaluation condition and its support claim."""
    if not isinstance(name, str) or not _CONDITION_NAME.fullmatch(name):
        raise EvaluationContractError(
            "condition name must use lowercase letters, digits, hyphens, or underscores"
        )
    if declared_label not in CONDITION_LABELS:
        raise EvaluationContractError(
            f"condition label must be one of {list(CONDITION_LABELS)}"
        )
    is_reference = declared_label == "reference"
    if not is_reference and (not isinstance(changed_factor, str) or not changed_factor.strip()):
        raise EvaluationContractError("a non-reference condition must name its changed factor")

    normalized_training = (
        list(_range("training_support", training_support))
        if training_support is not None
        else None
    )
    normalized_evaluation = (
        list(_range("evaluation_range", evaluation_range))
        if evaluation_range is not None
        else None
    )
    inferred = classify_condition(
        is_reference=is_reference,
        training_support=normalized_training,
        evaluation_range=normalized_evaluation,
    )
    if declared_label != inferred:
        raise EvaluationContractError(
            f"declared condition label {declared_label!r} conflicts with audited relation {inferred!r}"
        )

    constants = [str(value).strip() for value in held_constant]
    if any(not value for value in constants):
        raise EvaluationContractError("held_constant entries must be non-empty")
    return {
        "name": name,
        "label": declared_label,
        "changed_factor": changed_factor.strip() if changed_factor else None,
        "training_support": normalized_training,
        "evaluation_range": normalized_evaluation,
        "held_constant": constants,
    }


def validate_evaluation_protocol(
    *,
    episodes: int,
    policy_fps: float,
    control_fps: float,
    dwell_seconds: float,
    max_seconds: float,
    tolerance: float,
    pick_objects: Sequence[str],
    place_target: str,
    available_objects: Sequence[str],
    base_seed: int,
    balanced: bool,
    condition_name: str,
    render_enabled: bool,
) -> dict[str, Any]:
    """Validate and normalize the complete pre-rollout protocol."""
    count = _positive_int("episodes", episodes)
    fps = _finite_float("policy_fps", policy_fps)
    control = _finite_float("control_fps", control_fps)
    timeout = _finite_float("max_seconds", max_seconds)
    tol = _finite_float("tolerance", tolerance)
    if fps <= 0.0 or control <= 0.0:
        raise EvaluationContractError("policy_fps and control_fps must be positive")
    if fps > control:
        raise EvaluationContractError("policy_fps must not exceed control_fps")
    if timeout <= 0.0:
        raise EvaluationContractError("max_seconds must be positive")
    if tol <= 0.0:
        raise EvaluationContractError("tolerance must be positive")
    if isinstance(base_seed, bool) or not isinstance(base_seed, int):
        raise EvaluationContractError("base_seed must be an integer")
    if not isinstance(balanced, bool) or not isinstance(render_enabled, bool):
        raise EvaluationContractError("balanced and render_enabled must be boolean")
    if not isinstance(condition_name, str) or not _CONDITION_NAME.fullmatch(condition_name):
        raise EvaluationContractError("condition_name is not a safe condition identifier")

    available = {str(name) for name in available_objects}
    objects = [str(name).strip() for name in pick_objects]
    if not objects or any(not name for name in objects):
        raise EvaluationContractError("pick_objects must contain at least one object")
    missing = sorted(set(objects) - available)
    if missing:
        raise EvaluationContractError(f"unsupported pick object(s): {missing}")
    if not isinstance(place_target, str) or place_target not in available:
        raise EvaluationContractError(f"unsupported place target: {place_target!r}")

    schedule = (
        balanced_object_schedule(objects, episodes=count, seed=base_seed)
        if balanced
        else []
    )
    dwell_frames = dwell_frame_count(dwell_seconds, fps)
    return {
        "schema_version": EVALUATION_PROTOCOL_SCHEMA_VERSION,
        "condition_name": condition_name,
        "task": {
            "pick_objects": objects,
            "place_target": place_target,
            "success_tolerance_m": tol,
        },
        "action": {
            "dimension": EXPECTED_ACTION_DIM,
            "semantics": "joint_position_target",
        },
        "timing": {
            "policy_fps": fps,
            "control_fps": control,
            "max_seconds": timeout,
            "hold_rule": "fractional_accumulator",
        },
        "success_rule": {
            "predicate": "robo_genesis.grasp_demo.check_success",
            "dwell_seconds": float(dwell_seconds),
            "dwell_frames": dwell_frames,
            "timeout_does_not_bypass_dwell": True,
        },
        "sampling": {
            "episodes": count,
            "base_seed": base_seed,
            "episode_seeds": [base_seed + index for index in range(count)],
            "balanced": balanced,
            "object_schedule": schedule if balanced else None,
        },
        "render_enabled": render_enabled,
    }


def audit_dataset_contract(dataset_root: str | Path, *, repo_id: str) -> dict[str, Any]:
    """Read the local LeRobot metadata needed before policy or simulator startup."""
    root = Path(dataset_root).expanduser().resolve()
    if not root.is_dir():
        raise EvaluationContractError(f"dataset directory does not exist: {root}")
    info_path = root / "meta" / "info.json"
    if not info_path.is_file():
        raise EvaluationContractError(f"dataset metadata does not exist: {info_path}")
    info = _read_json_object(info_path)
    fps = _finite_float("dataset fps", info.get("fps"))
    if fps <= 0.0:
        raise EvaluationContractError("dataset fps must be positive")
    features = info.get("features")
    if not isinstance(features, Mapping):
        raise EvaluationContractError("dataset features must be an object")

    expected_shapes = {
        "observation.state": [EXPECTED_ACTION_DIM],
        "action": [EXPECTED_ACTION_DIM],
    }
    for key, expected_shape in expected_shapes.items():
        feature = features.get(key)
        if not isinstance(feature, Mapping) or feature.get("shape") != expected_shape:
            raise EvaluationContractError(
                f"dataset feature {key!r} must have shape {expected_shape}"
            )

    image_shapes: dict[str, list[int]] = {}
    for key in ("observation.images.world", "observation.images.wrist"):
        feature = features.get(key)
        if not isinstance(feature, Mapping):
            raise EvaluationContractError(f"dataset image feature is missing: {key}")
        shape = feature.get("shape")
        if (
            not isinstance(shape, list)
            or len(shape) != 3
            or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in shape)
            or shape[2] != 3
        ):
            raise EvaluationContractError(f"dataset image feature {key!r} must be HWC RGB")
        image_shapes[key] = list(shape)

    provenance_path = root / "meta" / "robo_genesis_domain_randomization.json"
    provenance: dict[str, Any] | None = None
    if provenance_path.is_file():
        from .domain_provenance import load_domain_provenance

        provenance = load_domain_provenance(provenance_path)

    return {
        "repo_id": repo_id,
        "root": str(root),
        "metadata_path": str(info_path),
        "codebase_version": info.get("codebase_version"),
        "fps": fps,
        "robot_type": info.get("robot_type"),
        "total_episodes": info.get("total_episodes"),
        "total_frames": info.get("total_frames"),
        "state_shape": list(features["observation.state"]["shape"]),
        "action_shape": list(features["action"]["shape"]),
        "image_shapes": image_shapes,
        "task_table": str(root / "meta" / "tasks.parquet"),
        "domain_provenance_path": str(provenance_path) if provenance is not None else None,
        "domain_provenance": provenance,
    }


def require_requested_device(
    requested: str, *, cuda_available: bool, mps_available: bool = False
) -> None:
    """Reject unavailable explicit accelerator requests instead of silently falling back."""
    if not isinstance(requested, str) or not requested.strip():
        raise EvaluationContractError("device must be a non-empty string")
    device_type = requested.split(":", maxsplit=1)[0].lower()
    if device_type == "cuda" and not cuda_available:
        raise EvaluationContractError(
            "CUDA/ROCm device was requested but torch.cuda.is_available() is false"
        )
    if device_type == "mps" and not mps_available:
        raise EvaluationContractError("MPS device was requested but is unavailable")
    if device_type not in {"cpu", "cuda", "mps"}:
        raise EvaluationContractError(f"unsupported device type: {device_type!r}")


def validate_output_root(path: str | Path, *, allowed_root: str | Path) -> Path:
    """Require a lesson output directory to be a non-root child of ``allowed_root``."""
    resolved = Path(path).expanduser().resolve()
    allowed = Path(allowed_root).expanduser().resolve()
    if resolved == allowed or not resolved.is_relative_to(allowed):
        raise EvaluationContractError(
            f"output root must be a child of {allowed}, got {resolved}"
        )
    return resolved


def validate_output_targets(
    *,
    results_path: str | Path | None,
    video_dir: str | Path | None,
    log_path: str | Path | None = None,
    save_video: bool,
) -> None:
    """Reject paths that would mix a new run with existing result evidence."""
    result = Path(results_path).resolve() if results_path is not None else None
    log = Path(log_path).resolve() if log_path is not None else None
    if result is not None and log is not None and result == log:
        raise EvaluationContractError("results and log outputs must use different paths")
    if result is not None and result.exists():
        raise EvaluationContractError(f"results output already exists: {result}")
    if log is not None and log.exists():
        raise EvaluationContractError(f"log output already exists: {log}")
    if save_video:
        if video_dir is None:
            raise EvaluationContractError("video_dir is required when save_video is enabled")
        path = Path(video_dir)
        if path.exists() and (not path.is_dir() or any(path.iterdir())):
            raise EvaluationContractError(f"video output is not an empty directory: {path}")


def summarize_episode_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate episode rows and recompute counts and Wilson uncertainty."""
    if not rows:
        raise EvaluationContractError("an evaluation report must contain episode rows")
    seeds: list[int] = []
    reason_counts: Counter[str] = Counter()
    object_hits: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        seed = row.get("seed")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise EvaluationContractError(f"episodes[{index}].seed must be an integer")
        seeds.append(seed)
        reason = row.get("termination_reason")
        if reason not in TERMINATION_REASONS:
            raise EvaluationContractError(
                f"episodes[{index}].termination_reason must be one of {list(TERMINATION_REASONS)}"
            )
        success = row.get("success")
        if not isinstance(success, bool) or success != (reason == "success"):
            raise EvaluationContractError(
                f"episodes[{index}].success conflicts with termination_reason"
            )
        pick = row.get("pick")
        if not isinstance(pick, str) or not pick:
            raise EvaluationContractError(f"episodes[{index}].pick must be a non-empty string")
        reason_counts[reason] += 1
        object_hits.setdefault(pick, []).append(int(success))
    if len(seeds) != len(set(seeds)):
        raise EvaluationContractError("episode seeds must be unique within one condition")

    episodes = len(rows)
    successes = reason_counts["success"]
    ci_low, ci_high = wilson(successes, episodes)
    per_object: dict[str, dict[str, Any]] = {}
    for name, hits in sorted(object_hits.items()):
        object_successes = sum(hits)
        object_low, object_high = wilson(object_successes, len(hits))
        per_object[name] = {
            "episodes": len(hits),
            "successes": object_successes,
            "success_rate": object_successes / len(hits),
            "wilson_95": [object_low, object_high],
        }
    return {
        "episodes": episodes,
        "successes": successes,
        "failures": episodes - successes,
        "success_rate": successes / episodes,
        "wilson_95": [ci_low, ci_high],
        "termination_counts": {
            reason: reason_counts[reason] for reason in TERMINATION_REASONS
        },
        "per_object": per_object,
    }


def build_evaluation_report(
    *,
    generated_at: str,
    environment: Mapping[str, Any],
    dataset: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    protocol: Mapping[str, Any],
    condition: Mapping[str, Any],
    episode_rows: Sequence[Mapping[str, Any]],
    outputs: Mapping[str, Any],
    limitations: Sequence[str],
) -> dict[str, Any]:
    """Build and validate one versioned, single-condition evaluation report."""
    rows = [dict(row) for row in episode_rows]
    report = {
        "schema_name": "robo-genesis-evaluation-report",
        "schema_version": EVALUATION_REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "environment": dict(environment),
        "artifacts": {"dataset": dict(dataset), "checkpoint": dict(checkpoint)},
        "protocol": dict(protocol),
        "condition": dict(condition),
        "summary": summarize_episode_rows(rows),
        "episodes": rows,
        "outputs": dict(outputs),
        "limitations": list(limitations),
    }
    validate_evaluation_report(report)
    return report


def validate_evaluation_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Validate counts, seeds, condition identity, and schema of an evaluation report."""
    required = {
        "schema_name",
        "schema_version",
        "generated_at",
        "environment",
        "artifacts",
        "protocol",
        "condition",
        "summary",
        "episodes",
        "outputs",
        "limitations",
    }
    missing = sorted(required - set(report))
    if missing:
        raise EvaluationContractError(f"evaluation report is missing fields: {missing}")
    if report.get("schema_name") != "robo-genesis-evaluation-report":
        raise EvaluationContractError("unsupported evaluation report schema_name")
    if report.get("schema_version") != EVALUATION_REPORT_SCHEMA_VERSION:
        raise EvaluationContractError("unsupported evaluation report schema_version")
    episodes = report.get("episodes")
    if not isinstance(episodes, list):
        raise EvaluationContractError("evaluation report episodes must be a list")
    recomputed = summarize_episode_rows(episodes)
    if report.get("summary") != recomputed:
        raise EvaluationContractError("evaluation report summary does not match episode rows")
    protocol = report.get("protocol")
    condition = report.get("condition")
    if not isinstance(protocol, Mapping) or not isinstance(condition, Mapping):
        raise EvaluationContractError("evaluation report protocol and condition must be objects")
    sampling = protocol.get("sampling")
    if not isinstance(sampling, Mapping) or sampling.get("episodes") != len(episodes):
        raise EvaluationContractError("protocol episode count does not match episode rows")
    if protocol.get("condition_name") != condition.get("name"):
        raise EvaluationContractError("protocol condition_name does not match condition.name")
    expected_seeds = sampling.get("episode_seeds")
    actual_seeds = [row.get("seed") for row in episodes]
    if expected_seeds != actual_seeds:
        raise EvaluationContractError("episode seeds do not match the frozen protocol")
    return dict(report)


def paired_outcome_changes(
    reference_rows: Sequence[Mapping[str, Any]],
    held_out_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Place matched binary outcomes side by side without claiming significance."""
    def by_seed(rows: Sequence[Mapping[str, Any]], label: str) -> dict[int, bool]:
        result: dict[int, bool] = {}
        for index, row in enumerate(rows):
            seed = row.get("seed")
            success = row.get("success")
            if isinstance(seed, bool) or not isinstance(seed, int) or not isinstance(success, bool):
                raise EvaluationContractError(f"invalid {label} row at index {index}")
            if seed in result:
                raise EvaluationContractError(f"duplicate {label} seed: {seed}")
            result[seed] = success
        return result

    reference = by_seed(reference_rows, "reference")
    held_out = by_seed(held_out_rows, "held-out")
    if set(reference) != set(held_out):
        raise EvaluationContractError("reference and held-out reports must use identical seeds")
    changes: list[dict[str, Any]] = []
    for seed in sorted(reference):
        before, after = reference[seed], held_out[seed]
        changes.append(
            {
                "seed": seed,
                "reference": "success" if before else "failure",
                "held_out": "success" if after else "failure",
                "change": (
                    "unchanged-success"
                    if before and after
                    else "success-to-failure"
                    if before
                    else "failure-to-success"
                    if after
                    else "unchanged-failure"
                ),
            }
        )
    return changes


def git_identity(project_root: str | Path) -> dict[str, Any]:
    """Return the current commit and dirty flag without requiring GitPython."""
    root = Path(project_root).resolve()
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--short"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (OSError, subprocess.CalledProcessError):
        return {"revision": None, "dirty": None}
    return {"revision": revision, "dirty": dirty}


__all__ = [
    "CONDITION_LABELS",
    "DwellTracker",
    "EVALUATION_PROTOCOL_SCHEMA_VERSION",
    "EVALUATION_REPORT_SCHEMA_VERSION",
    "EXPECTED_ACTION_DIM",
    "EvaluationContractError",
    "TERMINATION_REASONS",
    "audit_dataset_contract",
    "balanced_object_schedule",
    "build_condition_spec",
    "build_evaluation_report",
    "classify_condition",
    "dwell_frame_count",
    "evaluate_predicate_trace",
    "git_identity",
    "paired_outcome_changes",
    "require_requested_device",
    "summarize_episode_rows",
    "validate_action_vector",
    "normalize_policy_action",
    "validate_evaluation_protocol",
    "validate_evaluation_report",
    "validate_output_root",
    "validate_output_targets",
]
