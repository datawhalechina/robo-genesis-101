import copy
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from robo_genesis.artifact_fetch import (
    ArtifactError,
    ArtifactIntegrityError,
    ArtifactManifestError,
    ArtifactTargetError,
    ArtifactUnavailableError,
    fetch_artifact,
    load_artifact_manifest,
    resolve_artifact_target,
    validate_artifact_manifest,
    verify_artifact,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "artifacts" / "manifest.json"
REVISION = "a" * 40
SOURCE_REVISION = "b" * 40
TEST_BASE_URL = (
    "https://huggingface.co/datasets/tests/artifact/resolve/" + REVISION
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _payload_manifest(files: list[dict[str, object]]) -> str:
    stream = "".join(
        f"{item['sha256']}  {item['path']}\n"
        for item in sorted(files, key=lambda item: str(item["path"]))
    ).encode("utf-8")
    return _sha256(stream)


def _manifest_data(
    base_url: str,
    payload: dict[str, bytes],
    *,
    status: str = "release",
) -> dict[str, object]:
    files = [
        {"path": path, "size": len(data), "sha256": _sha256(data)}
        for path, data in sorted(payload.items())
    ]
    return {
        "schema_version": "1.0.0",
        "course_version": "0.1.0",
        "payload_manifest_algorithm": "sha256sum-relative-path-v1",
        "artifacts": [
            {
                "id": "test-artifact",
                "version": "1.0.0",
                "kind": "dataset",
                "status": status,
                "schema_version": "1.0.0",
                "creator": "RoboGenesis test fixture",
                "license": {
                    "spdx": "MIT",
                    "notice": "Synthetic bytes created only for local tests."
                },
                "default_target": "datasets/test-artifact",
                "source": {
                    "provider": "huggingface",
                    "repo_type": "dataset",
                    "repo_id": "tests/artifact",
                    "revision": REVISION,
                    "base_url": base_url,
                },
                "payload": {
                    "size": sum(len(data) for data in payload.values()),
                    "manifest_sha256": _payload_manifest(files),
                    "files": files,
                },
                "requires": [],
                "generation": {
                    "source_repository": "tests/artifact-fixture",
                    "source_revision": SOURCE_REVISION,
                    "summary": "Small local payload used to test downloader behavior.",
                    "configuration": {"synthetic": True},
                },
                "unavailable_reason": None,
            }
        ],
    }


def _write_server_payload(root: Path, payload: dict[str, bytes]) -> None:
    for relative_path, data in payload.items():
        path = root / REVISION / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def _install_fake_urlopen(monkeypatch, root: Path) -> list[str]:
    calls: list[str] = []

    def fake_urlopen(request, *, timeout: float):
        assert timeout > 0
        calls.append(request.full_url)
        parsed = urlsplit(request.full_url)
        marker = f"/{REVISION}/"
        assert marker in parsed.path
        relative_path = unquote(parsed.path.split(marker, maxsplit=1)[1])
        return (root / REVISION / relative_path).open("rb")

    monkeypatch.setattr("robo_genesis.artifact_fetch.urlopen", fake_urlopen)
    return calls


def test_repository_manifest_freezes_release_and_unavailable_identities() -> None:
    manifest = load_artifact_manifest(MANIFEST_PATH)

    assert manifest.schema_version == "1.0.0"
    assert manifest.course_version == "0.1.0"
    assert [artifact.identity for artifact in manifest.artifacts] == [
        "rg101-fruit-pick@1.0.0",
        "rg101-fruit-pick-act@1.0.0",
        "rg101-fruit-pick-smolvla@1.0.0",
    ]

    dataset = manifest.find("rg101-fruit-pick", "1.0.0")
    assert dataset.status == "release"
    assert dataset.payload is not None
    assert dataset.payload.size == 505_224_976
    assert dataset.payload.manifest_sha256 == (
        "26cb09b621aa43f3abbe39ce2e55a3c161c2f89c9fe174fbd5e317bec4426f23"
    )
    assert dataset.source is not None
    assert dataset.source.revision == (
        "eab67399248de625506d43fdeb994788874a8492"
    )

    act = manifest.find("rg101-fruit-pick-act", "1.0.0")
    assert act.status == "unavailable"
    assert act.payload is None
    assert act.source is None
    assert "200-step smoke" in str(act.unavailable_reason)
    assert "20,000-step ACT candidate" in str(act.unavailable_reason)
    assert "all 5 reference" in str(act.unavailable_reason)
    assert act.generation.source_revision == (
        "947c9ee8a92e3b1c94f59b77d5f09006006b84a6"
    )

    smolvla = manifest.find("rg101-fruit-pick-smolvla", "1.0.0")
    assert smolvla.status == "release"
    assert smolvla.source is not None
    assert smolvla.source.revision == (
        "6649cc34576b1bf6a7ed1310251ece8c969dfafe"
    )
    assert smolvla.payload is not None
    assert smolvla.payload.size == 906_740_620
    assert smolvla.payload.manifest_sha256 == (
        "97872e6db48a225a3425cbbb94894628acccaf7d7fe7c14d830526c5178ef555"
    )
    assert smolvla.requires[0].payload_manifest_sha256 == (
        dataset.payload.manifest_sha256
    )


def test_manifest_rejects_path_traversal_and_manifest_hash_drift() -> None:
    data = _manifest_data(TEST_BASE_URL, {"file.bin": b"ok"})
    traversing = copy.deepcopy(data)
    traversing["artifacts"][0]["payload"]["files"][0]["path"] = "../file.bin"  # type: ignore[index]

    with pytest.raises(ArtifactManifestError, match="normalized relative POSIX path"):
        validate_artifact_manifest(traversing)

    bad_manifest = copy.deepcopy(data)
    bad_manifest["artifacts"][0]["payload"]["manifest_sha256"] = "0" * 64  # type: ignore[index]

    with pytest.raises(ArtifactManifestError, match="sha256sum-relative-path-v1"):
        validate_artifact_manifest(bad_manifest)

    wrong_host = copy.deepcopy(data)
    wrong_host["artifacts"][0]["source"]["base_url"] = (  # type: ignore[index]
        f"https://example.test/{REVISION}"
    )
    with pytest.raises(ArtifactManifestError, match="canonical immutable Hugging Face"):
        validate_artifact_manifest(wrong_host)


def test_fetch_is_idempotent_and_preserves_unrelated_files(
    tmp_path: Path, monkeypatch
) -> None:
    payload = {"meta/info.json": b'{"fps": 30}\n', "data/sample.bin": b"sample-bytes"}
    server_root = tmp_path / "server"
    _write_server_payload(server_root, payload)

    calls = _install_fake_urlopen(monkeypatch, server_root)
    artifact = validate_artifact_manifest(
        _manifest_data(TEST_BASE_URL, payload)
    ).find("test-artifact", "1.0.0")
    target = tmp_path / "target"
    target.mkdir()
    unrelated = target / "learner-notes.txt"
    unrelated.write_text("keep me", encoding="utf-8")

    first = fetch_artifact(artifact, target, retries=0)
    assert tuple(path.as_posix() for path in first.downloaded) == (
        "data/sample.bin",
        "meta/info.json",
    )
    assert first.repaired == ()
    assert first.reused == ()
    assert len(calls) == 2
    assert unrelated.read_text(encoding="utf-8") == "keep me"

    second = fetch_artifact(artifact, target, retries=0)
    assert second.downloaded == ()
    assert second.repaired == ()
    assert tuple(path.as_posix() for path in second.reused) == (
        "data/sample.bin",
        "meta/info.json",
    )
    assert len(calls) == 2
    assert verify_artifact(artifact, target).ok


def test_candidate_download_requires_explicit_opt_in(tmp_path: Path, monkeypatch) -> None:
    payload = {"file.bin": b"candidate"}
    server_root = tmp_path / "server"
    _write_server_payload(server_root, payload)

    calls = _install_fake_urlopen(monkeypatch, server_root)
    artifact = validate_artifact_manifest(
        _manifest_data(
            TEST_BASE_URL, payload, status="candidate"
        )
    ).find("test-artifact", "1.0.0")
    target = tmp_path / "target"

    with pytest.raises(ArtifactUnavailableError, match="--allow-candidate"):
        fetch_artifact(artifact, target, retries=0)
    assert calls == []

    result = fetch_artifact(
        artifact,
        target,
        allow_candidate=True,
        retries=0,
    )
    assert tuple(path.as_posix() for path in result.downloaded) == ("file.bin",)
    assert len(calls) == 1


def test_existing_mismatch_stops_before_network_and_repair_is_explicit(
    tmp_path: Path, monkeypatch
) -> None:
    payload = {"nested/file.bin": b"expected bytes"}
    server_root = tmp_path / "server"
    _write_server_payload(server_root, payload)

    calls = _install_fake_urlopen(monkeypatch, server_root)
    artifact = validate_artifact_manifest(
        _manifest_data(TEST_BASE_URL, payload)
    ).find("test-artifact", "1.0.0")
    target = tmp_path / "target"
    corrupt = target / "nested" / "file.bin"
    corrupt.parent.mkdir(parents=True)
    corrupt.write_bytes(b"wrong")

    with pytest.raises(ArtifactIntegrityError, match="no files were changed"):
        fetch_artifact(artifact, target, retries=0)
    assert corrupt.read_bytes() == b"wrong"
    assert calls == []

    result = fetch_artifact(artifact, target, repair=True, retries=0)
    assert result.downloaded == ()
    assert tuple(path.as_posix() for path in result.repaired) == (
        "nested/file.bin",
    )
    assert corrupt.read_bytes() == payload["nested/file.bin"]
    assert len(calls) == 1


def test_bad_download_never_becomes_a_final_file(tmp_path: Path, monkeypatch) -> None:
    expected_payload = {"file.bin": b"expected"}
    server_root = tmp_path / "server"
    _write_server_payload(server_root, {"file.bin": b"badbytes"})

    _install_fake_urlopen(monkeypatch, server_root)
    artifact = validate_artifact_manifest(
        _manifest_data(TEST_BASE_URL, expected_payload)
    ).find("test-artifact", "1.0.0")
    target = tmp_path / "target"

    with pytest.raises(ArtifactError, match="download verification failed"):
        fetch_artifact(artifact, target, retries=0)

    assert not (target / "file.bin").exists()
    assert list(target.glob("*.part")) == []
    assert list(target.glob(".*.part")) == []


def test_unavailable_artifact_and_symlink_target_fail_clearly(tmp_path: Path) -> None:
    manifest = load_artifact_manifest(MANIFEST_PATH)
    act = manifest.find("rg101-fruit-pick-act", "1.0.0")

    with pytest.raises(ArtifactUnavailableError, match="200-step smoke"):
        fetch_artifact(act, tmp_path / "act")

    payload = {"file.bin": b"safe"}
    artifact = validate_artifact_manifest(
        _manifest_data(TEST_BASE_URL, payload)
    ).find("test-artifact", "1.0.0")
    real_target = tmp_path / "real"
    real_target.mkdir()
    symlink_target = tmp_path / "link"
    symlink_target.symlink_to(real_target, target_is_directory=True)

    with pytest.raises(ArtifactTargetError, match="cannot be a symlink"):
        fetch_artifact(artifact, symlink_target, retries=0)


def test_target_override_is_the_exact_artifact_root(tmp_path: Path, monkeypatch) -> None:
    artifact = validate_artifact_manifest(
        _manifest_data(TEST_BASE_URL, {"file.bin": b"data"})
    ).find("test-artifact", "1.0.0")
    monkeypatch.chdir(tmp_path)

    assert resolve_artifact_target(artifact, None, project_root=tmp_path) == (
        tmp_path / "datasets" / "test-artifact"
    )
    assert resolve_artifact_target(artifact, "custom") == tmp_path / "custom"
