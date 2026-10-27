from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from robo_genesis.l14_workflow import (
    AGGREGATE_EVIDENCE_MODE,
    L14ContractError,
    archive_changed_files,
    audit_hf_checkpoint,
    build_aggregate_evidence_card,
    build_single_task_eval_command,
    l14_output_paths,
    parse_final_success_rate,
    parse_last_progress_rate,
    require_fresh_paths,
    run_command_logged,
    snapshot_files,
    validate_l14_config,
    write_json_artifact,
)


def _config(tmp_path: Path) -> dict[str, object]:
    return {
        "run_name": "l14-review",
        "robotwin_root": "/RoboTwin",
        "runtime_root": str(tmp_path),
        "python": "/opt/robotwin-env/bin/python",
        "task_name": "adjust_bottle",
        "task_config": "demo_clean",
        "core_gpu_count": 4,
        "competition_gpu_count": 8,
        "lora_steps": 100,
        "eval_episodes": 10,
        "training_seed": 42,
    }


def test_l14_config_and_output_paths_keep_conditions_isolated(tmp_path: Path) -> None:
    config = validate_l14_config(_config(tmp_path))
    paths = l14_output_paths(config)

    assert config["core_gpu_count"] == 4
    assert paths["run_root"] == (
        tmp_path.resolve() / "outputs/robo_genesis_l14/l14-review"
    )
    assert paths["base_eval_log"] != paths["merged_eval_log"]
    assert paths["lora_output"] != paths["full_sft_output"]


