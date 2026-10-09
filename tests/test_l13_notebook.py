import ast
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

from robo_genesis.evaluation_contract import (
    EvaluationContractError,
    build_condition_spec,
    validate_evaluation_protocol,
)
from robo_genesis.l13_workflow import (
    L13InputAudit,
    L13Workflow,
    audit_l13_inputs,
    build_l13_capstone_guidance,
    build_l13_evaluation_command,
    evaluator_environment_overrides,
    require_l13_inputs,
    resolve_checkpoint_source,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_NAME = "l13-closed-loop-evaluation-and-capstone.ipynb"


def _load_notebook(locale: str) -> dict:
    path = PROJECT_ROOT / "notebooks" / locale / NOTEBOOK_NAME
    return json.loads(path.read_text(encoding="utf-8"))


def _write_dataset_info(root: Path) -> None:
    meta = root / "meta"
    meta.mkdir(parents=True)
    (meta / "info.json").write_text(
        json.dumps(
            {
                "fps": 30,
                "features": {
                    "observation.state": {"shape": [9]},
                    "action": {"shape": [9]},
                    "observation.images.world": {"shape": [360, 640, 3]},
                    "observation.images.wrist": {"shape": [360, 640, 3]},
                },
            }
        ),
        encoding="utf-8",
    )


def test_l13_notebooks_follow_the_lecture_evidence_gates_linearly() -> None:
    expected_code_ids = (
        "l13-configuration",
        "l13-preflight",
        "l13-protocol",
        "l13-condition-plan",
        "l13-reference-rollout",
        "l13-result-audit",
        "l13-condition-comparison",
        "l13-capstone-report",
    )
    expected_cell_types = (
        "markdown",
        "markdown",
        "code",
        "markdown",
        "code",
        "markdown",
        "code",
        "markdown",
        "code",
        "markdown",
        "code",
        "markdown",
        "code",
        "markdown",
        "code",
        "markdown",
        "code",
        "markdown",
    )
    required_code = (
        "CONFIG = {",
        "'checkpoint': None",
        "'dataset_repo_id': 'genesis/fruit_pick'",
        "'dataset_root': 'datasets/fruit_pick'",
        "'run_name': 'fruit-pick-hf-fallback'",
        "'protocol': {",
        "COURSE_DEFAULT_DATASET = {",
        "'repo_id': 'wangxun1010/fruit_pick'",
        "'revision': '475e8c6ec7079c4c52b20a0221bf959acb541abd'",
        "COURSE_DEFAULT_CHECKPOINT = {",
        "'repo_id': 'wangxun1010/smolvla-fruit-pick-0821'",
        "'revision': 'cdf720f162e6ee86dbc856cdf15c5dcd4a673221'",
        "'subfolder': '.'",
        "lesson.status.value == 'gpu-verified'",
        "prepare_l13_workflow(",
        "course_default_dataset=COURSE_DEFAULT_DATASET",
        "audit_l13_inputs(",
        "allow_dataset_download=True",
        "allow_checkpoint_download=False",
        "preflight.ready_for_reference",
        "validate_evaluation_protocol(",
        "evaluate_predicate_trace(",
        "SYNTHETIC_PREDICATE_TRACE",
        "declare_l13_conditions(",
        "require_l13_inputs(",
        "run_l13_condition(",
        "audit_l13_evidence(",
        "MANUAL_FAILURE_LABELS",
        "compare_l13_runs(",
        "no significance claim is made",
        "write_l13_capstone_report(",
        "Core Reference evaluation:",
        "Capstone comparison and report:",
    )
    forbidden_code = (
        "'mode':",
        "RUN_REFERENCE",
        "RUN_HELD_OUT",
        "RG101_L13_",
        "environment_flag(",
        "run_eval",
        "run_capstone",
        "subprocess.run(",
        "snapshot_download(",
        "cv2.VideoCapture",
        "robo_genesis.eval_sweep",
        "sys.path.append",
        "sys.path.insert",
        "gs.init",
        "load_policy(",
        "build_scene(",
    )
    localized_code: dict[str, tuple[str, ...]] = {}

    for locale in ("en", "zh"):
        notebook = _load_notebook(locale)
        cells = notebook["cells"]
        code_cells = [cell for cell in cells if cell["cell_type"] == "code"]
        code_sources = tuple("".join(cell["source"]) for cell in code_cells)
        code_source = "\n".join(code_sources)
        localized_code[locale] = code_sources

        assert len(cells) == 18
        assert len(code_cells) == 8
        assert tuple(cell["cell_type"] for cell in cells) == expected_cell_types
        assert tuple(cell["id"] for cell in code_cells) == expected_code_ids
        assert notebook["metadata"]["robo_genesis"] == {
            "lesson": "L13",
            "slug": "closed-loop-evaluation-and-capstone",
            "locale": locale,
            "duration_minutes": 120,
            "hardware": "gpu-required",
            "status": "gpu-verified",
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
        assert "six evidence gates" in markdown_source or "六道证据门" in markdown_source
        assert (
            "numbered steps from top to bottom" in markdown_source
            or "按照编号步骤从上到下" in markdown_source
        )

    assert localized_code["en"] == localized_code["zh"]
    workflow_source = (PROJECT_ROOT / "src" / "robo_genesis" / "l13_workflow.py").read_text()
    assert "RG101_L13_" not in workflow_source


def test_l13_notebook_preflight_downloads_metadata_but_defers_checkpoint(
    capsys, monkeypatch, tmp_path
) -> None:
    namespace: dict[str, object] = {}
    notebook = _load_notebook("en")
    fake_hub = ModuleType("huggingface_hub")
    snapshot = tmp_path / "dataset-snapshot"
    _write_dataset_info(snapshot)
    calls: list[dict[str, object]] = []

    def fake_snapshot_download(**kwargs) -> str:
        calls.append(kwargs)
        if kwargs.get("repo_type") != "dataset":
            raise AssertionError("checkpoint download must remain deferred")
        return str(snapshot)

    fake_hub.snapshot_download = fake_snapshot_download  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_hub)
    with patch(
        "subprocess.run", side_effect=AssertionError("subprocess must remain idle")
    ):
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                source = "".join(cell["source"])
                exec(compile(source, f"notebook:{cell['id']}", "exec"), namespace)
                if cell["id"] == "l13-condition-plan":
                    break

    output = capsys.readouterr().out
    assert '"checkpoint_origin": "course-default"' in output
    assert '"repo_id": "wangxun1010/smolvla-fruit-pick-0821"' in output
    assert '"revision": "cdf720f162e6ee86dbc856cdf15c5dcd4a673221"' in output
    assert "download is deferred until you run the Reference cell (Step 4)" in output
    assert "Ready to run Step 4: True" in output
    assert "STOP before Step 4" not in output
    assert calls == [
        {
            "repo_id": "wangxun1010/fruit_pick",
            "repo_type": "dataset",
            "revision": "475e8c6ec7079c4c52b20a0221bf959acb541abd",
            "allow_patterns": ["meta/**"],
        }
    ]
    assert namespace["preflight"].dataset_root == snapshot.resolve()
    assert namespace["preflight"].dataset["fps"] == 30.0
    assert any(
        row["input"] == "checkpoint" and row["status"] == "DEFERRED"
        for row in namespace["preflight"].rows
    )
    assert namespace["preflight"].checkpoint is None
    assert namespace["preflight"].checkpoint_root is None
    assert "reference_run" not in namespace
    assert "held_out_run" not in namespace
    assert "capstone_output" not in namespace


def test_l13_pinned_huggingface_checkpoint_resolution_is_explicit(
    monkeypatch, tmp_path
) -> None:
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    calls: list[tuple[str, str]] = []
    fake_hub = ModuleType("huggingface_hub")

    def fake_snapshot_download(*, repo_id: str, revision: str) -> str:
        calls.append((repo_id, revision))
        return str(snapshot)

    fake_hub.snapshot_download = fake_snapshot_download  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_hub)
    source = {
        "repo_id": "wangxun1010/smolvla-fruit-pick-0821",
        "revision": "cdf720f162e6ee86dbc856cdf15c5dcd4a673221",
        "subfolder": ".",
    }
    resolved, evidence = resolve_checkpoint_source(source, allow_download=True)

    assert resolved == snapshot.resolve()
    assert calls == [
        (
            "wangxun1010/smolvla-fruit-pick-0821",
            "cdf720f162e6ee86dbc856cdf15c5dcd4a673221",
        )
    ]
    assert evidence["downloaded"] is True
    assert evidence["revision"] == "cdf720f162e6ee86dbc856cdf15c5dcd4a673221"


