import json
import re
from pathlib import Path

from robo_genesis.course_validation import (
    _paired_relative_files,
    markdown_heading_levels,
    parse_frontmatter,
    validate_notebook_pair,
    validate_repository,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _notebook(code: str, *, outputs: list[object] | None = None) -> dict[str, object]:
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "id": "overview",
                "metadata": {},
                "source": ["# Lesson\n"],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "id": "example",
                "metadata": {},
                "outputs": [] if outputs is None else outputs,
                "source": [code],
            },
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _notebook_code(path: Path) -> str:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )


def _notebook_markdown(path: Path) -> str:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "markdown"
    )


def _fenced_blocks(text: str, *, languages: set[str]) -> tuple[tuple[str, str], ...]:
    blocks: list[tuple[str, str]] = []
    marker: str | None = None
    language = ""
    body: list[str] = []

    for line in text.splitlines():
        stripped = line.lstrip()
        if marker is None:
            match = re.fullmatch(r"(`{3,}|~{3,})(.*)", stripped)
            if match is None:
                continue
            marker = match.group(1)
            language = match.group(2).strip().split(maxsplit=1)[0].casefold()
            body = []
            continue

        if re.fullmatch(rf"{re.escape(marker[0])}{{{len(marker)},}}\s*", stripped):
            if language in languages:
                blocks.append((language, "\n".join(body)))
            marker = None
            language = ""
            body = []
            continue

        body.append(line)

    return tuple(blocks)


def test_repository_passes_all_course_gates() -> None:
    summary = validate_repository(PROJECT_ROOT)

    assert summary.lessons == 14
    assert summary.markdown_files == 34
    assert summary.notebooks == 28
    assert summary.python_files == 45


def test_bilingual_project_documents_have_matching_heading_structure() -> None:
    readme_zh = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_en = (PROJECT_ROOT / "README_en.md").read_text(encoding="utf-8")

    assert markdown_heading_levels(readme_zh) == markdown_heading_levels(readme_en)

    for name in ("CONTRIBUTING.md", "CONTENT_GUIDE.md"):
        text = (PROJECT_ROOT / name).read_text(encoding="utf-8")
        zh_section = text.split("\n## 中文\n", maxsplit=1)[1].split(
            "\n## English\n", maxsplit=1
        )[0]
        en_section = text.split("\n## English\n", maxsplit=1)[1]
        assert markdown_heading_levels(zh_section) == markdown_heading_levels(en_section)


def test_frontmatter_and_heading_parser_ignore_fenced_examples() -> None:
    text = """---
lesson: L01
duration_minutes: 60
title: "A lesson: with a colon"
---

# Top level

```python
## Not a Markdown heading
```

## Real subsection
"""

    document = parse_frontmatter(text)

    assert document.frontmatter == {
        "lesson": "L01",
        "duration_minutes": 60,
        "title": "A lesson: with a colon",
    }
    assert markdown_heading_levels(text) == (1, 2)


def test_notebook_pair_rejects_code_drift_outputs_and_syntax(tmp_path: Path) -> None:
    zh_path = tmp_path / "zh.ipynb"
    en_path = tmp_path / "en.ipynb"
    zh_path.write_text(json.dumps(_notebook("value = 1\n")), encoding="utf-8")
    en_path.write_text(
        json.dumps(_notebook("value = (\n", outputs=[{"output_type": "stream"}])),
        encoding="utf-8",
    )

    errors = validate_notebook_pair(zh_path, en_path)

    assert any("committed outputs are not allowed" in error for error in errors)
    assert any("Python syntax error" in error for error in errors)
    assert any("code cell 1 sources differ" in error for error in errors)


def test_paired_files_ignore_jupyter_checkpoints(tmp_path: Path) -> None:
    for locale in ("zh", "en"):
        locale_directory = tmp_path / "notebooks" / locale
        locale_directory.mkdir(parents=True)
        (locale_directory / "lesson.ipynb").write_text("{}", encoding="utf-8")

    checkpoint_directory = tmp_path / "notebooks" / "en" / ".ipynb_checkpoints"
    checkpoint_directory.mkdir()
    (checkpoint_directory / "lesson-checkpoint.ipynb").write_text("{}", encoding="utf-8")

    errors: list[str] = []
    localized, relative_paths = _paired_relative_files(
        tmp_path,
        base_directory="notebooks",
        pattern="*.ipynb",
        errors=errors,
    )

    assert errors == []
    assert {path.as_posix() for path in relative_paths} == {"lesson.ipynb"}
    assert all(
        {path.as_posix() for path in files} == {"lesson.ipynb"}
        for files in localized.values()
    )