def test_l14_rejects_non_course_core_profile(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config["core_gpu_count"] = 8
    with pytest.raises(L14ContractError, match="exactly 4 GPUs"):
        validate_l14_config(config)


def test_l14_fresh_path_gate_rejects_collision(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="fresh run_name"):
        require_fresh_paths([tmp_path / "missing", existing])


def test_l14_eval_command_uses_unmodified_companion_interface() -> None:
    command = build_single_task_eval_command(
        python="/opt/robotwin-env/bin/python",
        robotwin_root="/RoboTwin",
        task_name="adjust_bottle",
        task_config="demo_clean",
        episodes=10,
        video=True,
        seed_start=100000,
    )

    assert command[:2] == (
        "/opt/robotwin-env/bin/python",
        "/RoboTwin/scripts/eval_policy_xpolicylab.py",
    )
    assert command[command.index("--test_num") + 1] == "10"
    assert command[command.index("--expert_check") + 1] == "true"
    assert command[command.index("--accept_expert_info_on_failure") + 1] == "true"
    assert command[command.index("--seed_start") + 1] == "100000"
    assert command[command.index("--eval_batch") + 1] == "false"
    assert "--num_workers" not in command
    assert "--max_seed_attempts" not in command
    assert command[command.index("--additional_info") + 1] == "eval_video_log=true"
    assert "--episode_info_output" not in command


def test_l14_aggregate_card_does_not_invent_seed_matching(tmp_path: Path) -> None:
    base = parse_final_success_rate(
        "noise\nFinal success rate: 2/10 = 20.0%\n",
        condition="base",
        log_path=tmp_path / "base.log",
    )
    merged = parse_final_success_rate(
        "Final batch success rate: 4/10 = 40.0%\n",
        condition="merged_lora",
        log_path=tmp_path / "merged.log",
    )
    card = build_aggregate_evidence_card(
        base,
        merged,
        identities={"run_name": "l14-review"},
        video_artifacts={
            "base": [tmp_path / "videos/base/episode.mp4"],
            "merged_lora": [tmp_path / "videos/merged/episode.mp4"],
        },
    )

    assert base.rate == 0.2
    assert merged.rate == 0.4
    assert base.wilson_low < base.rate < base.wilson_high
    assert card["evidence_mode"] == AGGREGATE_EVIDENCE_MODE
    assert card["observed_rate_difference"] == pytest.approx(0.2)
    assert card["resolved_seed_matching_available"] is False
    assert card["matched_outcomes"] is None
    assert card["identities"] == {"run_name": "l14-review"}
    assert card["video_artifacts"]["base"] == [
        str(tmp_path / "videos/base/episode.mp4")
    ]
    assert "independent small-run observations" in card["conclusion_boundary"]


def test_l14_aggregate_parser_rejects_missing_or_invalid_result() -> None:
    with pytest.raises(L14ContractError, match="no Final success rate"):
        parse_final_success_rate("Success rate: 1/2", condition="base")
    with pytest.raises(L14ContractError, match="invalid aggregate"):
        parse_final_success_rate(
            "Final success rate: 11/10 = 110.0%", condition="base"
        )


def test_l14_serial_progress_parser_uses_actual_completed_denominator() -> None:
    text = (
        "Success rate: \x1b[96m0/1\x1b[0m => 0.0%\n"
        "Success rate: \x1b[96m1/5\x1b[0m => 20.0%\n"
        "Final success rate: 1/10 = 10.0%\n"
    )

    assert parse_last_progress_rate(text) == (1, 5)
    assert parse_last_progress_rate("Final success rate: 0/10 = 0.0%\n") is None


def test_l14_json_artifact_is_fresh_and_readable(tmp_path: Path) -> None:
    path = tmp_path / "evidence/card.json"
    write_json_artifact(path, {"evidence_mode": AGGREGATE_EVIDENCE_MODE})
    assert json.loads(path.read_text()) == {
        "evidence_mode": AGGREGATE_EVIDENCE_MODE
    }
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_json_artifact(path, {"evidence_mode": "changed"})


def test_l14_checkpoint_audit_and_logged_command(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text("{}")
    (checkpoint / "tokenizer_config.json").write_text("{}")
    (checkpoint / "model-00001-of-00001.safetensors").write_bytes(b"weights")
    (checkpoint / "model.safetensors.index.json").write_text(
        json.dumps(
            {
                "weight_map": {
                    "policy.weight": "model-00001-of-00001.safetensors"
                }
            }
        )
    )

    audit = audit_hf_checkpoint(checkpoint)
    assert audit["shards"] == ["model-00001-of-00001.safetensors"]
    assert audit["processor_files"] == ["tokenizer_config.json"]

    log_path = tmp_path / "logs/command.log"
    text = run_command_logged(
        [sys.executable, "-c", "print('Final success rate: 1/2 = 50.0%')"],
        cwd=tmp_path,
        env=None,
        log_path=log_path,
    )
    assert text == "Final success rate: 1/2 = 50.0%\n"
    assert log_path.read_text() == text


def test_l14_archives_only_files_changed_by_one_evaluation(tmp_path: Path) -> None:
    eval_root = tmp_path / "eval_result"
    old_video = eval_root / "adjust_bottle/old.mp4"
    old_video.parent.mkdir(parents=True)
    old_video.write_bytes(b"old")
    before = snapshot_files(eval_root)

    old_video.write_bytes(b"replaced")
    new_video = eval_root / "adjust_bottle/new.mp4"
    new_video.write_bytes(b"new")
    (eval_root / "adjust_bottle/notes.txt").write_text("not a video")

    archived = archive_changed_files(eval_root, before, tmp_path / "archive")
    assert archived == [
        str(tmp_path / "archive/adjust_bottle/new.mp4"),
        str(tmp_path / "archive/adjust_bottle/old.mp4"),
    ]
    assert (tmp_path / "archive/adjust_bottle/new.mp4").read_bytes() == b"new"
    assert (tmp_path / "archive/adjust_bottle/old.mp4").read_bytes() == b"replaced"


def test_l14_per_invocation_archives_preserve_reused_video_names(
    tmp_path: Path,
) -> None:
    eval_root = tmp_path / "eval_result"
    episode = eval_root / "adjust_bottle/episode0.mp4"
    episode.parent.mkdir(parents=True)

    before_first = snapshot_files(eval_root)
    episode.write_bytes(b"first invocation")
    first = archive_changed_files(
        eval_root, before_first, tmp_path / "videos/attempt_00"
    )

    before_second = snapshot_files(eval_root)
    episode.write_bytes(b"second invocation")
    second = archive_changed_files(
        eval_root, before_second, tmp_path / "videos/attempt_01"
    )

    assert Path(first[0]).read_bytes() == b"first invocation"
    assert Path(second[0]).read_bytes() == b"second invocation"
