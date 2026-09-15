import ast
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_NAME = "l11-domain-randomization.ipynb"


def _load_notebook(locale: str) -> dict:
    path = PROJECT_ROOT / "notebooks" / locale / NOTEBOOK_NAME
    return json.loads(path.read_text(encoding="utf-8"))


def test_l11_notebooks_expose_the_domain_randomization_contract() -> None:
    expected_code_ids = (
        "l11-setup",
        "l11-randomization-contract",
        "l11-appearance-preview",
        "l11-appearance-evidence",
        "l11-physics-guardrails",
        "l11-record-randomized-data",
        "l11-distribution-audit",
        "l11-provenance-and-split",
        "l11-final-check",
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
    )
    required_code = (
        "os.environ.get('ROBO_GENESIS_RENDER', '1')",
        "RG101_L11_OVERWRITE",
        "dataset_root.name != 'l11_banana_dr'",
        "preview_root.name != 'l11_dr_preview'",
        "No download or fallback dataset is attempted",
        "lesson.status.value == 'planned'",
        "validate_dr_collection_config(",
        "plan_seed_schedule(",
        "[False, True, True, True, True]",
        "'appearance_domain_index'",
        "robo_genesis.tools.dr_preview",
        "PREVIEW_PROFILE = 'combined'",
        "'table_color'",
        "'object_color'",
        "'fov'",
        "preview_run_root",
        "--seeds",
        "world_baseline.png",
        "sampled_observation_changed",
        "object_only_can_be_masked",
        "mass_references_pristine_base",
        "robo_genesis.record_dataset",
        "IMG_WH = (640, 360)",
        "TARGET_EPISODES = 4",
        "DR_REBUILD_EVERY = 2",
        "('5', '640', '360', 'h264')",
        "--episodes",
        "--max-attempts",
        "--vcodec",
        "h264",
        "--dr-appearance",
        "--dr-runtime",
        "LeRobotDatasetMetadata",
        "video_backend='pyav'",
        "load_domain_provenance(dataset_root)",
        "committed_episode_records(provenance)",
        "mode='held_out_domain'",
        "in_distribution_domains_shared",
        "held_out_domains_disjoint",
        "split_modes_are_distinct",
        "L11 CHECK: PASSED",
        "L11 DIAGNOSTIC CHECK: PASSED",
        "Core domain-randomization experiment: NOT COMPLETED",
        "Training: NOT RUN",
        "Sim-to-real improvement: NOT MEASURED",
    )
    forbidden_code = (
        "sys.path.append",
        "sys.path.insert",
        "PYOPENGL_PLATFORM",
        "libx264",
        "lerobot_train",
        "eval_policy",
        "from transformers",
    )
    localized_code: dict[str, tuple[str, ...]] = {}

    for locale in ("en", "zh"):
        notebook = _load_notebook(locale)
        cells = notebook["cells"]
        code_cells = [cell for cell in cells if cell["cell_type"] == "code"]
        code_sources = tuple("".join(cell["source"]) for cell in code_cells)
        code_source = "\n".join(code_sources)
        localized_code[locale] = code_sources

        assert len(cells) == 20
        assert tuple(cell["cell_type"] for cell in cells) == expected_cell_types
        assert tuple(cell["id"] for cell in code_cells) == expected_code_ids
        assert notebook["metadata"]["robo_genesis"] == {
            "lesson": "L11",
            "slug": "domain-randomization",
            "locale": locale,
            "duration_minutes": 90,
            "hardware": "gpu-recommended",
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
        assert "20 cells" not in markdown_source
        assert "9 code cells" not in markdown_source
        assert "Module 05" not in markdown_source
        assert "M4" not in markdown_source
        assert "IMG_WH = (160, 120)" not in code_source

    assert localized_code["en"] == localized_code["zh"]


def test_l11_notebook_keeps_runtime_work_out_of_diagnostic_branches() -> None:
    notebook = _load_notebook("en")
    code_cells = {cell["id"]: "".join(cell["source"]) for cell in notebook["cells"]}

    assert "if render_enabled:" in code_cells["l11-appearance-preview"]
    assert "if render_enabled:" in code_cells["l11-record-randomized-data"]
    assert "if render_enabled:" in code_cells["l11-distribution-audit"]
    assert "if render_enabled:" in code_cells["l11-provenance-and-split"]
    assert "subprocess.run(preview_command" in code_cells["l11-appearance-preview"]
    assert "subprocess.run(record_command" in code_cells["l11-record-randomized-data"]
    assert "SKIP — recorder subprocess was not started" in code_cells[
        "l11-record-randomized-data"
    ]
    assert "'diagnostic_mode_requested': not render_enabled" not in code_cells[
        "l11-appearance-preview"
    ]
    assert "preview_checks['diagnostic_mode_requested'] = True" in code_cells[
        "l11-appearance-preview"
    ]
    assert "'diagnostic_mode_requested': not render_enabled" not in code_cells[
        "l11-record-randomized-data"
    ]
    assert "record_checks['diagnostic_mode_requested'] = True" in code_cells[
        "l11-record-randomized-data"
    ]


def test_l11_preview_profiles_isolate_one_layer_a_knob(tmp_path: Path) -> None:
    notebook = _load_notebook("en")
    preview_source = next(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell.get("id") == "l11-appearance-preview"
    )
    command_setup = preview_source.split("print('Preview command:'", maxsplit=1)[0]
    expected = {
        "table_color": (False, "0.15", "0.0"),
        "object_color": (True, "0.0", "0.0"),
        "fov": (False, "0.0", "2.0"),
    }

    for profile, (has_object_color, table_jitter, fov_jitter) in expected.items():
        source = command_setup.replace(
            "PREVIEW_PROFILE = 'combined'", f"PREVIEW_PROFILE = '{profile}'", 1
        )
        namespace = {
            "preview_root": tmp_path,
            "sys": sys,
            "use_cpu_backend": False,
        }
        exec(source, namespace)
        command = namespace["preview_command"]

        assert ("--object-color" in command) is has_object_color
        assert command[command.index("--table-jitter") + 1] == table_jitter
        assert command[command.index("--fov-jitter") + 1] == fov_jitter
        assert Path(command[command.index("--output-dir") + 1]) == (
            tmp_path / f"exercise_{profile}"
        )
