"""Manifest-driven, checksum-verified course artifact downloads.

The downloader intentionally uses only the Python standard library so the
dependency-light validation environment can inspect manifests and exercise the
download contract.  Large release artifacts are never imported into Git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from .paths import PROJECT_ROOT, resolve_cli_path

DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "artifacts" / "manifest.json"
SUPPORTED_MANIFEST_MAJOR = 1
SUPPORTED_ARTIFACT_SCHEMA_MAJOR = 1
PAYLOAD_MANIFEST_ALGORITHM = "sha256sum-relative-path-v1"
USER_AGENT = "robo-genesis-101/0.1.0"

_SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_ARTIFACT_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_REPOSITORY_PATTERN = re.compile(r"^[^/\s]+/[^/\s]+$")


class ArtifactError(Exception):
    """Base exception for artifact manifest, target, and download failures."""


class ArtifactManifestError(ArtifactError):
    """Raised when an artifact manifest violates the supported schema."""


class ArtifactUnavailableError(ArtifactError):
    """Raised when a manifest entry intentionally has no downloadable payload."""


class ArtifactTargetError(ArtifactError):
    """Raised when a target path is unsafe or incompatible with the artifact."""


class ArtifactIntegrityError(ArtifactError):
    """Raised when local or downloaded bytes do not match the manifest."""


@dataclass(frozen=True)
class ArtifactLicense:
    """SPDX identity and the boundary learners must retain."""

    spdx: str
    notice: str


@dataclass(frozen=True)
class ArtifactSource:
    """One immutable HTTP source for a payload."""

    provider: str
    repo_type: str
    repo_id: str
    revision: str
    base_url: str


@dataclass(frozen=True)
class ArtifactFile:
    """One relative payload file and its immutable content identity."""

    path: PurePosixPath
    size: int
    sha256: str


@dataclass(frozen=True)
class ArtifactPayload:
    """The complete set of files fetched into one artifact target."""

    size: int
    manifest_sha256: str
    files: tuple[ArtifactFile, ...]


@dataclass(frozen=True)
class ArtifactRequirement:
    """A precise dependency on another artifact payload."""

    artifact_id: str
    version: str
    payload_manifest_sha256: str


@dataclass(frozen=True)
class ArtifactGeneration:
    """Audited source and configuration summary for artifact creation."""

    source_repository: str
    source_revision: str
    summary: str
    configuration: Mapping[str, Any]


@dataclass(frozen=True)
class ArtifactSpec:
    """One versioned dataset or checkpoint entry."""

    artifact_id: str
    version: str
    kind: str
    status: str
    schema_version: str
    creator: str
    license: ArtifactLicense
    default_target: PurePosixPath
    source: ArtifactSource | None
    payload: ArtifactPayload | None
    requires: tuple[ArtifactRequirement, ...]
    generation: ArtifactGeneration
    unavailable_reason: str | None

    @property
    def identity(self) -> str:
        return f"{self.artifact_id}@{self.version}"


@dataclass(frozen=True)
class ArtifactManifest:
    """Validated top-level artifact manifest."""

    schema_version: str
    course_version: str
    payload_manifest_algorithm: str
    artifacts: tuple[ArtifactSpec, ...]

    def find(self, artifact_id: str, version: str) -> ArtifactSpec:
        """Return one exact immutable artifact version."""
        for artifact in self.artifacts:
            if artifact.artifact_id == artifact_id and artifact.version == version:
                return artifact
        available = sorted(
            artifact.version
            for artifact in self.artifacts
            if artifact.artifact_id == artifact_id
        )
        if available:
            raise ArtifactManifestError(
                f"unknown version {version!r} for {artifact_id!r}; "
                f"available versions: {available}"
            )
        known = sorted({artifact.artifact_id for artifact in self.artifacts})
        raise ArtifactManifestError(
            f"unknown artifact {artifact_id!r}; available artifacts: {known}"
        )


@dataclass(frozen=True)
class ArtifactProblem:
    """One missing or invalid local payload path."""

    path: PurePosixPath
    reason: str
    expected: str | None = None
    actual: str | None = None

    def describe(self) -> str:
        detail = f"{self.path}: {self.reason}"
        if self.expected is not None:
            detail += f"; expected={self.expected}"
        if self.actual is not None:
            detail += f"; actual={self.actual}"
        return detail


@dataclass(frozen=True)
class VerificationReport:
    """Checksum state for one target directory."""

    artifact: ArtifactSpec
    target: Path
    valid: tuple[PurePosixPath, ...]
    missing: tuple[ArtifactProblem, ...]
    mismatched: tuple[ArtifactProblem, ...]

    @property
    def ok(self) -> bool:
        return not self.missing and not self.mismatched


@dataclass(frozen=True)
class FetchResult:
    """Summary of an idempotent fetch operation."""

    artifact: ArtifactSpec
    target: Path
    downloaded: tuple[PurePosixPath, ...]
    repaired: tuple[PurePosixPath, ...]
    reused: tuple[PurePosixPath, ...]


def _fail(source: str, location: str, message: str) -> NoReturn:
    raise ArtifactManifestError(f"{source}: {location}: {message}")


def _mapping(value: object, *, source: str, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(source, location, "expected an object")
    return value


def _exact_keys(
    value: Mapping[str, Any],
    expected: set[str],
    *,
    source: str,
    location: str,
) -> None:
    missing = sorted(expected - set(value))
    unexpected = sorted(set(value) - expected)
    if missing or unexpected:
        _fail(
            source,
            location,
            f"invalid keys; missing={missing}, unexpected={unexpected}",
        )


def _string(value: object, *, source: str, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(source, location, "expected a non-empty string")
    return value.strip()


def _semver(value: object, *, source: str, location: str) -> str:
    version = _string(value, source=source, location=location)
    if not _SEMVER_PATTERN.fullmatch(version):
        _fail(source, location, "expected MAJOR.MINOR.PATCH")
    return version


def _sha256(value: object, *, source: str, location: str) -> str:
    digest = _string(value, source=source, location=location).lower()
    if not _SHA256_PATTERN.fullmatch(digest):
        _fail(source, location, "expected a lowercase 64-hex SHA-256")
    return digest


def _relative_path(value: object, *, source: str, location: str) -> PurePosixPath:
    raw_path = _string(value, source=source, location=location)
    path = PurePosixPath(raw_path)
    if (
        path.is_absolute()
        or path in (PurePosixPath("."), PurePosixPath(""))
        or ".." in path.parts
        or "\\" in raw_path
        or path.as_posix() != raw_path
    ):
        _fail(source, location, "expected a normalized relative POSIX path")
    return path


def _positive_size(value: object, *, source: str, location: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        _fail(source, location, "expected a positive integer byte size")
    return value


def _payload_manifest_sha256(files: Sequence[ArtifactFile]) -> str:
    stream = "".join(
        f"{file.sha256}  {file.path.as_posix()}\n"
        for file in sorted(files, key=lambda item: item.path.as_posix())
    ).encode("utf-8")
    return hashlib.sha256(stream).hexdigest()


def _parse_license(value: object, *, source: str, location: str) -> ArtifactLicense:
    mapping = _mapping(value, source=source, location=location)
    _exact_keys(mapping, {"spdx", "notice"}, source=source, location=location)
    return ArtifactLicense(
        spdx=_string(mapping["spdx"], source=source, location=f"{location}.spdx"),
        notice=_string(
            mapping["notice"], source=source, location=f"{location}.notice"
        ),
    )


def _parse_source(
    value: object,
    *,
    source: str,
    location: str,
) -> ArtifactSource | None:
    if value is None:
        return None
    mapping = _mapping(value, source=source, location=location)
    _exact_keys(
        mapping,
        {"provider", "repo_type", "repo_id", "revision", "base_url"},
        source=source,
        location=location,
    )
    provider = _string(
        mapping["provider"], source=source, location=f"{location}.provider"
    )
    if provider != "huggingface":
        _fail(source, f"{location}.provider", "only 'huggingface' is supported")
    repo_type = _string(
        mapping["repo_type"], source=source, location=f"{location}.repo_type"
    )
    if repo_type not in {"dataset", "model"}:
        _fail(source, f"{location}.repo_type", "expected 'dataset' or 'model'")
    repo_id = _string(
        mapping["repo_id"], source=source, location=f"{location}.repo_id"
    )
    if not _REPOSITORY_PATTERN.fullmatch(repo_id):
        _fail(source, f"{location}.repo_id", "expected owner/repository")
    revision = _string(
        mapping["revision"], source=source, location=f"{location}.revision"
    ).lower()
    if not _REVISION_PATTERN.fullmatch(revision):
        _fail(source, f"{location}.revision", "expected a lowercase 40-hex commit")
    base_url = _string(
        mapping["base_url"], source=source, location=f"{location}.base_url"
    ).rstrip("/")
    parsed = urlsplit(base_url)
    expected_path = (
        f"/datasets/{repo_id}/resolve/{revision}"
        if repo_type == "dataset"
        else f"/{repo_id}/resolve/{revision}"
    )
    if (
        parsed.scheme != "https"
        or parsed.netloc != "huggingface.co"
        or parsed.path != expected_path
        or parsed.query
        or parsed.fragment
    ):
        _fail(
            source,
            f"{location}.base_url",
            "expected the canonical immutable Hugging Face resolve URL",
        )
    return ArtifactSource(
        provider=provider,
        repo_type=repo_type,
        repo_id=repo_id,
        revision=revision,
        base_url=base_url,
    )


def _parse_payload(
    value: object,
    *,
    source: str,
    location: str,
) -> ArtifactPayload | None:
    if value is None:
        return None
    mapping = _mapping(value, source=source, location=location)
    _exact_keys(
        mapping,
        {"size", "manifest_sha256", "files"},
        source=source,
        location=location,
    )
    raw_files = mapping["files"]
    if not isinstance(raw_files, list) or not raw_files:
        _fail(source, f"{location}.files", "expected a non-empty array")
    files: list[ArtifactFile] = []
    for index, raw_file in enumerate(raw_files):
        file_location = f"{location}.files[{index}]"
        file_mapping = _mapping(raw_file, source=source, location=file_location)
        _exact_keys(
            file_mapping,
            {"path", "size", "sha256"},
            source=source,
            location=file_location,
        )
        files.append(
            ArtifactFile(
                path=_relative_path(
                    file_mapping["path"],
                    source=source,
                    location=f"{file_location}.path",
                ),
                size=_positive_size(
                    file_mapping["size"],
                    source=source,
                    location=f"{file_location}.size",
                ),
                sha256=_sha256(
                    file_mapping["sha256"],
                    source=source,
                    location=f"{file_location}.sha256",
                ),
            )
        )
    paths = [file.path for file in files]
    if len(paths) != len(set(paths)):
        _fail(source, f"{location}.files", "file paths must be unique")
    if paths != sorted(paths, key=lambda path: path.as_posix()):
        _fail(source, f"{location}.files", "files must be sorted by relative path")

    size = _positive_size(mapping["size"], source=source, location=f"{location}.size")
    if size != sum(file.size for file in files):
        _fail(source, f"{location}.size", "does not equal the sum of file sizes")
    manifest_sha256 = _sha256(
        mapping["manifest_sha256"],
        source=source,
        location=f"{location}.manifest_sha256",
    )
    computed_manifest = _payload_manifest_sha256(files)
    if manifest_sha256 != computed_manifest:
        _fail(
            source,
            f"{location}.manifest_sha256",
            f"does not match {PAYLOAD_MANIFEST_ALGORITHM}: {computed_manifest}",
        )
    return ArtifactPayload(
        size=size,
        manifest_sha256=manifest_sha256,
        files=tuple(files),
    )


def _parse_requirements(
    value: object,
    *,
    source: str,
    location: str,
) -> tuple[ArtifactRequirement, ...]:
    if not isinstance(value, list):
        _fail(source, location, "expected an array")
    requirements: list[ArtifactRequirement] = []
    for index, raw_requirement in enumerate(value):
        item_location = f"{location}[{index}]"
        mapping = _mapping(raw_requirement, source=source, location=item_location)
        _exact_keys(
            mapping,
            {"artifact_id", "version", "payload_manifest_sha256"},
            source=source,
            location=item_location,
        )
        artifact_id = _string(
            mapping["artifact_id"],
            source=source,
            location=f"{item_location}.artifact_id",
        )
        if not _ARTIFACT_ID_PATTERN.fullmatch(artifact_id):
            _fail(source, f"{item_location}.artifact_id", "expected kebab-case")
        requirements.append(
            ArtifactRequirement(
                artifact_id=artifact_id,
                version=_semver(
                    mapping["version"],
                    source=source,
                    location=f"{item_location}.version",
                ),
                payload_manifest_sha256=_sha256(
                    mapping["payload_manifest_sha256"],
                    source=source,
                    location=f"{item_location}.payload_manifest_sha256",
                ),
            )
        )
    identities = [(item.artifact_id, item.version) for item in requirements]
    if len(identities) != len(set(identities)):
        _fail(source, location, "requirements must be unique")
    return tuple(requirements)


def _parse_generation(
    value: object,
    *,
    source: str,
    location: str,
) -> ArtifactGeneration:
    mapping = _mapping(value, source=source, location=location)
    _exact_keys(
        mapping,
        {"source_repository", "source_revision", "summary", "configuration"},
        source=source,
        location=location,
    )
    source_revision = _string(
        mapping["source_revision"],
        source=source,
        location=f"{location}.source_revision",
    ).lower()
    if not _REVISION_PATTERN.fullmatch(source_revision):
        _fail(source, f"{location}.source_revision", "expected a 40-hex commit")
    configuration = _mapping(
        mapping["configuration"],
        source=source,
        location=f"{location}.configuration",
    )
    return ArtifactGeneration(
        source_repository=_string(
            mapping["source_repository"],
            source=source,
            location=f"{location}.source_repository",
        ),
        source_revision=source_revision,
        summary=_string(
            mapping["summary"], source=source, location=f"{location}.summary"
        ),
        configuration=dict(configuration),
    )


def _parse_artifact(
    value: object,
    *,
    source: str,
    index: int,
) -> ArtifactSpec:
    location = f"artifacts[{index}]"
    mapping = _mapping(value, source=source, location=location)
    _exact_keys(
        mapping,
        {
            "id",
            "version",
            "kind",
            "status",
            "schema_version",
            "creator",
            "license",
            "default_target",
            "source",
            "payload",
            "requires",
            "generation",
            "unavailable_reason",
        },
        source=source,
        location=location,
    )
    artifact_id = _string(mapping["id"], source=source, location=f"{location}.id")
    if not _ARTIFACT_ID_PATTERN.fullmatch(artifact_id):
        _fail(source, f"{location}.id", "expected lowercase kebab-case")
    kind = _string(mapping["kind"], source=source, location=f"{location}.kind")
    if kind not in {"dataset", "checkpoint"}:
        _fail(source, f"{location}.kind", "expected 'dataset' or 'checkpoint'")
    status = _string(mapping["status"], source=source, location=f"{location}.status")
    if status not in {"candidate", "release", "unavailable"}:
        _fail(
            source,
            f"{location}.status",
            "expected 'candidate', 'release', or 'unavailable'",
        )
    raw_reason = mapping["unavailable_reason"]
    unavailable_reason = (
        None
        if raw_reason is None
        else _string(raw_reason, source=source, location=f"{location}.unavailable_reason")
    )
    artifact = ArtifactSpec(
        artifact_id=artifact_id,
        version=_semver(
            mapping["version"], source=source, location=f"{location}.version"
        ),
        kind=kind,
        status=status,
        schema_version=_semver(
            mapping["schema_version"],
            source=source,
            location=f"{location}.schema_version",
        ),
        creator=_string(
            mapping["creator"], source=source, location=f"{location}.creator"
        ),
        license=_parse_license(
            mapping["license"], source=source, location=f"{location}.license"
        ),
        default_target=_relative_path(
            mapping["default_target"],
            source=source,
            location=f"{location}.default_target",
        ),
        source=_parse_source(
            mapping["source"], source=source, location=f"{location}.source"
        ),
        payload=_parse_payload(
            mapping["payload"], source=source, location=f"{location}.payload"
        ),
        requires=_parse_requirements(
            mapping["requires"], source=source, location=f"{location}.requires"
        ),
        generation=_parse_generation(
            mapping["generation"], source=source, location=f"{location}.generation"
        ),
        unavailable_reason=unavailable_reason,
    )
    if (
        int(artifact.schema_version.split(".", maxsplit=1)[0])
        != SUPPORTED_ARTIFACT_SCHEMA_MAJOR
    ):
        _fail(
            source,
            f"{location}.schema_version",
            f"unsupported major; expected {SUPPORTED_ARTIFACT_SCHEMA_MAJOR}.x.x",
        )
    if status == "unavailable":
        if artifact.source is not None or artifact.payload is not None:
            _fail(source, location, "unavailable artifacts cannot define source or payload")
        if artifact.unavailable_reason is None:
            _fail(source, location, "unavailable artifacts require a reason")
    else:
        if artifact.source is None or artifact.payload is None:
            _fail(source, location, "fetchable artifacts require source and payload")
        if artifact.unavailable_reason is not None:
            _fail(source, location, "fetchable artifacts cannot have unavailable_reason")
    if kind == "dataset" and artifact.requires:
        _fail(source, f"{location}.requires", "dataset artifacts cannot require checkpoints")
    if kind == "checkpoint" and len(artifact.requires) != 1:
        _fail(source, f"{location}.requires", "checkpoint artifacts must bind one dataset")
    if artifact.source is not None:
        expected_repo_type = "dataset" if kind == "dataset" else "model"
        if artifact.source.repo_type != expected_repo_type:
            _fail(
                source,
                f"{location}.source.repo_type",
                f"{kind} artifacts require repo_type={expected_repo_type!r}",
            )
    return artifact


def validate_artifact_manifest(
    value: object,
    *,
    source: str = "<memory>",
) -> ArtifactManifest:
    """Validate and convert a raw JSON-compatible artifact manifest."""
    mapping = _mapping(value, source=source, location="<root>")
    _exact_keys(
        mapping,
        {"schema_version", "course_version", "payload_manifest_algorithm", "artifacts"},
        source=source,
        location="<root>",
    )
    schema_version = _semver(
        mapping["schema_version"], source=source, location="schema_version"
    )
    if int(schema_version.split(".", maxsplit=1)[0]) != SUPPORTED_MANIFEST_MAJOR:
        _fail(
            source,
            "schema_version",
            f"unsupported major; expected {SUPPORTED_MANIFEST_MAJOR}.x.x",
        )
    course_version = _semver(
        mapping["course_version"], source=source, location="course_version"
    )
    algorithm = _string(
        mapping["payload_manifest_algorithm"],
        source=source,
        location="payload_manifest_algorithm",
    )
    if algorithm != PAYLOAD_MANIFEST_ALGORITHM:
        _fail(
            source,
            "payload_manifest_algorithm",
            f"expected {PAYLOAD_MANIFEST_ALGORITHM!r}",
        )
    raw_artifacts = mapping["artifacts"]
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        _fail(source, "artifacts", "expected a non-empty array")
    artifacts = tuple(
        _parse_artifact(raw_artifact, source=source, index=index)
        for index, raw_artifact in enumerate(raw_artifacts)
    )
    identities = [(artifact.artifact_id, artifact.version) for artifact in artifacts]
    if len(identities) != len(set(identities)):
        _fail(source, "artifacts", "artifact id/version pairs must be unique")
    index = {
        (artifact.artifact_id, artifact.version): artifact for artifact in artifacts
    }
    for artifact in artifacts:
        for requirement in artifact.requires:
            required = index.get((requirement.artifact_id, requirement.version))
            if required is None or required.payload is None:
                _fail(
                    source,
                    f"{artifact.identity}.requires",
                    f"unknown or unavailable dependency {requirement.artifact_id}@"
                    f"{requirement.version}",
                )
            if required.kind != "dataset":
                _fail(
                    source,
                    f"{artifact.identity}.requires",
                    f"checkpoint dependency {required.identity} is not a dataset",
                )
            if required.payload.manifest_sha256 != requirement.payload_manifest_sha256:
                _fail(
                    source,
                    f"{artifact.identity}.requires",
                    f"dependency manifest mismatch for {required.identity}",
                )
    return ArtifactManifest(
        schema_version=schema_version,
        course_version=course_version,
        payload_manifest_algorithm=algorithm,
        artifacts=artifacts,
    )


def load_artifact_manifest(path: str | Path = DEFAULT_MANIFEST_PATH) -> ArtifactManifest:
    """Load and validate one UTF-8 JSON artifact manifest."""
    manifest_path = Path(path).expanduser().resolve()
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactManifestError(
            f"cannot read artifact manifest {manifest_path}: {exc}"
        ) from exc
    return validate_artifact_manifest(raw, source=str(manifest_path))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _absolute_target(value: str | Path) -> Path:
    """Make a target absolute without resolving away a final symlink."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return Path(os.path.abspath(path))


