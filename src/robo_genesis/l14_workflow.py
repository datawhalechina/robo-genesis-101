"""Dependency-light contracts for the optional L14 RoboTwin/LingBot practicum.

The external ``Robotwin-radeon-cloud`` companion remains the runtime source of
truth for containers, RoboTwin patches, training launchers, and model serving.
This module only validates the values exposed by the course notebook, builds a
small number of commands, and turns aggregate evaluator logs into scoped
evidence.  It deliberately does not import or monkey-patch the companion.
"""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .stats import wilson


COMPANION_COMMIT = "27b2f6fcb6c715e2cbb6db4431381f87c94b86ed"
ROBOTWIN_COMMIT = "266f3aadf505a4f7fe9af0faa41a20f5f47cd123"
AGGREGATE_EVIDENCE_MODE = "independent-aggregate"

_SUCCESS_RATE_RE = re.compile(
    r"Final(?: batch)? success rate:\s*(?P<successes>\d+)\s*/\s*(?P<episodes>\d+)"
)
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_PROGRESS_RATE_RE = re.compile(
    r"(?m)^\s*Success rate:\s*(?P<successes>\d+)\s*/\s*(?P<episodes>\d+)"
)


class L14ContractError(ValueError):
    """Raised when a notebook configuration or artifact breaks the L14 contract."""


@dataclass(frozen=True)
class AggregateEvaluation:
    """One aggregate closed-loop result parsed from a companion evaluator log."""

    condition: str
    successes: int
    episodes: int
    rate: float
    wilson_low: float
    wilson_high: float
    log_path: str | None = None


def validate_l14_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the learner-visible configuration without importing GPU stacks."""

    required = {
        "run_name",
        "robotwin_root",
        "runtime_root",
        "python",
        "task_name",
        "task_config",
        "core_gpu_count",
        "competition_gpu_count",
        "lora_steps",
        "eval_episodes",
        "training_seed",
    }
    missing = sorted(required - set(config))
    if missing:
        raise L14ContractError(f"missing L14 config keys: {missing}")

    run_name = str(config["run_name"]).strip()
    if not run_name or Path(run_name).name != run_name:
        raise L14ContractError("run_name must be one non-empty directory name")

    core_gpu_count = int(config["core_gpu_count"])
    competition_gpu_count = int(config["competition_gpu_count"])
    if core_gpu_count != 4:
        raise L14ContractError("the required course profile uses exactly 4 GPUs")
    if competition_gpu_count not in (4, 8):
        raise L14ContractError("competition_gpu_count must be 4 or 8")

    positive_fields = ("lora_steps", "eval_episodes")
    for field in positive_fields:
        if int(config[field]) <= 0:
            raise L14ContractError(f"{field} must be positive")

    task_name = str(config["task_name"]).strip()
    task_config = str(config["task_config"]).strip()
    if not task_name or not task_config:
        raise L14ContractError("task_name and task_config must be non-empty")

    normalized = dict(config)
    normalized.update(
        run_name=run_name,
        robotwin_root=str(Path(config["robotwin_root"]).expanduser()),
        runtime_root=str(Path(config["runtime_root"]).expanduser()),
        python=str(Path(config["python"]).expanduser()),
        task_name=task_name,
        task_config=task_config,
        core_gpu_count=core_gpu_count,
        competition_gpu_count=competition_gpu_count,
        lora_steps=int(config["lora_steps"]),
        eval_episodes=int(config["eval_episodes"]),
        training_seed=int(config["training_seed"]),
    )
    return normalized


def l14_output_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    """Resolve stable, condition-specific output paths for one notebook run."""

    normalized = validate_l14_config(config)
    runtime_root = Path(normalized["runtime_root"]).resolve()
    run_root = runtime_root / "outputs" / "robo_genesis_l14" / normalized["run_name"]
    logs = run_root / "logs"
    return {
        "run_root": run_root,
        "logs": logs,
        "manifest": run_root / "run_manifest.json",
        "base_eval_log": logs / "base_evaluation.log",
        "merged_eval_log": logs / "merged_lora_evaluation.log",
        "base_videos": run_root / "videos" / "base",
        "merged_videos": run_root / "videos" / "merged_lora",
        "official_videos": run_root / "videos" / "official_robotwin",
        "full_sft_videos": run_root / "videos" / "full_sft",
        "aggregate_evidence": run_root / "aggregate_evidence.json",
        "lora_output": run_root / "lora_training",
        "full_sft_output": run_root / "full_sft_training",
    }


def require_fresh_paths(paths: Iterable[str | Path]) -> None:
    """Reject output collisions before a long-running command starts."""

    collisions = sorted(str(Path(path)) for path in paths if Path(path).exists())
    if collisions:
        raise FileExistsError(
            "L14 output paths already exist; choose a fresh run_name:\n- "
            + "\n- ".join(collisions)
        )


def snapshot_files(
    root: str | Path, *, suffixes: Iterable[str] = (".mp4",)
) -> dict[str, dict[str, int]]:
    """Snapshot selected files without assuming the evaluator's directory layout."""

    source = Path(root)
    normalized_suffixes = {str(suffix).lower() for suffix in suffixes}
    if not source.exists():
        return {}
    snapshot: dict[str, dict[str, int]] = {}
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in normalized_suffixes:
            continue
        stat = path.stat()
        snapshot[str(path.relative_to(source))] = {
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        }
    return snapshot


