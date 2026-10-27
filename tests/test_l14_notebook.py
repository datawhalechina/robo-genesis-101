from __future__ import annotations

import ast
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_NAME = "l14-robotwin-lingbot-vla-fine-tuning.ipynb"


def _load_notebook(locale: str) -> dict:
    path = PROJECT_ROOT / "notebooks" / locale / NOTEBOOK_NAME
    return json.loads(path.read_text(encoding="utf-8"))


def test_l14_notebooks_preserve_the_companion_coverage_without_fake_matching() -> None:
    expected_ids = (
        "l14-overview",
        "l14-config",
        "l14-environment-and-data-check",
        "l14-preflight",
        "l14-base-server",
        "l14-base-server-run",
        "l14-base-evaluation-protocol",
        "l14-base-evaluation-role",
        "l14-base-evaluation-run",
        "l14-official-checkpoint-extension",
        "l14-official-checkpoint-run",
        "l14-official-benchmark-extension",
        "l14-official-benchmark-run",
        "l14-robotwin-benchmark-extension",
        "l14-robotwin-benchmark-run",
        "l14-lora-workflow",
        "l14-lora-training",
        "l14-lora-train",
        "l14-lora-merge",
        "l14-lora-merge-run",
        "l14-merged-server",
        "l14-merged-server-run",
        "l14-merged-evaluation",
        "l14-merged-evaluation-run",
        "l14-lora-benchmark-extension",
        "l14-lora-benchmark-run",
        "l14-lora-evidence-and-cleanup",
        "l14-lora-evidence-and-cleanup-run",
        "l14-full-sft-workflow",
        "l14-full-sft-storage-audit",
        "l14-full-sft-training",
        "l14-full-sft-train",
        "l14-full-sft-capacity-reference",
        "l14-full-sft-conversion",
        "l14-full-sft-convert",
        "l14-full-sft-server",
        "l14-full-sft-server-run",
        "l14-full-sft-evaluation",
        "l14-full-sft-evaluation-run",
        "l14-full-sft-benchmark",
        "l14-full-sft-benchmark-run",
        "l14-full-sft-cleanup",
        "l14-full-sft-cleanup-run",
    )
    expected_types = (
        "markdown", "code", "markdown", "code", "markdown", "code",
        "markdown", "markdown", "code", "markdown", "code", "markdown",
        "code", "markdown", "code", "markdown", "markdown", "code",
        "markdown", "code", "markdown", "code", "markdown", "code",
        "markdown", "code", "markdown", "code", "markdown", "code",
        "markdown", "code", "markdown", "markdown", "code", "markdown",
        "code", "markdown", "code", "markdown", "code", "markdown", "code",
    )
    expected_code_ids = tuple(
        cell_id
        for cell_id, cell_type in zip(expected_ids, expected_types, strict=True)
        if cell_type == "code"
    )
    required_code = (
        "CONFIG = validate_l14_config({",
        "'core_gpu_count': 4",
        "'competition_gpu_count': 8",
        "'lora_steps': 100",
        "'training_seed': 42",
        "COMPANION_COMMIT",
        "ROBOTWIN_COMMIT",
        "AMD Radeon PRO W7900",
        "'/opt/aiter'",
        "len(dataset_entries) == 50",
        "meta/info.json",
        "configs/robot_configs/robotwin.yaml",
        "'camera_top': 'observation.images.cam_high'",
        "raw_feature_shapes == {'observation.state': 14, 'action': 14}",
        "'observation.state.arm.position': 12",
        "'action.effector.position': 2",
        "'arm.position': 14",
        "training_config['train']['max_action_dim'] == 55",
        "set(mapped_targets).issubset(norm_stats['norm_stats'])",
        "len(norm_stats['norm_stats'][target_key][stat_name]) == width",
        "lora_scope'] == 'action_expert'",
        "lora_rank'] == 8",
        "lora_alpha'] == 16",
        "build_single_task_eval_command(",
        "collect_serial_episodes",
        "parse_last_progress_rate",
        "batch=False, seed_start=seed_start",
        "attempts_json",
        "video_root / f'attempt_{attempt_index:02d}'",
        "'video_artifacts': attempt_video_artifacts",
        "len(BASE_VIDEO_ARTIFACTS) == CONFIG['eval_episodes']",
        "len(MERGED_VIDEO_ARTIFACTS) == CONFIG['eval_episodes']",
        "EVAL_RESULT_ROOT = ROBOTWIN / 'eval_result'",
        "snapshot_files(EVAL_RESULT_ROOT)",
        "archive_changed_files(",
        "EVAL_VIDEO_LOG = True",
        "RUN_OFFICIAL_ROBOTWIN_CHECKPOINT = False",
        "RUN_OFFICIAL_FULL_BENCHMARK = False",
        "RUN_ROBOTWIN_FULL_BENCHMARK = False",
        "BENCHMARK_RESUME = False",
        "benchmark_command.append('--resume')",
        "GPU_COUNT = CONFIG['core_gpu_count']",
        "--train.data_parallel_shard_size",
        "--train.micro_batch_size",
        "--train.gradient_accumulation_steps",
        "--train.global_batch_size",
        "--train.seed",
        "merge_lora_dcp.py",
        "audit_hf_checkpoint(MERGED)",
        "RUN_LORA_FULL_BENCHMARK = False",
        "build_aggregate_evidence_card(",
        "'base': BASE_VIDEO_ARTIFACTS",
        "'merged_lora': MERGED_VIDEO_ARTIFACTS",
        "matched outcomes are unavailable",
        "RUN_FULL_SFT = False",
        "FULL_SFT_TEACHER_MODE = 'full'",
        "FULL_SFT_GLOBAL_BATCH_SIZE = 256",
        "FULL_SFT_MICRO_BATCH_SIZE = 16",
        "FULL_SFT_ENABLE_FULL_SHARD = True",
        "train_full_sft.sh",
        "convert_full_sft_dcp.py",
        "RUN_FULL_SFT_FULL_BENCHMARK = False",
        "resolved_seed_matching_available",
    )
    forbidden_code = (
        "--episode_info_output",
        "matched_outcome_changes",
        "failure-to-success",
        "success-to-failure",
        "sys.path.append",
        "sys.path.insert",
        "shutil.rmtree",
        "DELETE_PREVIOUS_LORA_OUTPUTS = True",
        "RUN_ALL",
        "global_run_mode",
    )
    localized_code: dict[str, tuple[str, ...]] = {}

    for locale in ("en", "zh"):
        notebook = _load_notebook(locale)
        cells = notebook["cells"]
        code_cells = [cell for cell in cells if cell["cell_type"] == "code"]
        code_sources = tuple("".join(cell["source"]) for cell in code_cells)
        code_source = "\n".join(code_sources)
        localized_code[locale] = code_sources

        assert len(cells) == 43
        assert len(code_cells) == 20
        assert tuple(cell["cell_type"] for cell in cells) == expected_types
        assert tuple(cell["id"] for cell in cells) == expected_ids
        assert tuple(cell["id"] for cell in code_cells) == expected_code_ids
        assert notebook["metadata"]["robo_genesis"] == {
            "lesson": "L14",
            "slug": "robotwin-lingbot-vla-fine-tuning",
            "locale": locale,
            "duration_minutes": 180,
            "hardware": "gpu-required",
            "status": "planned",
        }
        assert all(cell["execution_count"] is None for cell in code_cells)
        assert all(cell["outputs"] == [] for cell in code_cells)
        assert all(fragment in code_source for fragment in required_code)
        assert all(fragment not in code_source for fragment in forbidden_code)
        for cell in code_cells:
            ast.parse("".join(cell["source"]), filename=f"{locale}:{cell['id']}")

        markdown_source = "\n".join(
            "".join(cell["source"])
            for cell in cells
            if cell["cell_type"] == "markdown"
        )
        assert "LoRA" in markdown_source
        assert "full" in markdown_source.lower()
        assert "matched" in markdown_source
        assert (
            "independent aggregate observations" in markdown_source
            or "独立 run 的 aggregate 观测" in markdown_source
        )

    assert localized_code["en"] == localized_code["zh"]