def test_l13_local_dataset_precedes_the_huggingface_fallback(
    monkeypatch, tmp_path
) -> None:
    dataset_root = tmp_path / "fruit_pick"
    _write_dataset_info(dataset_root)
    fake_hub = ModuleType("huggingface_hub")

    def unexpected_download(**_kwargs) -> str:
        raise AssertionError("local dataset must take precedence")

    fake_hub.snapshot_download = unexpected_download  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_hub)
    workflow = L13Workflow(
        project_root=PROJECT_ROOT,
        outputs_dir=PROJECT_ROOT / "outputs",
        dataset_root=dataset_root,
        repo_id="genesis/fruit_pick",
        output_root=PROJECT_ROOT / "outputs" / "l13" / "test-run",
        checkpoint_source={
            "repo_id": "wangxun1010/smolvla-fruit-pick-0821",
            "revision": "cdf720f162e6ee86dbc856cdf15c5dcd4a673221",
            "subfolder": ".",
        },
        checkpoint_origin="course-default",
        policy_device="cuda",
        gpu_index=0,
        render_enabled=True,
        dataset_fallback_source={
            "repo_id": "wangxun1010/fruit_pick",
            "revision": "475e8c6ec7079c4c52b20a0221bf959acb541abd",
            "subfolder": ".",
        },
    )

    audit = audit_l13_inputs(
        workflow,
        allow_dataset_download=True,
        allow_checkpoint_download=False,
    )

    assert audit.dataset_root == dataset_root.resolve()
    assert audit.dataset["source"] == {
        "kind": "local",
        "path": str(dataset_root.resolve()),
    }


