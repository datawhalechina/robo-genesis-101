"""Linear orchestration helpers for the L13 closed-loop evaluation lab.

The lecture owns the evaluation reasoning.  This module keeps notebook-only
infrastructure—path resolution, dataset-metadata and checkpoint acquisition,
subprocess logging, video validation, and report writing—out of the
learner-facing cells.  It does not initialize Genesis in the notebook kernel;
live evaluation remains in ``robo_genesis.eval_policy``.
"""

from __future__ import annotations

import importlib.metadata as package_metadata
import json
import os
import platform
import re
import shlex
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .evaluation_contract import (
    EvaluationContractError,
    audit_dataset_contract,
    build_condition_spec,
    classify_condition,
    paired_outcome_changes,
    summarize_episode_rows,
    validate_evaluation_report,
    validate_output_root,
    validate_output_targets,
)
from .paths import OUTPUTS_DIR, PROJECT_ROOT
from .training_contract import audit_checkpoint

CheckpointSource = str | Path | Mapping[str, object] | None
DatasetFallbackSource = Mapping[str, object] | None


@dataclass(frozen=True)
class L13Workflow:
    """Resolved artifacts, device request, and output root for one lab run."""

    project_root: Path
    outputs_dir: Path
    dataset_root: Path
    repo_id: str
    output_root: Path
    checkpoint_source: CheckpointSource
    checkpoint_origin: str
    policy_device: str
    gpu_index: int | None
    render_enabled: bool
    dataset_fallback_source: DatasetFallbackSource = None


@dataclass(frozen=True)
class L13InputAudit:
    """Preflight evidence collected without initializing Genesis."""

    rows: tuple[dict[str, str], ...]
    dataset: dict[str, Any] | None
    checkpoint: dict[str, Any] | None
    checkpoint_root: Path | None
    dataset_root: Path | None = None

    @property
    def ready(self) -> bool:
        return (
            self.dataset is not None
            and self.dataset_root is not None
            and self.checkpoint is not None
            and self.checkpoint_root is not None
        )

    @property
    def ready_for_reference(self) -> bool:
        """Whether Step 4 can resolve the checkpoint and start evaluation."""
        deferred = {
            row["input"]
            for row in self.rows
            if row["status"] == "DEFERRED"
        }
        dataset_available = (
            self.dataset is not None and self.dataset_root is not None
        ) or "dataset" in deferred
        checkpoint_available = (
            self.checkpoint is not None and self.checkpoint_root is not None
        ) or "checkpoint" in deferred
        return dataset_available and checkpoint_available


@dataclass(frozen=True)
class L13ConditionRun:
    """One completed evaluator subprocess and its validated report."""

    root: Path
    paths: dict[str, Path]
    command: tuple[str, ...]
    report: dict[str, Any]


def _configured_path(
    value: str | Path | None,
    *,
    default: str | Path | None = None,
    project_root: Path = PROJECT_ROOT,
) -> Path | None:
    raw = value if value not in (None, "") else default
    if raw is None:
        return None
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else project_root / path).resolve()


def _installed_version(distribution: str) -> str | None:
    try:
        return package_metadata.version(distribution)
    except package_metadata.PackageNotFoundError:
        return None


