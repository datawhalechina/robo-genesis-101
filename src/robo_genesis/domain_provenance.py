"""Pure helpers for domain-randomization provenance and split planning.

The recorder owns simulation and dataset I/O.  This module deliberately depends
only on the Python standard library so configuration, sidecar, seed-schedule,
and split contracts can be tested without Genesis or LeRobot.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

DOMAIN_PROVENANCE_SCHEMA_VERSION = 1
DOMAIN_PROVENANCE_RELATIVE_PATH = Path("meta") / "robo_genesis_domain_randomization.json"
DOMAIN_SPLIT_MODES = ("in_distribution", "held_out_domain")


class DomainProvenanceError(ValueError):
    """Raised when a DR configuration, sidecar, or split violates its contract."""


def _finite_float(name: str, value: object) -> float:
    if isinstance(value, bool):
        raise DomainProvenanceError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DomainProvenanceError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise DomainProvenanceError(f"{name} must be a finite number")
    return number


def _positive_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise DomainProvenanceError(f"{name} must be a positive integer")
    return value


def _nonnegative(name: str, value: object) -> float:
    number = _finite_float(name, value)
    if number < 0.0:
        raise DomainProvenanceError(f"{name} must be non-negative")
    return number


def _positive_range(name: str, values: Sequence[float]) -> tuple[float, float]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or len(values) != 2:
        raise DomainProvenanceError(f"{name} must contain exactly two values")
    low = _finite_float(f"{name}[0]", values[0])
    high = _finite_float(f"{name}[1]", values[1])
    if low <= 0.0 or high <= 0.0:
        raise DomainProvenanceError(f"{name} values must be positive")
    if low > high:
        raise DomainProvenanceError(f"{name} lower bound must not exceed its upper bound")
    return low, high


def validate_dr_collection_config(
    *,
    episodes: int,
    max_attempts: int,
    fps: int,
    image_width: int,
    image_height: int,
    dr_rebuild_every: int,
    table_color_jitter: float,
    fov_jitter_deg: float,
    camera_fovs_deg: Sequence[float],
    friction_ratio_range: Sequence[float],
    mass_ratio_range: Sequence[float],
    cam_pos_jitter: float,
    cam_lookat_jitter: float,
) -> dict[str, Any]:
    """Validate and normalize the bounded collection settings used by L11."""

    normalized_episodes = _positive_int("episodes", episodes)
    normalized_attempts = _positive_int("max_attempts", max_attempts)
    if normalized_attempts < normalized_episodes:
        raise DomainProvenanceError("max_attempts must be at least episodes")

    normalized_fps = _positive_int("fps", fps)
    normalized_width = _positive_int("image_width", image_width)
    normalized_height = _positive_int("image_height", image_height)
    normalized_rebuild = _positive_int("dr_rebuild_every", dr_rebuild_every)
    table_jitter = _nonnegative("table_color_jitter", table_color_jitter)
    fov_jitter = _nonnegative("fov_jitter_deg", fov_jitter_deg)
    camera_fovs = tuple(_finite_float("camera_fov", value) for value in camera_fovs_deg)
    if not camera_fovs or any(value <= 0.0 for value in camera_fovs):
        raise DomainProvenanceError("camera_fovs_deg must contain positive values")
    if fov_jitter >= min(camera_fovs):
        raise DomainProvenanceError(
            "fov_jitter_deg must be smaller than every baseline camera FOV"
        )

    friction_range = _positive_range("friction_ratio_range", friction_ratio_range)
    mass_range = _positive_range("mass_ratio_range", mass_ratio_range)
    position_jitter = _nonnegative("cam_pos_jitter", cam_pos_jitter)
    lookat_jitter = _nonnegative("cam_lookat_jitter", cam_lookat_jitter)

    return {
        "episodes": normalized_episodes,
        "max_attempts": normalized_attempts,
        "fps": normalized_fps,
        "image_width": normalized_width,
        "image_height": normalized_height,
        "dr_rebuild_every": normalized_rebuild,
        "table_color_jitter": table_jitter,
        "fov_jitter_deg": fov_jitter,
        "camera_fovs_deg": list(camera_fovs),
        "friction_ratio_range": list(friction_range),
        "mass_ratio_range": list(mass_range),
        "cam_pos_jitter": position_jitter,
        "cam_lookat_jitter": lookat_jitter,
    }


def plan_seed_schedule(
    outcomes: Iterable[bool],
    *,
    runtime_base_seed: int,
    appearance_base_seed: int,
    rebuild_every: int,
    appearance_enabled: bool = True,
) -> list[dict[str, Any]]:
    """Return the deterministic attempt/success/domain schedule for known outcomes."""

    _positive_int("rebuild_every", rebuild_every)
    if isinstance(runtime_base_seed, bool) or not isinstance(runtime_base_seed, int):
        raise DomainProvenanceError("runtime_base_seed must be an integer")
    if isinstance(appearance_base_seed, bool) or not isinstance(appearance_base_seed, int):
        raise DomainProvenanceError("appearance_base_seed must be an integer")

    committed_successes = 0
    schedule: list[dict[str, Any]] = []
    for attempt_index, outcome in enumerate(outcomes):
        if not isinstance(outcome, bool):
            raise DomainProvenanceError("outcomes must contain booleans")
        domain_index = committed_successes // rebuild_every if appearance_enabled else 0
        schedule.append(
            {
                "attempt_index": attempt_index,
                "runtime_seed": runtime_base_seed + attempt_index,
                "appearance_domain_index": domain_index,
                "appearance_seed": (
                    appearance_base_seed + domain_index if appearance_enabled else None
                ),
                "success": outcome,
                "committed_episode_index": committed_successes if outcome else None,
            }
        )
        committed_successes += int(outcome)
    return schedule


def _require_mapping(value: object, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DomainProvenanceError(f"{location} must be an object")
    return value


def _require_int(value: object, location: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise DomainProvenanceError(f"{location} must be an integer >= {minimum}")
    return value


def validate_domain_provenance(provenance: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the sidecar fields needed for replay and domain-aware splitting."""

    data = dict(_require_mapping(provenance, "provenance"))
    if data.get("schema_version") != DOMAIN_PROVENANCE_SCHEMA_VERSION:
        raise DomainProvenanceError(
            f"unsupported schema_version: {data.get('schema_version')!r}"
        )
    if not isinstance(data.get("implementation_version"), str) or not data[
        "implementation_version"
    ].strip():
        raise DomainProvenanceError("implementation_version must be a non-empty string")

    requested = _require_mapping(data.get("requested"), "requested")
    appearance = _require_mapping(requested.get("appearance"), "requested.appearance")
    runtime = _require_mapping(requested.get("runtime"), "requested.runtime")
    requested_successes = _require_int(
        requested.get("successful_episodes"), "requested.successful_episodes", minimum=1
    )
    requested_max_attempts = _require_int(
        requested.get("max_attempts"), "requested.max_attempts", minimum=1
    )
    if requested_max_attempts < requested_successes:
        raise DomainProvenanceError(
            "requested.max_attempts must be at least requested.successful_episodes"
        )
    rebuild_every = _require_int(
        appearance.get("rebuild_every"), "requested.appearance.rebuild_every", minimum=1
    )
    appearance_enabled = appearance.get("enabled")
    if not isinstance(appearance_enabled, bool):
        raise DomainProvenanceError("requested.appearance.enabled must be boolean")
    if not isinstance(runtime.get("enabled"), bool):
        raise DomainProvenanceError("requested.runtime.enabled must be boolean")
    appearance_base_seed = appearance.get("base_seed")
    runtime_base_seed = runtime.get("base_seed")
    if isinstance(appearance_base_seed, bool) or not isinstance(appearance_base_seed, int):
        raise DomainProvenanceError("requested.appearance.base_seed must be an integer")
    if isinstance(runtime_base_seed, bool) or not isinstance(runtime_base_seed, int):
        raise DomainProvenanceError("requested.runtime.base_seed must be an integer")
    friction_range = _positive_range(
        "requested.runtime.friction_ratio_range",
        runtime.get("friction_ratio_range"),
    )
    mass_range = _positive_range(
        "requested.runtime.mass_ratio_range", runtime.get("mass_ratio_range")
    )
    _nonnegative("requested.runtime.cam_pos_jitter", runtime.get("cam_pos_jitter"))
    _nonnegative("requested.runtime.cam_lookat_jitter", runtime.get("cam_lookat_jitter"))

    raw_attempts = data.get("attempts")
    if not isinstance(raw_attempts, list):
        raise DomainProvenanceError("attempts must be an array")
    committed_successes = 0
    committed_dataset_episodes = 0
    successful_attempts = 0
    failed_attempts = 0
    committed_debug_failures = 0
    committed_indices: set[int] = set()
    for expected_index, raw_attempt in enumerate(raw_attempts):
        attempt = _require_mapping(raw_attempt, f"attempts[{expected_index}]")
        attempt_index = _require_int(
            attempt.get("attempt_index"), f"attempts[{expected_index}].attempt_index"
        )
        if attempt_index != expected_index:
            raise DomainProvenanceError("attempt_index values must be contiguous from zero")
        if attempt.get("runtime_seed") != runtime_base_seed + attempt_index:
            raise DomainProvenanceError("runtime_seed does not match base seed + attempt_index")

        expected_domain = committed_successes // rebuild_every if appearance_enabled else 0
        if attempt.get("appearance_domain_index") != expected_domain:
            raise DomainProvenanceError("appearance_domain_index does not follow success quota")
        expected_appearance_seed = (
            appearance_base_seed + expected_domain if appearance_enabled else None
        )
        if attempt.get("appearance_seed") != expected_appearance_seed:
            raise DomainProvenanceError("appearance_seed does not match the declared schedule")

        success = attempt.get("success")
        committed = attempt.get("committed")
        if not isinstance(success, bool) or not isinstance(committed, bool):
            raise DomainProvenanceError("attempt success and committed fields must be boolean")
        episode_index = attempt.get("committed_episode_index")
        if committed:
            episode_index = _require_int(
                episode_index, f"attempts[{expected_index}].committed_episode_index"
            )
            if episode_index != committed_dataset_episodes:
                raise DomainProvenanceError(
                    "committed_episode_index values must follow dataset commit order"
                )
            if episode_index in committed_indices:
                raise DomainProvenanceError("committed_episode_index values must be unique")
            committed_indices.add(episode_index)
            committed_dataset_episodes += 1
        elif episode_index is not None:
            raise DomainProvenanceError(
                "an uncommitted attempt cannot have committed_episode_index"
            )
        frame_count = _require_int(
            attempt.get("frame_count"), f"attempts[{expected_index}].frame_count"
        )
        if committed and frame_count == 0:
            raise DomainProvenanceError("a committed attempt must contain at least one frame")
        actual = _require_mapping(attempt.get("actual"), f"attempts[{expected_index}].actual")
        friction_ratio = actual.get("friction_ratio")
        mass_ratios = actual.get("mass_ratios")
        world_camera_pose = actual.get("world_camera_pose")
        if runtime["enabled"]:
            normalized_friction = _finite_float(
                f"attempts[{expected_index}].actual.friction_ratio", friction_ratio
            )
            if not friction_range[0] <= normalized_friction <= friction_range[1]:
                raise DomainProvenanceError("actual friction ratio is outside the requested range")
            mass_ratios = _require_mapping(
                mass_ratios, f"attempts[{expected_index}].actual.mass_ratios"
            )
            if not mass_ratios:
                raise DomainProvenanceError("runtime DR must record per-object mass ratios")
            for object_name, mass_ratio in mass_ratios.items():
                if not isinstance(object_name, str) or not object_name:
                    raise DomainProvenanceError("mass-ratio object names must be non-empty strings")
                normalized_mass = _finite_float(
                    f"attempts[{expected_index}].actual.mass_ratios[{object_name!r}]",
                    mass_ratio,
                )
                if not mass_range[0] <= normalized_mass <= mass_range[1]:
                    raise DomainProvenanceError("actual mass ratio is outside the requested range")
            world_camera_pose = _require_mapping(
                world_camera_pose,
                f"attempts[{expected_index}].actual.world_camera_pose",
            )
            for vector_name in ("pos", "lookat"):
                vector = world_camera_pose.get(vector_name)
                if (
                    not isinstance(vector, Sequence)
                    or isinstance(vector, (str, bytes))
                    or len(vector) != 3
                ):
                    raise DomainProvenanceError(
                        f"actual world-camera {vector_name} must contain three values"
                    )
                for value in vector:
                    _finite_float(
                        f"attempts[{expected_index}].actual.world_camera_pose.{vector_name}",
                        value,
                    )
        elif (
            friction_ratio is not None
            or mass_ratios not in ({}, None)
            or world_camera_pose is not None
        ):
            raise DomainProvenanceError(
                "runtime-disabled attempts must not claim runtime DR values"
            )
        successful_attempts += int(success)
        failed_attempts += int(not success)
        committed_debug_failures += int(committed and not success)
        if success and committed:
            committed_successes += 1

    summary = _require_mapping(data.get("summary"), "summary")
    if len(raw_attempts) > requested_max_attempts:
        raise DomainProvenanceError("attempts exceed requested.max_attempts")
    summary_attempts = _require_int(summary.get("attempts"), "summary.attempts")
    summary_successes = _require_int(
        summary.get("successful_attempts"), "summary.successful_attempts"
    )
    summary_failures = _require_int(
        summary.get("failed_attempts"), "summary.failed_attempts"
    )
    summary_committed_successes = _require_int(
        summary.get("committed_successful_episodes"),
        "summary.committed_successful_episodes",
    )
    summary_debug_failures = _require_int(
        summary.get("committed_debug_failures"), "summary.committed_debug_failures"
    )
    if summary_attempts != len(raw_attempts):
        raise DomainProvenanceError("summary.attempts does not match attempts")
    if summary_committed_successes != committed_successes:
        raise DomainProvenanceError(
            "summary.committed_successful_episodes does not match attempts"
        )
    if summary_successes != successful_attempts:
        raise DomainProvenanceError("summary.successful_attempts does not match attempts")
    if summary_failures != failed_attempts:
        raise DomainProvenanceError("summary.failed_attempts does not match attempts")
    if summary_debug_failures != committed_debug_failures:
        raise DomainProvenanceError("summary.committed_debug_failures does not match attempts")
    if committed_successes > requested_successes:
        raise DomainProvenanceError("committed successes exceed the requested quota")
    expected_complete = committed_successes == requested_successes
    if not isinstance(summary.get("complete"), bool) or summary["complete"] != expected_complete:
        raise DomainProvenanceError("summary.complete does not match the requested quota")
    return data


