import json
from pathlib import Path

import numpy as np
import pytest

from robo_genesis.evaluation_contract import (
    DwellTracker,
    EvaluationContractError,
    audit_dataset_contract,
    balanced_object_schedule,
    build_condition_spec,
    build_evaluation_report,
    classify_condition,
    dwell_frame_count,
    evaluate_predicate_trace,
    paired_outcome_changes,
    normalize_policy_action,
    require_requested_device,
    summarize_episode_rows,
    validate_action_vector,
    validate_evaluation_protocol,
    validate_evaluation_report,
    validate_output_root,
    validate_output_targets,
)


AVAILABLE_OBJECTS = ("011_banana", "014_lemon", "018_plum", "024_bowl")


def _protocol(**overrides: object) -> dict[str, object]:
    values = {
        "episodes": 5,
        "policy_fps": 5.0,
        "control_fps": 100.0,
        "dwell_seconds": 0.4,
        "max_seconds": 15.0,
        "tolerance": 0.06,
        "pick_objects": ("011_banana",),
        "place_target": "024_bowl",
        "available_objects": AVAILABLE_OBJECTS,
        "base_seed": 1000,
        "balanced": True,
        "condition_name": "reference",
        "render_enabled": True,
    }
    values.update(overrides)
    return validate_evaluation_protocol(**values)


def _rows(successes: tuple[bool, ...] = (True, False, True)) -> list[dict[str, object]]:
    return [
        {
            "ep": index,
            "seed": 1000 + index,
            "pick": "011_banana",
            "steps": 10 + index,
            "success": success,
            "termination_reason": "success" if success else "timeout",
        }
        for index, success in enumerate(successes)
    ]


def test_dwell_uses_ceil_and_timeout_never_promotes_a_final_true_frame() -> None:
    assert dwell_frame_count(0.4, 5) == 2
    assert dwell_frame_count(0.4, 7) == 3

    failed = evaluate_predicate_trace(
        [False, False, True], dwell_seconds=0.4, policy_fps=5
    )
    assert failed == {
        "success": False,
        "termination_reason": "timeout",
        "steps": 3,
        "dwell_frames": 2,
        "max_streak": 1,
    }

    tracker = DwellTracker(required_frames=2)
    assert tracker.update(True) is False
    assert tracker.update(False) is False
    assert tracker.streak == 0
    assert tracker.update(True) is False
    assert tracker.update(True) is True


def test_balanced_schedule_is_deterministic_and_near_equal() -> None:
    objects = ("011_banana", "014_lemon", "018_plum")
    first = balanced_object_schedule(objects, episodes=8, seed=21)
    second = balanced_object_schedule(objects, episodes=8, seed=21)

    assert first == second
    counts = {name: first.count(name) for name in objects}
    assert max(counts.values()) - min(counts.values()) <= 1

    with pytest.raises(EvaluationContractError, match="duplicates"):
        balanced_object_schedule(("011_banana", "011_banana"), episodes=2, seed=0)


@pytest.mark.parametrize(
    ("training", "evaluation", "expected"),
    [
        ((0.7, 1.3), (0.8, 1.2), "unseen-in-support"),
        ((0.7, 1.3), (1.2, 1.5), "shifted"),
        ((0.7, 1.3), (1.4, 1.6), "ood"),
        (None, (1.4, 1.6), "shifted"),
    ],
)
def test_condition_labels_are_relative_to_training_support(
    training: tuple[float, float] | None,
    evaluation: tuple[float, float],
    expected: str,
) -> None:
    assert classify_condition(
        is_reference=False,
        training_support=training,
        evaluation_range=evaluation,
    ) == expected


def test_reference_is_a_role_and_false_ood_claims_are_rejected() -> None:
    reference = build_condition_spec(
        name="reference", declared_label="reference", held_constant=("task", "seeds")
    )
    assert reference["label"] == "reference"

    with pytest.raises(EvaluationContractError, match="conflicts"):
        build_condition_spec(
            name="held-out-friction",
            declared_label="ood",
            changed_factor="friction_ratio",
            training_support=(0.7, 1.3),
            evaluation_range=(1.2, 1.5),
        )


def test_protocol_preflight_rejects_invalid_counts_fps_objects_and_tolerance() -> None:
    protocol = _protocol()
    assert protocol["success_rule"]["dwell_frames"] == 2
    assert protocol["sampling"]["episode_seeds"] == [1000, 1001, 1002, 1003, 1004]

    for overrides, message in (
        ({"episodes": 0}, "episodes"),
        ({"policy_fps": 101.0}, "must not exceed"),
        ({"pick_objects": ()}, "pick_objects"),
        ({"pick_objects": ("999_unknown",)}, "unsupported pick"),
        ({"place_target": "999_unknown"}, "unsupported place"),
        ({"tolerance": float("nan")}, "finite"),
    ):
        with pytest.raises(EvaluationContractError, match=message):
            _protocol(**overrides)