def test_cross_lesson_dataset_and_checkpoint_handoffs_remain_explicit() -> None:
    notebooks = PROJECT_ROOT / "notebooks" / "en"
    l09 = _notebook_code(notebooks / "l09-synthetic-data-recording-and-throughput.ipynb")
    l10 = _notebook_code(notebooks / "l10-dataset-anatomy-and-imitation-learning.ipynb")
    l11 = _notebook_code(notebooks / "l11-domain-randomization.ipynb")
    l12 = _notebook_code(notebooks / "l12-act-and-smolvla-policy-training.ipynb")
    l13 = _notebook_code(notebooks / "l13-closed-loop-evaluation-and-capstone.ipynb")

    assert "REPO_ID = 'local/l09_banana_demo'" in l09
    assert "dataset_parent = DATASETS_DIR.resolve()" in l09
    assert "dataset_parent / 'l09_banana_demo'" in l09
    assert "DATASETS_DIR / 'l09_banana_demo'" in l10
    assert "'RG101_L11_BASELINE_REPO_ID', 'local/l09_banana_demo'" in l11
    assert "DATASETS_DIR / 'l09_banana_demo'" in l11
    assert "DR_REPO_ID = 'local/l11_banana_dr'" in l11
    assert "DATASETS_DIR / 'l11_banana_dr'" in l11

    assert 'os.environ.get("RG101_REPO_ID", "genesis/fruit_pick")' in l12
    assert 'str(DATASETS_DIR / "fruit_pick")' in l12
    assert "'dataset_repo_id': 'genesis/fruit_pick'" in l13
    assert "'dataset_root': 'datasets/fruit_pick'" in l13
    assert "COURSE_DEFAULT_DATASET = {" in l13
    assert "COURSE_DEFAULT_CHECKPOINT = {" in l13


def test_core_lessons_do_not_require_the_l14_companion_runtime() -> None:
    forbidden_runtime_fragments = (
        "/RoboTwin",
        "/opt/robotwin-env",
        "/opt/lerobot-env",
        "robo_genesis.l14_workflow",
    )
    notebooks = PROJECT_ROOT / "notebooks" / "en"
    for path in sorted(notebooks.glob("l*.ipynb")):
        if path.name.startswith("l14-"):
            continue
        code = _notebook_code(path)
        assert not any(fragment in code for fragment in forbidden_runtime_fragments), path

    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8").casefold()
    for dependency_name in ("robotwin", "lingbot", "xpolicylab", "aiter"):
        assert dependency_name not in pyproject

    for path in sorted((PROJECT_ROOT / "src" / "robo_genesis").rglob("*.py")):
        if path.name == "l14_workflow.py":
            continue
        source = path.read_text(encoding="utf-8")
        assert not any(fragment in source for fragment in forbidden_runtime_fragments), path


def test_verified_lessons_do_not_describe_available_notebooks_as_planned() -> None:
    lesson_text = "\n".join(
        path.read_text(encoding="utf-8")
        for locale in ("en", "zh")
        for path in sorted((PROJECT_ROOT / "docs" / locale / "lessons").glob("*.md"))
    )
    for stale_phrase in (
        "The companion notebook, when published",
        "配套 notebook 发布后",
        "The planned L08 notebook",
        "规划中的 L08 notebook",
    ):
        assert stale_phrase not in lesson_text


def test_bilingual_shell_commands_remain_identical() -> None:
    shell_languages = {"bash", "console", "sh", "shell"}
    lecture_root = PROJECT_ROOT / "docs"

    for en_path in sorted((lecture_root / "en" / "lessons").glob("*.md")):
        zh_path = lecture_root / "zh" / "lessons" / en_path.name
        en_blocks = _fenced_blocks(
            en_path.read_text(encoding="utf-8"), languages=shell_languages
        )
        zh_blocks = _fenced_blocks(
            zh_path.read_text(encoding="utf-8"), languages=shell_languages
        )
        assert zh_blocks == en_blocks, en_path.name

    notebook_root = PROJECT_ROOT / "notebooks"
    for en_path in sorted((notebook_root / "en").glob("*.ipynb")):
        zh_path = notebook_root / "zh" / en_path.name
        en_blocks = _fenced_blocks(
            _notebook_markdown(en_path), languages=shell_languages
        )
        zh_blocks = _fenced_blocks(
            _notebook_markdown(zh_path), languages=shell_languages
        )
        assert zh_blocks == en_blocks, en_path.name


def test_chinese_course_material_uses_canonical_glossary_terms() -> None:
    lectures = PROJECT_ROOT / "docs" / "zh" / "lessons"
    notebooks = PROJECT_ROOT / "notebooks" / "zh"

    l08_overview = (
        lectures / "l08-demonstration-acquisition-and-scripted-experts.md"
    ).read_text(encoding="utf-8")
    l08_methods = (
        lectures / "l08-demonstration-acquisition-methods.md"
    ).read_text(encoding="utf-8")
    l10 = (lectures / "l10-dataset-anatomy-and-imitation-learning.md").read_text(
        encoding="utf-8"
    )
    l11 = (lectures / "l11-domain-randomization.md").read_text(encoding="utf-8")
    l12_en = (
        PROJECT_ROOT / "docs" / "en" / "lessons" / "l12-act-and-smolvla-policy-training.md"
    ).read_text(encoding="utf-8")
    l12_zh = (lectures / "l12-act-and-smolvla-policy-training.md").read_text(
        encoding="utf-8"
    )

    assert "scripted rollout" in l08_overview
    assert "scripted rollout（" not in l08_overview
    assert "演示数据（demonstration）" in l08_methods
    assert "模仿学习（imitation learning）" in l10
    assert "闭环评估（closed-loop evaluation）" in l10
    assert "域随机化（domain randomization，DR）" in l11
    assert "`snapshots/<40-hex-commit>`" in l12_en
    assert "`snapshots/<40-hex-commit>`" in l12_zh

    chinese_learner_text = "\n".join(
        [
            *(
                path.read_text(encoding="utf-8")
                for path in sorted(lectures.glob("*.md"))
            ),
            *(_notebook_markdown(path) for path in sorted(notebooks.glob("*.ipynb"))),
        ]
    )
    assert "snapshots/<40 位十六进制 commit>" not in chinese_learner_text