def resolve_checkpoint_source(
    source: CheckpointSource,
    *,
    allow_download: bool,
) -> tuple[Path | None, dict[str, Any]]:
    """Resolve a local path or one commit-pinned Hugging Face subfolder."""
    if source is None:
        return None, {"kind": "unavailable"}
    if isinstance(source, (str, Path)):
        path = _configured_path(source)
        assert path is not None
        return path, {"kind": "local", "path": str(path)}
    if not isinstance(source, Mapping):
        raise TypeError(
            "checkpoint must be a local path, a pinned Hugging Face mapping, or None"
        )

    required = {"repo_id", "revision", "subfolder"}
    if set(source) != required:
        raise ValueError(
            f"Hugging Face checkpoint source must contain exactly {sorted(required)}"
        )
    repo_id = str(source["repo_id"]).strip()
    revision = str(source["revision"]).strip().lower()
    subfolder = str(source["subfolder"]).strip().strip("/")
    if not repo_id or not re.fullmatch(r"[0-9a-f]{40}", revision) or not subfolder:
        raise ValueError(
            "Hugging Face checkpoint requires repo_id, a 40-hex commit, and subfolder"
        )
    evidence: dict[str, Any] = {
        "kind": "huggingface",
        "repo_id": repo_id,
        "revision": revision,
        "subfolder": subfolder,
        "downloaded": False,
    }
    if not allow_download:
        return None, evidence

    from huggingface_hub import snapshot_download

    snapshot = Path(snapshot_download(repo_id=repo_id, revision=revision)).resolve()
    checkpoint = (snapshot / subfolder).resolve()
    if not checkpoint.is_relative_to(snapshot) or not checkpoint.is_dir():
        raise EvaluationContractError(
            f"Hugging Face checkpoint subfolder does not exist: {checkpoint}"
        )
    evidence.update(
        {"downloaded": True, "snapshot": str(snapshot), "path": str(checkpoint)}
    )
    return checkpoint, evidence


def resolve_dataset_fallback(
    source: DatasetFallbackSource,
    *,
    allow_download: bool,
) -> tuple[Path | None, dict[str, Any]]:
    """Resolve commit-pinned LeRobot metadata from a Hugging Face dataset repo."""
    if source is None:
        return None, {"kind": "unavailable"}
    if not isinstance(source, Mapping):
        raise TypeError("dataset fallback must be a pinned Hugging Face mapping")

    required = {"repo_id", "revision", "subfolder"}
    if set(source) != required:
        raise ValueError(
            f"Hugging Face dataset source must contain exactly {sorted(required)}"
        )
    repo_id = str(source["repo_id"]).strip()
    revision = str(source["revision"]).strip().lower()
    subfolder = str(source["subfolder"]).strip().strip("/")
    if not repo_id or not re.fullmatch(r"[0-9a-f]{40}", revision) or not subfolder:
        raise ValueError(
            "Hugging Face dataset requires repo_id, a 40-hex commit, and subfolder"
        )
    metadata_pattern = "meta/**" if subfolder == "." else f"{subfolder}/meta/**"
    evidence: dict[str, Any] = {
        "kind": "huggingface-dataset",
        "repo_id": repo_id,
        "revision": revision,
        "subfolder": subfolder,
        "allow_patterns": [metadata_pattern],
        "downloaded": False,
    }
    if not allow_download:
        return None, evidence

    from huggingface_hub import snapshot_download

    try:
        snapshot = Path(
            snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                revision=revision,
                allow_patterns=[metadata_pattern],
            )
        ).resolve()
    except Exception as exc:
        raise EvaluationContractError(
            f"could not download dataset metadata from {repo_id}@{revision}: {exc}"
        ) from exc
    dataset_root = (snapshot / subfolder).resolve()
    if not dataset_root.is_relative_to(snapshot) or not dataset_root.is_dir():
        raise EvaluationContractError(
            f"Hugging Face dataset subfolder does not exist: {dataset_root}"
        )
    evidence.update(
        {"downloaded": True, "snapshot": str(snapshot), "path": str(dataset_root)}
    )
    return dataset_root, evidence