def archive_changed_files(
    root: str | Path,
    before: Mapping[str, Mapping[str, int]],
    output_dir: str | Path,
    *,
    suffixes: Iterable[str] = (".mp4",),
) -> list[str]:
    """Copy files created or replaced by one evaluation into a fresh archive."""

    source = Path(root)
    destination = Path(output_dir)
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite L14 archive: {destination}")
    after = snapshot_files(source, suffixes=suffixes)
    changed = [
        relative
        for relative, metadata in after.items()
        if relative not in before or dict(before[relative]) != metadata
    ]
    if not changed:
        raise L14ContractError(
            f"evaluation produced no new or changed files under {source}"
        )
    archived: list[str] = []
    for relative in changed:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)
        archived.append(str(target))
    return archived


def audit_required_paths(paths: Mapping[str, str | Path]) -> dict[str, Any]:
    """Return a serializable path audit and fail when any required input is absent."""

    rows = []
    missing = []
    for name, raw_path in paths.items():
        path = Path(raw_path).expanduser().resolve()
        exists = path.exists()
        rows.append({"name": str(name), "path": str(path), "exists": exists})
        if not exists:
            missing.append(str(path))
    if missing:
        raise FileNotFoundError("missing L14 inputs:\n- " + "\n- ".join(missing))
    return {"ready": True, "paths": rows}


def audit_hf_checkpoint(root: str | Path) -> dict[str, Any]:
    """Validate the minimum config/processor/weight-index serving artifact."""

    checkpoint = Path(root).expanduser().resolve()
    index_path = checkpoint / "model.safetensors.index.json"
    config_path = checkpoint / "config.json"
    if not checkpoint.is_dir() or not index_path.is_file() or not config_path.is_file():
        raise FileNotFoundError(
            "Hugging Face checkpoint requires config.json and "
            f"model.safetensors.index.json under {checkpoint}"
        )
    index = json.loads(index_path.read_text(encoding="utf-8"))
    weight_map = index.get("weight_map")
    if not isinstance(weight_map, dict) or not weight_map:
        raise L14ContractError("checkpoint weight index has no weight_map")
    shards = sorted({str(name) for name in weight_map.values()})
    missing = [name for name in shards if not (checkpoint / name).is_file()]
    if missing:
        raise FileNotFoundError(f"checkpoint index references missing shards: {missing}")
    processor_candidates = (
        "preprocessor_config.json",
        "processor_config.json",
        "tokenizer_config.json",
    )
    processor_files = [
        name for name in processor_candidates if (checkpoint / name).is_file()
    ]
    if not processor_files:
        raise FileNotFoundError(
            f"checkpoint has no processor/tokenizer config under {checkpoint}"
        )
    return {
        "root": str(checkpoint),
        "config": str(config_path),
        "weight_index": str(index_path),
        "shards": shards,
        "processor_files": processor_files,
    }


def build_single_task_eval_command(
    *,
    python: str | Path,
    robotwin_root: str | Path,
    task_name: str,
    task_config: str,
    episodes: int,
    port: int = 13400,
    video: bool = True,
    batch: bool = False,
    num_workers: int = 1,
    max_seed_attempts: int | None = None,
    seed_start: int | None = None,
) -> tuple[str, ...]:
    """Build the pinned companion's one-task evaluator command.

    ``seed_start`` lets the course continue with a fresh seed range when the
    companion's serial evaluator consumes requested slots on unstable setup.
    The companion command and evaluator source remain unmodified.
    """

    if episodes <= 0:
        raise L14ContractError("episodes must be positive")
    if not (1 <= int(port) <= 65535):
        raise L14ContractError("port must be between 1 and 65535")
    if num_workers <= 0:
        raise L14ContractError("num_workers must be positive")
    seed_attempt_limit = (
        int(max_seed_attempts)
        if max_seed_attempts is not None
        else int(episodes) * 50
    )
    if seed_attempt_limit < episodes:
        raise L14ContractError("max_seed_attempts must cover all episodes")
    command = [
        str(python),
        str(Path(robotwin_root) / "scripts/eval_policy_xpolicylab.py"),
        "--task_name",
        task_name,
        "--task_config",
        task_config,
        "--policy_name",
        "LingBot-VLA-v2",
        "--protocol",
        "lingbot_vla_v2",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--device_id",
        "0",
        "--seed",
        "0",
    ]
    if seed_start is not None:
        command.extend(("--seed_start", str(int(seed_start))))
    command.extend(
        (
        "--test_num",
        str(episodes),
        "--expert_check",
        "true",
        "--accept_expert_info_on_failure",
        "true",
        "--eval_batch",
        str(bool(batch)).lower(),
        "--additional_info",
        f"eval_video_log={str(video).lower()}",
        )
    )
    if batch:
        command.extend(
            (
                "--num_workers",
                str(num_workers),
                "--max_seed_attempts",
                str(seed_attempt_limit),
            )
        )
    return tuple(command)