def test_l13_step_4_rejects_missing_dataset_before_checkpoint_download(
    monkeypatch, tmp_path
) -> None:
    fake_hub = ModuleType("huggingface_hub")

    def unexpected_download(**_kwargs) -> str:
        raise AssertionError("checkpoint download must not start before dataset passes")

    fake_hub.snapshot_download = unexpected_download  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_hub)
    workflow = L13Workflow(
        project_root=PROJECT_ROOT,
        outputs_dir=PROJECT_ROOT / "outputs",
        dataset_root=tmp_path / "missing-dataset",
        repo_id="genesis/fruit_pick",
        output_root=PROJECT_ROOT / "outputs" / "l13" / "test-run",
        checkpoint_source={
            "repo_id": "wangxun1010/smolvla-fruit-pick-0821",
            "revision": "cdf720f162e6ee86dbc856cdf15c5dcd4a673221",
            "subfolder": ".",
        },
        checkpoint_origin="course-default",
        policy_device="cuda",
        gpu_index=0,
        render_enabled=True,
    )

    with pytest.raises(EvaluationContractError, match="Step 4 cannot start.*dataset=FAIL"):
        require_l13_inputs(workflow)


def test_l13_workflow_translates_the_frozen_protocol_into_one_cli_command(
    tmp_path,
) -> None:
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    workflow = L13Workflow(
        project_root=PROJECT_ROOT,
        outputs_dir=PROJECT_ROOT / "outputs",
        dataset_root=tmp_path / "dataset",
        repo_id="example/dataset",
        output_root=PROJECT_ROOT / "outputs" / "l13" / "test-run",
        checkpoint_source=checkpoint,
        checkpoint_origin="explicit",
        policy_device="cuda",
        gpu_index=0,
        render_enabled=True,
    )
    inputs = L13InputAudit(
        rows=(),
        dataset={"fps": 5.0},
        checkpoint={"policy_type": "act"},
        checkpoint_root=checkpoint,
        dataset_root=tmp_path / "dataset",
    )
    protocol = validate_evaluation_protocol(
        episodes=5,
        policy_fps=5.0,
        control_fps=100,
        dwell_seconds=0.4,
        max_seconds=15.0,
        tolerance=0.06,
        pick_objects=("011_banana",),
        place_target="024_bowl",
        available_objects=("011_banana", "024_bowl"),
        base_seed=1000,
        balanced=True,
        condition_name="reference",
        render_enabled=True,
    )
    condition = build_condition_spec(
        name="reference",
        declared_label="reference",
        held_constant=("task", "camera contract", "object schedule", "episode seeds"),
    )
    command = build_l13_evaluation_command(
        workflow, inputs, protocol, condition, workflow.output_root / "reference"
    )

    assert command[:3] == (sys.executable, "-m", "robo_genesis.eval_policy")
    assert command[command.index("--episodes") + 1] == "5"
    assert command[command.index("--seed") + 1] == "1000"
    assert command[command.index("--dataset-root") + 1] == str(tmp_path / "dataset")
    assert "--balanced=true" in command
    assert command.count("--held-constant") == 4
    assert evaluator_environment_overrides(workflow) == {
        "PYOPENGL_PLATFORM": "egl",
        "ROBO_GENESIS_RENDER": "1",
        "TOKENIZERS_PARALLELISM": "false",
        "ROCR_VISIBLE_DEVICES": "0",
        "HIP_VISIBLE_DEVICES": None,
        "CUDA_VISIBLE_DEVICES": None,
    }


