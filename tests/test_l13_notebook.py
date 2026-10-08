import ast
import json
import os
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_NAME = "l13-closed-loop-evaluation-and-capstone.ipynb"


def _load_notebook(locale: str) -> dict:
    path = PROJECT_ROOT / "notebooks" / locale / NOTEBOOK_NAME
    return json.loads(path.read_text(encoding="utf-8"))


def test_l13_notebooks_expose_the_closed_loop_evaluation_contract() -> None:
    expected_code_ids = (
        "l13-setup",
        "l13-input-audit",
        "l13-protocol",
        "l13-condition-plan",
        "l13-reference-rollout",
        "l13-rollout-evidence",
        "l13-result-audit",
        "l13-condition-comparison",
        "l13-checkpoint-sweep",
        "l13-capstone-report",
        "l13-final-check",
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
        "code",
        "markdown",
        "code",
        "markdown",
        "code",
    )
    required_code = (
        "lesson.status.value == 'planned'",
        "RG101_L13_RUN_EVAL",
        "RG101_L13_RUN_CAPSTONE",
        "RG101_L13_RUN_SWEEP",
        "ROBO_GENESIS_RENDER",
        "RG101_L13_DATASET_ROOT",
        "RG101_L13_CHECKPOINT",
        "RG101_L13_OUTPUT_ROOT",
        "validate_output_root(",
        "audit_dataset_contract(",
        "audit_checkpoint(",
        "No download or fallback checkpoint is attempted",
        "validate_evaluation_protocol(",
        "evaluate_predicate_trace(",
        "SYNTHETIC_PREDICATE_TRACE",
        "classify_condition(",
        "subprocess.run(",
        "capture_output=True",
        "robo_genesis.eval_policy",
        "--save-video",
        "validate_evaluation_report(",
        "reference_data['outputs']['log']",
        "cv2.VideoCapture",
        "expected H.264 video",
        "summarize_episode_rows(",
        "MANUAL_FAILURE_LABELS",
        "paired_outcome_changes(",
        "no significance claim is made",
        "robo_genesis.eval_sweep",
        "sweep_budget = len(sweep_checkpoints) * EPISODES",
        "robo-genesis-l13-capstone-report",
        "Core closed-loop evaluation: NOT COMPLETED",
        "Capstone: NOT COMPLETED",
    )
    forbidden_code = (
        "sys.path.append",
        "sys.path.insert",
        "gs.init",
        "load_policy(",
        "build_scene(",
        "requests.get",
        "snapshot_download",
        "--dr-domains",
        "--dr-runtime",
        "--dr-friction",
        "--dr-mass",
        "--log-out",
        "aggregate (mean over domains)",
    )
    localized_code: dict[str, tuple[str, ...]] = {}

    for locale in ("en", "zh"):
        notebook = _load_notebook(locale)
        cells = notebook["cells"]
        code_cells = [cell for cell in cells if cell["cell_type"] == "code"]
        code_sources = tuple("".join(cell["source"]) for cell in code_cells)
        code_source = "\n".join(code_sources)
        localized_code[locale] = code_sources

        assert len(cells) == 23
        assert len(code_cells) == 11
        assert tuple(cell["cell_type"] for cell in cells) == expected_cell_types
        assert tuple(cell["id"] for cell in code_cells) == expected_code_ids
        assert notebook["metadata"]["robo_genesis"] == {
            "lesson": "L13",
            "slug": "closed-loop-evaluation-and-capstone",
            "locale": locale,
            "duration_minutes": 120,
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
        assert "23 cells" not in markdown_source
        assert "11 code cells" not in markdown_source
        assert "Module 07" not in markdown_source

    assert localized_code["en"] == localized_code["zh"]


def test_l13_notebook_default_diagnostic_path_starts_no_subprocess(
    monkeypatch, capsys
) -> None:
    for name in tuple(os.environ):
        if name.startswith("RG101_L13_") or name == "ROBO_GENESIS_RENDER":
            monkeypatch.delenv(name, raising=False)

    namespace: dict[str, object] = {}
    notebook = _load_notebook("en")
    with patch("subprocess.run", side_effect=AssertionError("subprocess must remain idle")):
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                source = "".join(cell["source"])
                exec(compile(source, f"notebook:{cell['id']}", "exec"), namespace)

    output = capsys.readouterr().out
    assert "Diagnostic/preflight: COMPLETED" in output
    assert "Core closed-loop evaluation: NOT COMPLETED" in output
    assert "Capstone: NOT COMPLETED" in output
    assert namespace["reference_report"] is None
    assert namespace["held_out_report"] is None
    assert namespace["sweep_status"] == "NOT RUN"


def test_l13_exercises_and_reports_keep_evidence_boundaries_visible() -> None:
    notebook = _load_notebook("en")
    cells = {cell["id"]: "".join(cell["source"]) for cell in notebook["cells"]}

    assert "predict the result" in cells["l13-protocol-intro"]
    assert "Change no second factor" in cells["l13-condition-intro"]
    assert "visible in that episode's video" in cells["l13-statistics-intro"]
    assert "what this run supports" in cells["l13-capstone-intro"]
    assert "if run_eval:" in cells["l13-reference-rollout"]
    assert "if run_capstone:" in cells["l13-condition-comparison"]
    assert "if run_sweep:" in cells["l13-checkpoint-sweep"]
    assert "reference_report['summary']['successes']" in cells["l13-capstone-report"]
    assert "SUPPORTED_CLAIM = os.environ.get" in cells["l13-capstone-report"]
    assert "success_rate =" not in cells["l13-capstone-report"]