def _inspect_parent_directories(target: Path, relative_path: PurePosixPath) -> None:
    current = target
    for part in relative_path.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ArtifactTargetError(
                f"artifact target contains a symlinked directory: {current}"
            )
        if current.exists() and not current.is_dir():
            raise ArtifactTargetError(
                f"artifact target path is not a directory: {current}"
            )


def _validate_target_root(target: Path, *, allow_missing: bool) -> None:
    if target.is_symlink():
        raise ArtifactTargetError(f"artifact target cannot be a symlink: {target}")
    if target.exists() and not target.is_dir():
        raise ArtifactTargetError(f"artifact target is not a directory: {target}")
    if not target.exists() and not allow_missing:
        raise ArtifactTargetError(f"artifact target does not exist: {target}")


def verify_artifact(artifact: ArtifactSpec, target: str | Path) -> VerificationReport:
    """Verify every manifest-owned file without changing the target."""
    if artifact.payload is None:
        raise ArtifactUnavailableError(
            f"{artifact.identity} is unavailable: {artifact.unavailable_reason}"
        )
    target_path = _absolute_target(target)
    _validate_target_root(target_path, allow_missing=True)
    if not target_path.exists():
        return VerificationReport(
            artifact=artifact,
            target=target_path,
            valid=(),
            missing=tuple(
                ArtifactProblem(file.path, "missing") for file in artifact.payload.files
            ),
            mismatched=(),
        )
    _validate_target_root(target_path, allow_missing=False)
    valid: list[PurePosixPath] = []
    missing: list[ArtifactProblem] = []
    mismatched: list[ArtifactProblem] = []
    for expected in artifact.payload.files:
        _inspect_parent_directories(target_path, expected.path)
        path = target_path.joinpath(*expected.path.parts)
        if path.is_symlink():
            mismatched.append(ArtifactProblem(expected.path, "symlinks are not allowed"))
            continue
        if not path.exists():
            missing.append(ArtifactProblem(expected.path, "missing"))
            continue
        if not path.is_file():
            mismatched.append(ArtifactProblem(expected.path, "expected a regular file"))
            continue
        actual_size = path.stat().st_size
        if actual_size != expected.size:
            mismatched.append(
                ArtifactProblem(
                    expected.path,
                    "size mismatch",
                    expected=str(expected.size),
                    actual=str(actual_size),
                )
            )
            continue
        actual_digest = _sha256_file(path)
        if actual_digest != expected.sha256:
            mismatched.append(
                ArtifactProblem(
                    expected.path,
                    "SHA-256 mismatch",
                    expected=expected.sha256,
                    actual=actual_digest,
                )
            )
            continue
        valid.append(expected.path)
    return VerificationReport(
        artifact=artifact,
        target=target_path,
        valid=tuple(valid),
        missing=tuple(missing),
        mismatched=tuple(mismatched),
    )