def prepare_l13_workflow(
    config: Mapping[str, Any],
    *,
    course_default_checkpoint: CheckpointSource = None,
    course_default_dataset: DatasetFallbackSource = None,
) -> L13Workflow:
    """Resolve exactly the values displayed in the learner configuration cell."""
    run_name = str(config["run_name"]).strip()
    if not run_name or Path(run_name).name != run_name:
        raise ValueError("run_name must be one non-empty directory name")

    repo_id = str(config["dataset_repo_id"]).strip()
    if not repo_id:
        raise ValueError("dataset_repo_id must be non-empty")
    dataset_root = _configured_path(config["dataset_root"])
    assert dataset_root is not None

    checkpoint_source: CheckpointSource = config.get("checkpoint")
    if checkpoint_source is not None:
        checkpoint_origin = "explicit"
    elif course_default_checkpoint is not None:
        checkpoint_origin = "course-default"
        checkpoint_source = course_default_checkpoint
    else:
        checkpoint_origin = "unavailable"

    output_root = _configured_path(
        OUTPUTS_DIR / "l13" / run_name,
    )
    assert output_root is not None
    output_root = validate_output_root(output_root, allowed_root=OUTPUTS_DIR)

    policy_device = str(config["policy_device"]).strip()
    if not policy_device:
        raise ValueError("policy_device must be non-empty")

    gpu_value: object = config.get("gpu_index")
    gpu_index = None if gpu_value in (None, "", "-1", -1) else int(gpu_value)
    if gpu_index is not None and gpu_index < 0:
        raise ValueError("gpu_index must be non-negative or None")

    return L13Workflow(
        project_root=PROJECT_ROOT,
        outputs_dir=OUTPUTS_DIR,
        dataset_root=dataset_root,
        repo_id=repo_id,
        output_root=output_root,
        checkpoint_source=checkpoint_source,
        checkpoint_origin=checkpoint_origin,
        policy_device=policy_device,
        gpu_index=gpu_index,
        render_enabled=bool(config["render"]),
        dataset_fallback_source=course_default_dataset,
    )


def evaluator_environment_overrides(
    workflow: L13Workflow,
) -> dict[str, str | None]:
    """Show the child-process environment derived from visible notebook choices."""
    overrides: dict[str, str | None] = {
        "PYOPENGL_PLATFORM": "egl",
        "ROBO_GENESIS_RENDER": "1" if workflow.render_enabled else "0",
        "TOKENIZERS_PARALLELISM": "false",
    }
    if workflow.gpu_index is not None and workflow.policy_device.startswith("cuda"):
        overrides.update(
            {
                "ROCR_VISIBLE_DEVICES": str(workflow.gpu_index),
                "HIP_VISIBLE_DEVICES": None,
                "CUDA_VISIBLE_DEVICES": None,
            }
        )
    return overrides


def runtime_summary(workflow: L13Workflow, *, lesson_status: str) -> dict[str, Any]:
    """Return the environment identity shown at the first evidence gate."""
    try:
        import torch

        names = [
            torch.cuda.get_device_name(index)
            for index in range(torch.cuda.device_count())
        ]
        torch_evidence: dict[str, Any] = {
            "version": torch.__version__,
            "hip": getattr(torch.version, "hip", None),
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
            "device_names": names,
        }
    except Exception as exc:  # pragma: no cover - installation-specific diagnostic
        torch_evidence = {"import_error": str(exc)}

    return {
        "lesson": "L13",
        "status": lesson_status,
        "python": platform.python_version(),
        "genesis": _installed_version("genesis-world"),
        "lerobot": _installed_version("lerobot"),
        "torch": torch_evidence,
        "requested_policy_device": workflow.policy_device,
        "evaluator_gpu_index": workflow.gpu_index,
        "render_enabled": workflow.render_enabled,
        "configured_dataset_root": str(workflow.dataset_root),
        "dataset_repo_id": workflow.repo_id,
        "dataset_fallback_source": workflow.dataset_fallback_source,
        "checkpoint_origin": workflow.checkpoint_origin,
        "checkpoint_source": workflow.checkpoint_source,
        "evaluator_environment_overrides": evaluator_environment_overrides(workflow),
        "output_root": str(workflow.output_root),
    }


