import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RECORDER_PATH = PROJECT_ROOT / "src" / "robo_genesis" / "record_dataset.py"


def _recorder_source() -> str:
    return RECORDER_PATH.read_text(encoding="utf-8")


def test_recorder_validates_before_destructive_or_runtime_work() -> None:
    source = _recorder_source()
    ast.parse(source, filename=str(RECORDER_PATH))

    validation = source.index("normalized_config = validate_dr_collection_config(")
    overwrite = source.index("shutil.rmtree(root)")
    genesis_init = source.index("gs.init(backend=backend)")

    assert validation < overwrite < genesis_init


def test_recorder_writes_dr_sidecar_after_finalize_and_fails_incomplete_runs() -> None:
    source = _recorder_source()

    finalize = source.index("dataset.finalize()")
    dr_guard = source.index("if args.dr_appearance or args.dr_runtime:", finalize)
    sidecar_write = source.index("write_domain_provenance(root, provenance)", dr_guard)
    incomplete_guard = source.index("if n_success != args.episodes:", sidecar_write)

    assert finalize < dr_guard < sidecar_write < incomplete_guard
    assert "raise SystemExit(" in source[incomplete_guard:]
    assert '"committed_debug_failures": n_failed_saved' in source
    assert '"world_camera_pose": randomizer.last_world_camera_pose' in source