def resolve_artifact_target(
    artifact: ArtifactSpec,
    target: str | Path | None,
    *,
    project_root: str | Path = PROJECT_ROOT,
) -> Path:
    """Resolve an exact artifact root; ``--target`` is not a parent directory."""
    if target is not None:
        return _absolute_target(target)
    root = Path(project_root).expanduser().resolve()
    return root.joinpath(*artifact.default_target.parts)


def _download_url(source: ArtifactSource, relative_path: PurePosixPath) -> str:
    return f"{source.base_url}/{quote(relative_path.as_posix(), safe='/')}?download=true"


def _prepare_parent(target: Path, relative_path: PurePosixPath) -> Path:
    current = target
    for part in relative_path.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ArtifactTargetError(
                f"artifact target contains a symlinked directory: {current}"
            )
        if current.exists() and not current.is_dir():
            raise ArtifactTargetError(
                f"artifact target path is not a directory: {current}"
            )
        current.mkdir(exist_ok=True)
    return target.joinpath(*relative_path.parts)


def _download_once(
    source: ArtifactSource,
    expected: ArtifactFile,
    destination: Path,
    *,
    timeout: float,
) -> None:
    url = _download_url(source, expected.path)
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".part",
            delete=False,
        ) as output:
            temp_path = Path(output.name)
            digest = hashlib.sha256()
            size = 0
            with urlopen(request, timeout=timeout) as response:
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > expected.size:
                        raise ArtifactIntegrityError(
                            f"downloaded file exceeds expected size for {expected.path}: "
                            f"expected={expected.size}, received>{expected.size}"
                        )
                    digest.update(chunk)
                    output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        actual_digest = digest.hexdigest()
        if size != expected.size or actual_digest != expected.sha256:
            raise ArtifactIntegrityError(
                f"download verification failed for {expected.path}: "
                f"expected size/SHA-256={expected.size}/{expected.sha256}, "
                f"actual={size}/{actual_digest}"
            )
        os.replace(temp_path, destination)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _download_with_retries(
    source: ArtifactSource,
    expected: ArtifactFile,
    destination: Path,
    *,
    retries: int,
    timeout: float,
) -> None:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            _download_once(source, expected, destination, timeout=timeout)
            return
        except Exception as exc:  # URL, filesystem, and integrity failures need context
            last_error = exc
            if attempt < retries:
                time.sleep(min(2**attempt, 5))
    assert last_error is not None
    url = _download_url(source, expected.path)
    raise ArtifactError(
        f"could not fetch {expected.path} from {url} after {retries + 1} attempt(s): "
        f"{type(last_error).__name__}: {last_error}"
    ) from last_error


