import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_NAME = "l13-closed-loop-evaluation-and-capstone.ipynb"


def _read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    return text.split(start, 1)[1].split(end, 1)[0]


def _shell_blocks(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"```sh\n(.*?)```", text, flags=re.DOTALL))


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _notebook_code(locale: str) -> str:
    notebook = json.loads(
        _read(f"notebooks/{locale}/{NOTEBOOK_NAME}")
    )
    return "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )


def test_bilingual_fallback_tutorial_matches_the_artifact_manifest() -> None:
    manifest = json.loads(_read("artifacts/manifest.json"))
    artifacts = {
        (item["id"], item["version"]): item for item in manifest["artifacts"]
    }
    dataset = artifacts[("rg101-fruit-pick", "1.0.0")]
    checkpoint = artifacts[("rg101-fruit-pick-smolvla", "1.0.0")]
    act = artifacts[("rg101-fruit-pick-act", "1.0.0")]

    en = _section(
        _read("docs/en/appendix/setup-and-fallbacks.md"),
        "## Versioned artifact fallback tutorial",
        "## Diagnose failures without hiding them",
    )
    zh = _section(
        _read("docs/zh/appendix/setup-and-fallbacks.md"),
        "## 版本化 artifact fallback 教程",
        "## 在不隐藏错误的前提下诊断",
    )

    assert _shell_blocks(en) == _shell_blocks(zh)
    assert len(_shell_blocks(en)) == 2
    for artifact in (dataset, checkpoint):
        assert artifact["status"] == "release"
        assert artifact["id"] in en and artifact["id"] in zh
        assert artifact["version"] in en and artifact["version"] in zh
        assert artifact["default_target"] in en and artifact["default_target"] in zh
    assert act["status"] == "unavailable"
    assert "ACT entry is `unavailable`" in en
    assert "ACT 条目状态为\n`unavailable`" in zh
    assert "--allow-candidate" not in en and "--allow-candidate" not in zh
    assert "formally marked `release`" in _normalized(en)
    assert "正式标记为 `release`" in _normalized(zh)


def test_fallback_tutorial_preserves_lesson_claim_boundaries() -> None:
    en = _read("docs/en/appendix/setup-and-fallbacks.md")
    zh = _read("docs/zh/appendix/setup-and-fallbacks.md")

    for command in (
        "export RG101_L10_DATASET_ROOT=datasets/fruit_pick",
        "export RG101_L10_REPO_ID=genesis/fruit_pick",
        "export RG101_DATASET_ROOT=datasets/fruit_pick",
        "export RG101_REPO_ID=genesis/fruit_pick",
        "export RG101_RUN_SMOKE=0",
    ):
        assert command in en and command in zh

    assert "does **not** count as completing L09" in _normalized(en)
    assert "**不算完成 L09**" in _normalized(zh)
    assert "does not mean that ACT or SmolVLA was trained" in _normalized(en)
    assert "不表示已经训练 ACT 或 SmolVLA" in _normalized(zh)
    assert "without claiming that you trained the model yourself" in _normalized(en)
    assert "不能声称模型由自己训练" in _normalized(zh)
    assert "does not mean closed-loop success" not in en
    assert "closed-loop evidence bar" in en
    assert "闭环证据门槛" in zh
    for internal_milestone in tuple(f"M5.{index}" for index in range(1, 9)):
        assert internal_milestone not in en
        assert internal_milestone not in zh


def test_l13_defaults_to_manifest_targets_without_implicit_artifact_downloads() -> None:
    manifest = json.loads(_read("artifacts/manifest.json"))
    artifacts = {item["id"]: item for item in manifest["artifacts"]}
    dataset = artifacts["rg101-fruit-pick"]
    checkpoint = artifacts["rg101-fruit-pick-smolvla"]
    en_code = _notebook_code("en")
    zh_code = _notebook_code("zh")

    assert en_code == zh_code
    assert f"'dataset_root': '{dataset['default_target']}'" in en_code
    assert f"'{checkpoint['default_target']}'" in en_code
    assert "COURSE_DEFAULT_DATASET = None" in en_code
    assert "allow_dataset_download=False" in en_code
    assert "fruit-pick-hf-fallback" not in en_code
    assert dataset["source"]["repo_id"] not in en_code
    assert checkpoint["source"]["repo_id"] not in en_code

    en_l12 = _read("docs/en/lessons/l12-act-and-smolvla-policy-training.md")
    zh_l12 = _read("docs/zh/lessons/l12-act-and-smolvla-policy-training.md")
    en_l13 = _read("docs/en/lessons/l13-closed-loop-evaluation-and-capstone.md")
    zh_l13 = _read("docs/zh/lessons/l13-closed-loop-evaluation-and-capstone.md")
    assert "future versioned dataset and checkpoint release" not in en_l12
    assert "未来带 checksum" not in zh_l12
    assert "never downloads these release artifacts implicitly" in en_l13
    assert "不会隐式下载这些 release artifact" in zh_l13