def audit_l13_inputs(
    workflow: L13Workflow,
    *,
    allow_dataset_download: bool,
    allow_checkpoint_download: bool,
) -> L13InputAudit:
    """Audit dataset and checkpoint identities without starting the simulator."""
    rows: list[dict[str, str]] = []
    dataset_evidence: dict[str, Any] | None = None
    checkpoint_evidence: dict[str, Any] | None = None
    checkpoint_root: Path | None = None
    dataset_root: Path | None = None

    try:
        if workflow.dataset_root.is_dir():
            dataset_root = workflow.dataset_root
            dataset_source: dict[str, Any] = {
                "kind": "local",
                "path": str(dataset_root),
            }
        elif workflow.dataset_fallback_source is not None:
            dataset_root, dataset_source = resolve_dataset_fallback(
                workflow.dataset_fallback_source,
                allow_download=allow_dataset_download,
            )
        else:
            dataset_root = workflow.dataset_root
            dataset_source = {
                "kind": "local",
                "path": str(dataset_root),
            }

        if dataset_root is None:
            rows.append(
                {
                    "input": "dataset",
                    "status": "DEFERRED",
                    "detail": (
                        "Local dataset is absent; pinned Hugging Face metadata is "
                        "declared but has not been downloaded."
                    ),
                }
            )
        else:
            dataset_evidence = audit_dataset_contract(
                dataset_root, repo_id=workflow.repo_id
            )
            dataset_evidence["source"] = dataset_source
            rows.append(
                {
                    "input": "dataset",
                    "status": "PASS",
                    "detail": str(dataset_root),
                }
            )
    except (EvaluationContractError, OSError, ValueError, TypeError) as exc:
        dataset_root = None
        dataset_evidence = None
        rows.append({"input": "dataset", "status": "FAIL", "detail": str(exc)})

    try:
        checkpoint_root, source_evidence = resolve_checkpoint_source(
            workflow.checkpoint_source, allow_download=allow_checkpoint_download
        )
        if checkpoint_root is None:
            if source_evidence["kind"] == "huggingface":
                detail = (
                    "Pinned Hugging Face checkpoint is declared; download is deferred "
                    "until you run the Reference cell (Step 4)."
                )
            else:
                detail = "No explicit or default checkpoint source is configured."
            status = "DEFERRED" if source_evidence["kind"] == "huggingface" else "SKIP"
            rows.append({"input": "checkpoint", "status": status, "detail": detail})
        else:
            config_path = checkpoint_root / "config.json"
            if not config_path.is_file():
                raise EvaluationContractError(
                    f"checkpoint config does not exist: {config_path}"
                )
            config = json.loads(config_path.read_text(encoding="utf-8"))
            policy_type = config.get("type")
            if not isinstance(policy_type, str) or not policy_type:
                raise EvaluationContractError("checkpoint config must name a policy type")
            checkpoint_evidence = audit_checkpoint(
                checkpoint_root, expected_policy_type=policy_type
            )
            checkpoint_evidence["source"] = source_evidence
            if checkpoint_evidence["dataset_repo_id"] != workflow.repo_id:
                raise EvaluationContractError(
                    "checkpoint training dataset does not match dataset_repo_id: "
                    f"{checkpoint_evidence['dataset_repo_id']!r} != {workflow.repo_id!r}"
                )
            rows.append(
                {
                    "input": "checkpoint",
                    "status": "PASS",
                    "detail": str(checkpoint_root),
                }
            )
    except (
        EvaluationContractError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ) as exc:
        checkpoint_root = None
        checkpoint_evidence = None
        rows.append({"input": "checkpoint", "status": "FAIL", "detail": str(exc)})

    return L13InputAudit(
        rows=tuple(rows),
        dataset=dataset_evidence,
        checkpoint=checkpoint_evidence,
        checkpoint_root=checkpoint_root,
        dataset_root=dataset_root,
    )


def require_l13_inputs(workflow: L13Workflow) -> L13InputAudit:
    """Resolve downloads if needed, then reject an incomplete live-run preflight."""
    preflight = audit_l13_inputs(
        workflow,
        allow_dataset_download=True,
        allow_checkpoint_download=False,
    )
    if preflight.ready:
        return preflight
    if not preflight.ready_for_reference:
        details = "; ".join(
            f"{row['input']}={row['status']}: {row['detail']}"
            for row in preflight.rows
            if row["status"] in {"FAIL", "SKIP"}
        )
        raise EvaluationContractError(
            "Step 4 cannot start. Return to the configuration cell and fix the "
            f"unready input before retrying: {details}"
        )

    audit = audit_l13_inputs(
        workflow,
        allow_dataset_download=True,
        allow_checkpoint_download=True,
    )
    if audit.ready:
        return audit
    details = "; ".join(
        f"{row['input']}={row['status']}: {row['detail']}" for row in audit.rows
    )
    raise EvaluationContractError(f"live evaluation inputs are not ready: {details}")