def test_l13_exercises_and_reports_match_the_lecture_contract() -> None:
    notebook = _load_notebook("en")
    cells = {cell["id"]: "".join(cell["source"]) for cell in notebook["cells"]}
    code_source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )

    assert "predict its maximum streak" in cells["l13-protocol-intro"]
    assert "change only `CONFIG['held_out']`" in cells["l13-condition-intro"]
    assert "evidence visible in that rollout" in cells["l13-result-intro"]
    assert "what the run supports" in cells["l13-capstone-intro"]
    assert "embed=True" in cells["l13-result-audit"]
    assert "embed=False" not in cells["l13-result-audit"]
    assert "reference_inputs = require_l13_inputs(workflow)" in cells["l13-reference-rollout"]
    assert "reference_run = run_l13_condition(" in cells["l13-reference-rollout"]
    assert "held_out_run = run_l13_condition(" in cells["l13-condition-comparison"]
    assert "python -m robo_genesis.eval_sweep" in cells["l13-optional-extension"]
    assert "build_l13_capstone_guidance(" in cells["l13-capstone-report"]
    assert "EVIDENCE CARD" in cells["l13-capstone-report"]
    assert "SENTENCE STEMS" in cells["l13-capstone-report"]
    assert "CAPSTONE_CONCLUSION = {" in cells["l13-capstone-report"]
    assert "capstone_statements(CAPSTONE_CONCLUSION)" in cells["l13-capstone-report"]
    assert "ACTION REQUIRED" in cells["l13-capstone-report"]
    assert "CONFIG['capstone']" not in code_source
    assert "success_rate =" not in cells["l13-capstone-report"]


def test_l13_capstone_guidance_scopes_equal_small_sample_results() -> None:
    reference_summary = {
        "successes": 5,
        "episodes": 5,
        "wilson_95": [0.5655, 1.0],
    }
    held_out_summary = {
        "successes": 5,
        "episodes": 5,
        "wilson_95": [0.5655, 1.0],
    }
    held_out_condition = {
        "name": "camera_yaw_shift",
        "label": "shifted",
        "changed_factor": "camera_yaw_deg",
        "evaluation_range": [10.0, 10.0],
    }
    paired_changes = [
        {"seed": seed, "change": "unchanged-success"} for seed in range(1000, 1005)
    ]

    guidance = build_l13_capstone_guidance(
        reference_summary,
        held_out_summary,
        held_out_condition,
        paired_changes,
    )

    assert guidance["evidence_card"]["reference"]["successes"] == 5
    assert guidance["evidence_card"]["held_out"]["successes"] == 5
    assert guidance["evidence_card"]["scope"]["matched_seeds"] == 5
    assert guidance["evidence_card"]["matched_outcome_changes"] == {
        "unchanged-success": 5
    }
    stems = guidance["sentence_stems"]
    assert "Reference achieved 5/5" in stems["supported_claim_stem"]
    assert "camera_yaw_shift achieved 5/5" in stems["supported_claim_stem"]
    assert "do not establish condition equivalence" in stems["unsupported_claim_stem"]
    assert "at least 50 predeclared seeds" in stems["next_evidence_stem"]