def fetch_artifact(
    artifact: ArtifactSpec,
    target: str | Path,
    *,
    allow_candidate: bool = False,
    repair: bool = False,
    retries: int = 2,
    timeout: float = 60.0,
) -> FetchResult:
    """Fetch missing files and verify the complete payload.

    Existing valid files are reused. Existing mismatches stop before network
    access unless ``repair`` is explicitly enabled. No unrelated target files
    are deleted.
    """
    if artifact.status == "unavailable" or artifact.payload is None or artifact.source is None:
        raise ArtifactUnavailableError(
            f"{artifact.identity} is unavailable: {artifact.unavailable_reason}"
        )
    if artifact.status == "candidate" and not allow_candidate:
        raise ArtifactUnavailableError(
            f"{artifact.identity} is a candidate payload, not a release; "
            "pass --allow-candidate only for the audited M5 baseline"
        )
    if retries < 0:
        raise ValueError("retries must be non-negative")
    if timeout <= 0:
        raise ValueError("timeout must be positive")

    target_path = _absolute_target(target)
    report = verify_artifact(artifact, target_path)
    if report.mismatched and not repair:
        details = "\n  ".join(problem.describe() for problem in report.mismatched)
        raise ArtifactIntegrityError(
            f"{artifact.identity} has invalid existing files; no files were changed. "
            f"Re-run with --repair to replace only these manifest-owned paths:\n  {details}"
        )

    _validate_target_root(target_path, allow_missing=True)
    target_path.mkdir(parents=True, exist_ok=True)
    missing_paths = {problem.path for problem in report.missing}
    repair_paths = {problem.path for problem in report.mismatched}
    for expected in artifact.payload.files:
        if expected.path not in missing_paths and expected.path not in repair_paths:
            continue
        destination = _prepare_parent(target_path, expected.path)
        if destination.is_symlink():
            raise ArtifactTargetError(
                f"manifest-owned destination cannot be a symlink: {destination}"
            )
        _download_with_retries(
            artifact.source,
            expected,
            destination,
            retries=retries,
            timeout=timeout,
        )

    final_report = verify_artifact(artifact, target_path)
    if not final_report.ok:
        problems = (*final_report.missing, *final_report.mismatched)
        details = "\n  ".join(problem.describe() for problem in problems)
        raise ArtifactIntegrityError(
            f"{artifact.identity} target failed final verification:\n  {details}"
        )
    return FetchResult(
        artifact=artifact,
        target=target_path,
        downloaded=tuple(
            file.path for file in artifact.payload.files if file.path in missing_paths
        ),
        repaired=tuple(
            file.path for file in artifact.payload.files if file.path in repair_paths
        ),
        reused=tuple(
            file.path
            for file in artifact.payload.files
            if file.path not in missing_paths and file.path not in repair_paths
        ),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch immutable RoboGenesis course artifacts with SHA-256 verification."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="Course workspace used for manifest default targets.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Artifact manifest (default: ROOT/artifacts/manifest.json).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List exact artifact versions and availability.")

    for command in ("verify", "fetch"):
        command_parser = subparsers.add_parser(
            command,
            help=f"{command.capitalize()} one exact artifact version.",
        )
        command_parser.add_argument("artifact_id")
        command_parser.add_argument("version")
        command_parser.add_argument(
            "--target",
            type=Path,
            help="Exact artifact root, not a parent directory.",
        )
        if command == "fetch":
            command_parser.add_argument(
                "--allow-candidate",
                action="store_true",
                help="Explicitly allow an audited candidate that is not release-ready.",
            )
            command_parser.add_argument(
                "--repair",
                action="store_true",
                help="Replace only manifest-owned files that fail size or SHA-256 checks.",
            )
            command_parser.add_argument(
                "--retries",
                type=int,
                default=2,
                help="Retries after the first HTTP attempt (default: 2).",
            )
            command_parser.add_argument(
                "--timeout",
                type=float,
                default=60.0,
                help="Per-request timeout in seconds (default: 60).",
            )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point for listing, verifying, and fetching artifacts."""
    parser = _parser()
    args = parser.parse_args(argv)
    root = resolve_cli_path(args.root)
    manifest_path = (
        resolve_cli_path(args.manifest)
        if args.manifest is not None
        else root / "artifacts" / "manifest.json"
    )
    try:
        manifest = load_artifact_manifest(manifest_path)
        if args.command == "list":
            for artifact in manifest.artifacts:
                size = "-" if artifact.payload is None else str(artifact.payload.size)
                print(
                    f"{artifact.artifact_id}\t{artifact.version}\t{artifact.kind}\t"
                    f"{artifact.status}\t{size}\t{artifact.default_target}"
                )
            return

        artifact = manifest.find(args.artifact_id, args.version)
        target = resolve_artifact_target(artifact, args.target, project_root=root)
        if args.command == "verify":
            report = verify_artifact(artifact, target)
            if not report.ok:
                problems = (*report.missing, *report.mismatched)
                details = "\n  ".join(problem.describe() for problem in problems)
                raise ArtifactIntegrityError(
                    f"{artifact.identity} verification failed at {target}:\n  {details}"
                )
            print(
                f"verified {artifact.identity}: files={len(report.valid)} target={target}"
            )
            return

        result = fetch_artifact(
            artifact,
            target,
            allow_candidate=args.allow_candidate,
            repair=args.repair,
            retries=args.retries,
            timeout=args.timeout,
        )
        print(
            f"verified {artifact.identity}: downloaded={len(result.downloaded)} "
            f"repaired={len(result.repaired)} reused={len(result.reused)} "
            f"target={result.target} status={artifact.status}"
        )
    except (ArtifactError, ValueError) as exc:
        parser.exit(2, f"Artifact operation failed: {exc}\n")


__all__ = [
    "ArtifactError",
    "ArtifactFile",
    "ArtifactGeneration",
    "ArtifactIntegrityError",
    "ArtifactLicense",
    "ArtifactManifest",
    "ArtifactManifestError",
    "ArtifactPayload",
    "ArtifactProblem",
    "ArtifactRequirement",
    "ArtifactSource",
    "ArtifactSpec",
    "ArtifactTargetError",
    "ArtifactUnavailableError",
    "DEFAULT_MANIFEST_PATH",
    "FetchResult",
    "PAYLOAD_MANIFEST_ALGORITHM",
    "VerificationReport",
    "fetch_artifact",
    "load_artifact_manifest",
    "main",
    "resolve_artifact_target",
    "validate_artifact_manifest",
    "verify_artifact",
]


if __name__ == "__main__":
    main()