def _optional_range(value: object, *, name: str) -> list[float] | None:
    if value in (None, ""):
        return None
    items = value.split(",") if isinstance(value, str) else value
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise ValueError(f"{name} must contain LO,HI")
    values = [float(item) for item in items]
    if len(values) != 2:
        raise ValueError(f"{name} must contain exactly LO,HI")
    return values


def declare_l13_conditions(
    held_out_config: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Declare Reference plus at most one provenance-labelled changed factor."""
    held_constant = ("task", "camera contract", "object schedule", "episode seeds")
    reference = build_condition_spec(
        name="reference",
        declared_label="reference",
        held_constant=held_constant,
    )

    factor = str(held_out_config.get("factor") or "").strip()
    if not factor:
        return reference, None
    if factor not in {"friction_ratio", "mass_ratio"}:
        raise ValueError("L13 isolates friction_ratio or mass_ratio only")

    training_support = _optional_range(
        held_out_config.get("training_support"),
        name="training_support",
    )
    evaluation_range = _optional_range(
        held_out_config.get("evaluation_range"),
        name="evaluation_range",
    )
    if evaluation_range is None:
        raise ValueError("a held-out condition requires one evaluation range")
    name = str(held_out_config["name"]).strip()
    label = classify_condition(
        is_reference=False,
        training_support=training_support,
        evaluation_range=evaluation_range,
    )
    held_out = build_condition_spec(
        name=name,
        declared_label=label,
        changed_factor=factor,
        training_support=training_support,
        evaluation_range=evaluation_range,
        held_constant=held_constant,
    )
    return reference, held_out


def build_l13_evaluation_command(
    workflow: L13Workflow,
    inputs: L13InputAudit,
    protocol: Mapping[str, Any],
    condition: Mapping[str, Any],
    run_root: Path,
) -> tuple[str, ...]:
    """Translate one frozen protocol into the evaluator CLI contract."""
    if not inputs.ready or inputs.checkpoint_root is None or inputs.dataset_root is None:
        raise EvaluationContractError("cannot build an evaluator command before preflight passes")
    task = protocol["task"]
    timing = protocol["timing"]
    sampling = protocol["sampling"]
    success_rule = protocol["success_rule"]
    command = [
        sys.executable,
        "-m",
        "robo_genesis.eval_policy",
        "--policy-path",
        str(inputs.checkpoint_root),
        "--repo-id",
        workflow.repo_id,
        "--dataset-root",
        str(inputs.dataset_root),
        "--device",
        workflow.policy_device,
        "--episodes",
        str(sampling["episodes"]),
        "--seed",
        str(sampling["base_seed"]),
        "--balanced=true",
        "--max-seconds",
        str(timing["max_seconds"]),
        "--dwell-seconds",
        str(success_rule["dwell_seconds"]),
        "--pick",
        *[str(value) for value in task["pick_objects"]],
        "--place",
        str(task["place_target"]),
        "--tol",
        str(task["success_tolerance_m"]),
        "--save-video",
        "--condition-name",
        str(condition["name"]),
        "--condition-label",
        str(condition["label"]),
        "--video-dir",
        str(run_root / "videos"),
        "--results-out",
        str(run_root / "results.json"),
    ]
    for item in condition["held_constant"]:
        command.extend(["--held-constant", str(item)])
    if condition["changed_factor"] is not None:
        command.extend(["--changed-factor", str(condition["changed_factor"])])
        command.extend(
            [
                "--evaluation-range",
                *[str(value) for value in condition["evaluation_range"]],
            ]
        )
        if condition["training_support"] is not None:
            command.extend(
                [
                    "--training-support",
                    *[str(value) for value in condition["training_support"]],
                ]
            )
    return tuple(command)


def _evaluator_environment(workflow: L13Workflow) -> dict[str, str]:
    environment = os.environ.copy()
    for name, value in evaluator_environment_overrides(workflow).items():
        if value is None:
            environment.pop(name, None)
        else:
            environment[name] = value
    return environment


def run_l13_condition(
    workflow: L13Workflow,
    inputs: L13InputAudit,
    protocol: Mapping[str, Any],
    condition: Mapping[str, Any],
) -> L13ConditionRun:
    """Run one condition, capture its log, and validate its structured report."""
    if not workflow.render_enabled:
        raise EvaluationContractError("live L13 evaluation requires rendering")
    run_root = workflow.output_root / str(condition["name"])
    paths = {
        "results": run_root / "results.json",
        "videos": run_root / "videos",
        "log": run_root / "run.log",
    }
    validate_output_targets(
        results_path=paths["results"],
        video_dir=paths["videos"],
        log_path=paths["log"],
        save_video=True,
    )
    command = build_l13_evaluation_command(
        workflow, inputs, protocol, condition, run_root
    )
    print("$ " + shlex.join(command))
    process = subprocess.run(
        command,
        cwd=workflow.project_root,
        env=_evaluator_environment(workflow),
        capture_output=True,
        text=True,
        check=False,
    )
    paths["log"].parent.mkdir(parents=True, exist_ok=True)
    paths["log"].write_text(process.stdout + process.stderr, encoding="utf-8")
    if process.returncode != 0:
        raise RuntimeError(
            f"evaluator exited with code {process.returncode}; inspect {paths['log']}"
        )
    data = json.loads(paths["results"].read_text(encoding="utf-8"))
    data["outputs"]["log"] = str(paths["log"])
    report = validate_evaluation_report(data)
    paths["results"].write_text(json.dumps(report, indent=2), encoding="utf-8")
    return L13ConditionRun(
        root=run_root,
        paths=paths,
        command=command,
        report=report,
    )


def audit_l13_evidence(
    report: Mapping[str, Any],
    *,
    manual_failure_labels: Mapping[int, Mapping[str, str]] | None = None,
) -> dict[str, Any]:
    """Recompute counts and verify one H.264 rollout video per episode."""
    validated = validate_evaluation_report(report)
    summary = summarize_episode_rows(validated["episodes"])
    if summary != validated["summary"]:
        raise EvaluationContractError("stored summary differs from episode rows")

    import cv2

    videos: list[dict[str, Any]] = []
    for episode in validated["episodes"]:
        video_value = episode.get("video")
        if not video_value:
            raise EvaluationContractError(
                f"episode seed {episode['seed']} has no video path"
            )
        video_path = Path(video_value)
        if not video_path.is_file() or video_path.stat().st_size <= 0:
            raise EvaluationContractError(f"missing or empty rollout video: {video_path}")
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise EvaluationContractError(f"cannot decode rollout video: {video_path}")
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fourcc = int(capture.get(cv2.CAP_PROP_FOURCC))
        codec = "".join(
            chr((fourcc >> (8 * index)) & 0xFF) for index in range(4)
        ).strip("\x00").lower()
        capture.release()
        if width <= 0 or height <= 0 or width % 2 or height % 2 or frames <= 0:
            raise EvaluationContractError(
                f"invalid video geometry or frame count: {video_path}"
            )
        if codec not in {"avc1", "h264", "x264"}:
            raise EvaluationContractError(
                f"expected H.264 video, got codec {codec!r}: {video_path}"
            )
        videos.append(
            {
                "seed": episode["seed"],
                "path": str(video_path),
                "codec": codec,
                "width": width,
                "height": height,
                "frames": frames,
            }
        )
    if len(videos) != summary["episodes"]:
        raise EvaluationContractError("video count does not match episode denominator")

    labels = dict(manual_failure_labels or {})
    failed_seeds = {
        row["seed"] for row in validated["episodes"] if not row["success"]
    }
    for seed, annotation in labels.items():
        if seed not in failed_seeds:
            raise EvaluationContractError(
                f"manual label seed {seed} is not a failed episode"
            )
        if set(annotation) != {"category", "visible_evidence"} or not all(
            annotation.values()
        ):
            raise EvaluationContractError(
                f"manual label for seed {seed} must contain visible evidence"
            )

    representative = next(
        (row for row in validated["episodes"] if not row["success"]),
        validated["episodes"][0],
    )
    return {
        "summary": summary,
        "videos": videos,
        "representative_episode": representative,
        "selection_rule": (
            "first failure" if not representative["success"] else "first episode"
        ),
        "manual_failure_labels": labels,
    }


def compare_l13_runs(
    reference: L13ConditionRun,
    held_out: L13ConditionRun,
) -> list[dict[str, Any]]:
    """Return matched outcome flips without adding a significance claim."""
    return paired_outcome_changes(
        reference.report["episodes"], held_out.report["episodes"]
    )


def build_l13_capstone_guidance(
    reference_summary: Mapping[str, Any],
    held_out_summary: Mapping[str, Any],
    held_out_condition: Mapping[str, Any],
    paired_changes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build an evidence card and scenario-aware sentence stems for Step 7."""
    held_out_name = str(held_out_condition["name"])
    change_counts: dict[str, int] = {}
    for row in paired_changes:
        change = str(row["change"])
        change_counts[change] = change_counts.get(change, 0) + 1

    reference_successes = int(reference_summary["successes"])
    reference_episodes = int(reference_summary["episodes"])
    held_out_successes = int(held_out_summary["successes"])
    held_out_episodes = int(held_out_summary["episodes"])
    evidence_question = (
        f"What do the Reference and {held_out_name} rollouts support for this checkpoint?"
    )
    evidence_card = {
        "question": evidence_question,
        "scope": {
            "matched_seeds": len(paired_changes),
            "simulation_only": True,
            "single_checkpoint": True,
        },
        "reference": {
            "successes": reference_successes,
            "episodes": reference_episodes,
            "wilson_95": reference_summary["wilson_95"],
        },
        "held_out": {
            "name": held_out_name,
            "label": held_out_condition["label"],
            "changed_factor": held_out_condition["changed_factor"],
            "evaluation_range": held_out_condition["evaluation_range"],
            "successes": held_out_successes,
            "episodes": held_out_episodes,
            "wilson_95": held_out_summary["wilson_95"],
        },
        "matched_outcome_changes": change_counts,
    }
    supported_stem = (
        f"Under this frozen {len(paired_changes)}-seed simulation protocol, "
        f"Reference achieved {reference_successes}/{reference_episodes}; "
        f"{held_out_name} achieved {held_out_successes}/{held_out_episodes}; "
        f"matched outcome changes were {change_counts}."
    )
    if reference_successes == 0:
        unsupported_stem = (
            "Because Reference did not establish task completion, this run cannot "
            "isolate sensitivity to the held-out factor or support a robustness claim."
        )
        next_evidence_stem = (
            "Inspect the representative Reference failures and first establish a "
            "checkpoint and protocol that can complete the Reference task."
        )
    elif (
        reference_successes == reference_episodes
        and held_out_successes == held_out_episodes
    ):
        unsupported_stem = (
            "Equal observed counts in this small matched sample do not establish "
            "condition equivalence, general robustness, or sim-to-real transfer."
        )
        next_evidence_stem = (
            "Repeat the same matched comparison with at least 50 predeclared seeds "
            "to look for less frequent failures."
        )
    else:
        unsupported_stem = (
            "This small matched sample does not establish statistical significance, "
            "general robustness to other shifts, or sim-to-real transfer."
        )
        next_evidence_stem = (
            "Repeat this exact Reference/held-out comparison with at least 50 "
            "predeclared matched seeds."
        )
    return {
        "question": evidence_question,
        "evidence_card": evidence_card,
        "sentence_stems": {
            "supported_claim_stem": supported_stem,
            "unsupported_claim_stem": unsupported_stem,
            "next_evidence_stem": next_evidence_stem,
        },
    }


def capstone_statements(
    config: Mapping[str, Any],
) -> dict[str, str]:
    """Return exactly the four learner-authored report fields."""
    return {
        "question": str(config["question"]),
        "supported": str(config["supported_claim"]),
        "not_supported": str(config["unsupported_claim"]),
        "next_evidence": str(config["next_evidence"]),
    }


def write_l13_capstone_report(
    workflow: L13Workflow,
    reference: L13ConditionRun,
    held_out: L13ConditionRun,
    paired_changes: Sequence[Mapping[str, Any]],
    statements: Mapping[str, str],
) -> dict[str, Any]:
    """Write the final evidence-chain report after both conditions are audited."""
    required = ("question", "supported", "not_supported", "next_evidence")
    missing = [name for name in required if not str(statements.get(name, "")).strip()]
    if missing:
        raise EvaluationContractError(
            "complete the Capstone conclusion fields before writing the report: "
            + ", ".join(missing)
        )

    root = workflow.output_root / "capstone"
    paths = {"json": root / "report.json", "markdown": root / "report.md"}
    validate_output_targets(
        results_path=paths["json"],
        video_dir=None,
        log_path=paths["markdown"],
        save_video=False,
    )
    reference_summary = reference.report["summary"]
    held_out_summary = held_out.report["summary"]
    report = {
        "schema_name": "robo-genesis-l13-capstone-report",
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "question": statements["question"],
        "evidence": {
            "environment": reference.report["environment"],
            "artifacts": reference.report["artifacts"],
            "protocol": reference.report["protocol"],
            "reference_report": str(reference.paths["results"]),
            "held_out_report": str(held_out.paths["results"]),
            "reference_summary": reference_summary,
            "held_out_summary": held_out_summary,
            "paired_outcome_changes": [dict(row) for row in paired_changes],
        },
        "conclusion_boundary": {
            "supported": statements["supported"],
            "not_supported": statements["not_supported"],
            "next_evidence": statements["next_evidence"],
        },
        "reproduce_with": {
            "reference": shlex.join(reference.command),
            "held_out": shlex.join(held_out.command),
        },
        "limitations": sorted(
            set(reference.report["limitations"] + held_out.report["limitations"])
        ),
    }
    reference_k = reference_summary["successes"]
    reference_n = reference_summary["episodes"]
    held_out_k = held_out_summary["successes"]
    held_out_n = held_out_summary["episodes"]
    markdown = (
        f"# L13 Capstone report\n\n## Question\n\n{statements['question']}\n\n"
        f"## Observed evidence\n\n- Reference: {reference_k}/{reference_n}, "
        f"95% Wilson interval {reference_summary['wilson_95']}\n"
        f"- {held_out.report['condition']['name']}: {held_out_k}/{held_out_n}, "
        f"95% Wilson interval {held_out_summary['wilson_95']}\n"
        f"- Matched outcome rows: {len(paired_changes)}\n\n"
        f"## Conclusion boundary\n\n- Supported: {statements['supported']}\n"
        f"- Not supported: {statements['not_supported']}\n"
        f"- Next evidence: {statements['next_evidence']}\n\n"
        f"## Reproduce with\n\n```sh\n{shlex.join(reference.command)}\n"
        f"{shlex.join(held_out.command)}\n```\n"
    )
    root.mkdir(parents=True, exist_ok=True)
    paths["json"].write_text(json.dumps(report, indent=2), encoding="utf-8")
    paths["markdown"].write_text(markdown, encoding="utf-8")
    return {"report": report, "markdown": markdown, "paths": paths}


__all__ = [
    "L13ConditionRun",
    "L13InputAudit",
    "L13Workflow",
    "audit_l13_evidence",
    "audit_l13_inputs",
    "build_l13_evaluation_command",
    "build_l13_capstone_guidance",
    "capstone_statements",
    "compare_l13_runs",
    "declare_l13_conditions",
    "evaluator_environment_overrides",
    "prepare_l13_workflow",
    "require_l13_inputs",
    "resolve_checkpoint_source",
    "resolve_dataset_fallback",
    "run_l13_condition",
    "runtime_summary",
    "write_l13_capstone_report",
]