def write_domain_provenance(dataset_root: Path, provenance: Mapping[str, Any]) -> Path:
    """Validate and atomically write the course-owned sidecar after finalization."""

    data = validate_domain_provenance(provenance)
    path = Path(dataset_root).resolve() / DOMAIN_PROVENANCE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary_path.replace(path)
    return path


def load_domain_provenance(path_or_dataset_root: Path) -> dict[str, Any]:
    """Read a sidecar path, or resolve the canonical sidecar below a dataset root."""

    path = Path(path_or_dataset_root).expanduser().resolve()
    if path.is_dir():
        path = path / DOMAIN_PROVENANCE_RELATIVE_PATH
    if not path.is_file():
        raise FileNotFoundError(f"domain-randomization provenance not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DomainProvenanceError(f"invalid provenance JSON at {path}: {exc}") from exc
    return validate_domain_provenance(_require_mapping(data, str(path)))


def committed_episode_records(provenance: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return successful committed attempts ordered by dataset episode index."""

    data = validate_domain_provenance(provenance)
    records = [
        dict(attempt)
        for attempt in data["attempts"]
        if attempt["success"] and attempt["committed"]
    ]
    return sorted(records, key=lambda record: record["committed_episode_index"])


def _ordered_unique(values: Iterable[Any]) -> list[Any]:
    return sorted(set(values), key=lambda value: (type(value).__name__, repr(value)))


def validate_domain_split(
    records: Sequence[Mapping[str, Any]],
    train_episode_ids: Sequence[int],
    eval_episode_ids: Sequence[int],
    *,
    domain_key: str = "appearance_domain_index",
    require_disjoint_domains: bool = False,
    require_full_coverage: bool = True,
) -> dict[str, Any]:
    """Validate episode identity and optional domain-group isolation for one split."""

    record_by_episode: dict[int, Mapping[str, Any]] = {}
    for position, raw_record in enumerate(records):
        record = _require_mapping(raw_record, f"records[{position}]")
        episode_index = _require_int(
            record.get("committed_episode_index"),
            f"records[{position}].committed_episode_index",
        )
        if episode_index in record_by_episode:
            raise DomainProvenanceError("records contain duplicate committed episode IDs")
        if domain_key not in record:
            raise DomainProvenanceError(f"records[{position}] is missing {domain_key!r}")
        record_by_episode[episode_index] = record

    train_ids = [_require_int(value, "train_episode_id") for value in train_episode_ids]
    eval_ids = [_require_int(value, "eval_episode_id") for value in eval_episode_ids]
    if not train_ids or not eval_ids:
        raise DomainProvenanceError("train and eval must each contain at least one episode")
    if len(set(train_ids)) != len(train_ids) or len(set(eval_ids)) != len(eval_ids):
        raise DomainProvenanceError("split episode IDs must be unique within each side")
    overlap = set(train_ids) & set(eval_ids)
    if overlap:
        raise DomainProvenanceError(f"train/eval episode overlap: {sorted(overlap)}")

    known_ids = set(record_by_episode)
    selected_ids = set(train_ids) | set(eval_ids)
    unknown_ids = selected_ids - known_ids
    if unknown_ids:
        raise DomainProvenanceError(f"split references unknown episodes: {sorted(unknown_ids)}")
    if require_full_coverage and selected_ids != known_ids:
        missing_ids = known_ids - selected_ids
        raise DomainProvenanceError(f"split omits episodes: {sorted(missing_ids)}")

    train_domains = _ordered_unique(record_by_episode[index][domain_key] for index in train_ids)
    eval_domains = _ordered_unique(record_by_episode[index][domain_key] for index in eval_ids)
    domain_overlap = _ordered_unique(set(train_domains) & set(eval_domains))
    if require_disjoint_domains and domain_overlap:
        raise DomainProvenanceError(f"train/eval domain overlap: {domain_overlap}")

    return {
        "train_episode_ids": train_ids,
        "eval_episode_ids": eval_ids,
        "domain_key": domain_key,
        "train_domain_ids": train_domains,
        "eval_domain_ids": eval_domains,
        "overlapping_domain_ids": domain_overlap,
        "all_episodes_covered": selected_ids == known_ids,
    }


def plan_domain_split(
    records: Sequence[Mapping[str, Any]],
    *,
    eval_fraction: float = 0.2,
    mode: str = "in_distribution",
    domain_key: str = "appearance_domain_index",
) -> dict[str, Any]:
    """Plan a deterministic episode split without copying or mutating dataset files."""

    fraction = _finite_float("eval_fraction", eval_fraction)
    if not 0.0 < fraction < 1.0:
        raise DomainProvenanceError("eval_fraction must be strictly between zero and one")
    if mode not in DOMAIN_SPLIT_MODES:
        raise DomainProvenanceError(f"mode must be one of {DOMAIN_SPLIT_MODES}")

    ordered_records = sorted(
        (_require_mapping(record, "record") for record in records),
        key=lambda record: _require_int(
            record.get("committed_episode_index"), "committed_episode_index"
        ),
    )
    if len(ordered_records) < 2:
        raise DomainProvenanceError("at least two committed episodes are required")

    if mode == "in_distribution":
        domains = _ordered_unique(record.get(domain_key) for record in ordered_records)
        train_ids = []
        eval_ids = []
        for domain in domains:
            domain_episode_ids = [
                record["committed_episode_index"]
                for record in ordered_records
                if record.get(domain_key) == domain
            ]
            if len(domain_episode_ids) < 2:
                raise DomainProvenanceError(
                    "in_distribution requires at least two episodes in every "
                    f"{domain_key} group; domain {domain!r} has "
                    f"{len(domain_episode_ids)}"
                )
            eval_count = min(
                len(domain_episode_ids) - 1,
                max(1, math.ceil(len(domain_episode_ids) * fraction)),
            )
            train_ids.extend(domain_episode_ids[:-eval_count])
            eval_ids.extend(domain_episode_ids[-eval_count:])
        require_disjoint_domains = False
    else:
        domains = _ordered_unique(record.get(domain_key) for record in ordered_records)
        if len(domains) < 2:
            raise DomainProvenanceError(
                f"held_out_domain requires at least two distinct {domain_key} values"
            )
        eval_domain_count = min(
            len(domains) - 1, max(1, math.ceil(len(domains) * fraction))
        )
        eval_domain_set = set(domains[-eval_domain_count:])
        train_ids = [
            record["committed_episode_index"]
            for record in ordered_records
            if record.get(domain_key) not in eval_domain_set
        ]
        eval_ids = [
            record["committed_episode_index"]
            for record in ordered_records
            if record.get(domain_key) in eval_domain_set
        ]
        require_disjoint_domains = True

    result = validate_domain_split(
        ordered_records,
        train_ids,
        eval_ids,
        domain_key=domain_key,
        require_disjoint_domains=require_disjoint_domains,
    )
    result["mode"] = mode
    result["eval_fraction"] = fraction
    return result


__all__ = [
    "DOMAIN_PROVENANCE_RELATIVE_PATH",
    "DOMAIN_PROVENANCE_SCHEMA_VERSION",
    "DOMAIN_SPLIT_MODES",
    "DomainProvenanceError",
    "committed_episode_records",
    "load_domain_provenance",
    "plan_domain_split",
    "plan_seed_schedule",
    "validate_domain_provenance",
    "validate_domain_split",
    "validate_dr_collection_config",
    "write_domain_provenance",
]