def command_text(command: Sequence[str]) -> str:
    """Render a command for learner inspection without invoking a shell."""

    return shlex.join(str(part) for part in command)


def run_command_logged(
    command: Sequence[str],
    *,
    cwd: str | Path,
    env: Mapping[str, str] | None,
    log_path: str | Path,
) -> str:
    """Run one command without a shell while streaming stdout to a fresh log."""

    output = Path(log_path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite L14 log: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    with output.open("x", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [str(part) for part in command],
            cwd=Path(cwd),
            env=dict(env) if env is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            log_file.write(line)
            lines.append(line)
        return_code = process.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, list(command))
    return "".join(lines)


def parse_final_success_rate(
    text: str,
    *,
    condition: str,
    log_path: str | Path | None = None,
) -> AggregateEvaluation:
    """Parse the last aggregate serial or batch ``Final ... rate: k/n`` line."""

    matches = list(_SUCCESS_RATE_RE.finditer(text))
    if not matches:
        raise L14ContractError(
            "evaluator log has no Final success rate or "
            "Final batch success rate: k/n line"
        )
    match = matches[-1]
    successes = int(match.group("successes"))
    episodes = int(match.group("episodes"))
    if episodes <= 0 or successes > episodes:
        raise L14ContractError("invalid aggregate success count in evaluator log")
    low, high = wilson(successes, episodes)
    return AggregateEvaluation(
        condition=str(condition),
        successes=successes,
        episodes=episodes,
        rate=successes / episodes,
        wilson_low=low,
        wilson_high=high,
        log_path=str(Path(log_path)) if log_path is not None else None,
    )


def parse_last_progress_rate(text: str) -> tuple[int, int] | None:
    """Parse the last completed-episode progress line from a serial log.

    This deliberately ignores the companion's fixed final requested-slot
    denominator.  A serial invocation that completed no policy episode returns
    ``None``.
    """

    clean_text = _ANSI_ESCAPE_RE.sub("", text)
    matches = list(_PROGRESS_RATE_RE.finditer(clean_text))
    if not matches:
        return None
    match = matches[-1]
    successes = int(match.group("successes"))
    episodes = int(match.group("episodes"))
    if episodes <= 0 or successes > episodes:
        raise L14ContractError("invalid completed-episode progress count")
    return successes, episodes


def parse_success_rate_file(
    path: str | Path, *, condition: str
) -> AggregateEvaluation:
    """Read and parse one evaluator log."""

    log_path = Path(path)
    return parse_final_success_rate(
        log_path.read_text(encoding="utf-8", errors="replace"),
        condition=condition,
        log_path=log_path,
    )


def build_aggregate_evidence_card(
    base: AggregateEvaluation,
    merged: AggregateEvaluation,
    *,
    companion_commit: str = COMPANION_COMMIT,
    robotwin_commit: str = ROBOTWIN_COMMIT,
    identities: Mapping[str, Any] | None = None,
    video_artifacts: Mapping[str, Sequence[str | Path]] | None = None,
) -> dict[str, Any]:
    """Build a deliberately non-matched comparison for the current companion."""

    return {
        "schema_version": "1.0.0",
        "evidence_mode": AGGREGATE_EVIDENCE_MODE,
        "companion_commit": companion_commit,
        "robotwin_commit": robotwin_commit,
        "identities": dict(identities or {}),
        "video_artifacts": {
            str(condition): [str(path) for path in paths]
            for condition, paths in (video_artifacts or {}).items()
        },
        "base": asdict(base),
        "merged": asdict(merged),
        "observed_rate_difference": merged.rate - base.rate,
        "resolved_seed_matching_available": False,
        "matched_outcomes": None,
        "conclusion_boundary": (
            "The two k/n values are independent small-run observations. "
            "The current companion log cannot prove that base and merged "
            "evaluations used the same resolved seeds, so no matched-policy "
            "improvement claim is made."
        ),
    }


def write_json_artifact(
    path: str | Path, payload: Mapping[str, Any], *, fresh: bool = True
) -> Path:
    """Write one readable JSON artifact, optionally rejecting overwrite."""

    output = Path(path)
    if fresh and output.exists():
        raise FileExistsError(f"refusing to overwrite L14 artifact: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output
