import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_POLICY = PROJECT_ROOT / "src" / "robo_genesis" / "eval_policy.py"
EVAL_SWEEP = PROJECT_ROOT / "src" / "robo_genesis" / "eval_sweep.py"


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    return next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name
    )


def test_eval_policy_checks_protocol_before_genesis_initialization() -> None:
    source = EVAL_POLICY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    main = _function(tree, "main")

    calls = [
        node
        for node in ast.walk(main)
        if isinstance(node, ast.Call)
    ]

    def call_name(node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            return f"{node.func.value.id}.{node.func.attr}"
        return ""

    names_by_line = [(node.lineno, call_name(node)) for node in calls]
    genesis_init_line = min(line for line, name in names_by_line if name == "gs.init")
    for required in (
        "audit_dataset_contract",
        "_checkpoint_evidence",
        "require_requested_device",
        "validate_evaluation_protocol",
        "validate_output_targets",
    ):
        assert min(line for line, name in names_by_line if name == required) < genesis_init_line


def test_run_episode_has_no_timeout_single_frame_success_bypass() -> None:
    source = EVAL_POLICY.read_text(encoding="utf-8")
    tree = ast.parse(source)
    run_episode = _function(tree, "run_episode")
    segment = ast.get_source_segment(source, run_episode)

    assert segment is not None
    assert "DwellTracker" in segment
    assert "dwell_frame_count" in segment
    assert "if not result.success" not in segment
    assert segment.count("check_success(") == 1
    assert 'termination_reason = "invalid_action"' in segment


def test_eval_policy_records_versioned_report_and_termination_reasons() -> None:
    source = EVAL_POLICY.read_text(encoding="utf-8")

    assert "build_evaluation_report(" in source
    assert '"termination_reason": "diverged"' in source
    assert 'result.termination_reason' in source
    assert "validate_action_vector(raw_action)" in source
    assert "audit_checkpoint(policy_path" in source
    assert "auto-falls back if unavailable" not in source


def test_single_checkpoint_condition_interface_stays_focused() -> None:
    source = EVAL_POLICY.read_text(encoding="utf-8")

    assert "def _condition_config(" in source
    assert 'choices=("friction_ratio", "mass_ratio")' in source
    assert 'protocol=protocol' in source
    assert "A five-episode run" not in source
    for unsupported_option in (
        "--log-out",
        "--dr-appearance",
        "--dr-runtime",
        "--dr-friction",
        "--dr-mass",
        "--dr-cam-pos",
        "--dr-cam-lookat",
    ):
        assert unsupported_option not in source


def test_sweep_labels_pooled_counts_accurately() -> None:
    source = EVAL_SWEEP.read_text(encoding="utf-8")

    assert "aggregate (pooled over domains)" in source
    assert "summary (pooled over domains)" in source
    assert "aggregate (mean over domains)" not in source
    assert "isolates the effect of training progress" not in source