def test_action_validation_rejects_wrong_shape_non_numeric_and_non_finite() -> None:
    assert validate_action_vector(range(9)) == tuple(float(value) for value in range(9))
    with pytest.raises(EvaluationContractError, match="shape"):
        validate_action_vector(range(8))
    with pytest.raises(EvaluationContractError, match="finite"):
        validate_action_vector([0.0] * 8 + [float("nan")])
    with pytest.raises(EvaluationContractError, match="finite"):
        validate_action_vector([0.0] * 8 + ["joint"])


def test_policy_action_normalization_only_removes_one_singleton_batch_axis() -> None:
    flat = np.arange(9, dtype=np.float32)
    batched = flat[np.newaxis, :]

    assert normalize_policy_action(flat) == tuple(float(value) for value in flat)
    assert normalize_policy_action(batched) == tuple(float(value) for value in flat)

    for wrong_shape in (np.zeros((2, 9)), np.zeros((3, 3))):
        with pytest.raises(EvaluationContractError, match="policy action shape"):
            normalize_policy_action(wrong_shape)
    with pytest.raises(EvaluationContractError, match="finite"):
        normalize_policy_action(np.asarray([[0.0] * 8 + [float("nan")]]))


def test_dataset_audit_checks_the_course_feature_contract(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    meta = root / "meta"
    meta.mkdir(parents=True)
    info = {
        "codebase_version": "v3.0",
        "fps": 5,
        "robot_type": "franka",
        "total_episodes": 2,
        "total_frames": 20,
        "features": {
            "observation.state": {"dtype": "float32", "shape": [9]},
            "action": {"dtype": "float32", "shape": [9]},
            "observation.images.world": {"dtype": "video", "shape": [120, 160, 3]},
            "observation.images.wrist": {"dtype": "video", "shape": [120, 160, 3]},
        },
    }
    (meta / "info.json").write_text(json.dumps(info), encoding="utf-8")
    (meta / "tasks.parquet").write_bytes(b"tasks")

    evidence = audit_dataset_contract(root, repo_id="local/example")
    assert evidence["fps"] == 5.0
    assert evidence["action_shape"] == [9]
    assert evidence["domain_provenance"] is None

    info["features"]["action"]["shape"] = [7]
    (meta / "info.json").write_text(json.dumps(info), encoding="utf-8")
    with pytest.raises(EvaluationContractError, match="action"):
        audit_dataset_contract(root, repo_id="local/example")


def test_summary_and_versioned_report_are_recomputed_from_episode_rows() -> None:
    rows = _rows()
    summary = summarize_episode_rows(rows)
    assert summary["successes"] == 2
    assert summary["termination_counts"] == {
        "success": 2,
        "timeout": 1,
        "diverged": 0,
        "invalid_action": 0,
    }

    protocol = _protocol(episodes=3)
    condition = build_condition_spec(name="reference", declared_label="reference")
    report = build_evaluation_report(
        generated_at="2026-10-08T12:00:00+08:00",
        environment={"python": "3.12"},
        dataset={"repo_id": "local/example"},
        checkpoint={"path": "/tmp/checkpoint"},
        protocol=protocol,
        condition=condition,
        episode_rows=rows,
        outputs={"results": "/tmp/results.json"},
        limitations=["small sample"],
    )
    assert report["schema_version"] == 1
    assert report["summary"]["wilson_95"][0] < report["summary"]["success_rate"]
    assert validate_evaluation_report(report) == report

    report["summary"]["successes"] = 3
    with pytest.raises(EvaluationContractError, match="summary"):
        validate_evaluation_report(report)


def test_paired_rows_require_identical_seeds_and_preserve_flips() -> None:
    reference = _rows((True, False, True))
    held_out = _rows((False, False, True))
    changes = paired_outcome_changes(reference, held_out)
    assert [row["change"] for row in changes] == [
        "success-to-failure",
        "unchanged-failure",
        "unchanged-success",
    ]

    held_out[0]["seed"] = 9999
    with pytest.raises(EvaluationContractError, match="identical seeds"):
        paired_outcome_changes(reference, held_out)


def test_device_and_output_preflight_fail_before_expensive_work(tmp_path: Path) -> None:
    with pytest.raises(EvaluationContractError, match="requested"):
        require_requested_device("cuda", cuda_available=False)
    require_requested_device("cpu", cuda_available=False)

    outputs = tmp_path / "outputs"
    safe = outputs / "l13" / "reference"
    assert validate_output_root(safe, allowed_root=outputs) == safe.resolve()
    with pytest.raises(EvaluationContractError, match="child"):
        validate_output_root(outputs, allowed_root=outputs)

    result = safe / "results.json"
    result.parent.mkdir(parents=True)
    result.write_text("{}", encoding="utf-8")
    with pytest.raises(EvaluationContractError, match="already exists"):
        validate_output_targets(results_path=result, video_dir=None, save_video=False)
