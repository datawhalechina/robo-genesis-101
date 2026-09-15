import copy

import pytest

from robo_genesis.domain_provenance import (
    DOMAIN_PROVENANCE_RELATIVE_PATH,
    DomainProvenanceError,
    committed_episode_records,
    load_domain_provenance,
    plan_domain_split,
    plan_seed_schedule,
    validate_domain_provenance,
    validate_domain_split,
    validate_dr_collection_config,
    write_domain_provenance,
)


def _valid_collection_config() -> dict:
    return {
        "episodes": 2,
        "max_attempts": 10,
        "fps": 5,
        "image_width": 160,
        "image_height": 120,
        "dr_rebuild_every": 1,
        "table_color_jitter": 0.15,
        "fov_jitter_deg": 2.0,
        "camera_fovs_deg": (42.0, 42.0),
        "friction_ratio_range": (0.7, 1.3),
        "mass_ratio_range": (0.8, 1.2),
        "cam_pos_jitter": 0.01,
        "cam_lookat_jitter": 0.02,
    }


def _provenance_fixture() -> dict:
    schedule = plan_seed_schedule(
        [False, True, True, True, True],
        runtime_base_seed=1100,
        appearance_base_seed=20,
        rebuild_every=2,
    )
    attempts = []
    for row in schedule:
        success = row["success"]
        attempts.append(
            {
                **row,
                "pick_object": "011_banana",
                "actual": {
                    "friction_ratio": 1.0,
                    "mass_ratios": {"011_banana": 1.0},
                    "world_camera_pose": {
                        "pos": [0.5, -0.5, 0.8],
                        "lookat": [0.0, 0.0, 0.2],
                    },
                },
                "committed": success,
                "frame_count": 12,
            }
        )
    return {
        "schema_version": 1,
        "implementation_version": "0.1.0",
        "requested": {
            "repo_id": "local/test",
            "successful_episodes": 4,
            "max_attempts": 10,
            "appearance": {
                "enabled": True,
                "base_seed": 20,
                "rebuild_every": 2,
            },
            "runtime": {
                "enabled": True,
                "base_seed": 1100,
                "friction_ratio_range": [0.7, 1.3],
                "mass_ratio_range": [0.8, 1.2],
                "cam_pos_jitter": 0.01,
                "cam_lookat_jitter": 0.02,
            },
        },
        "attempts": attempts,
        "summary": {
            "attempts": 5,
            "successful_attempts": 4,
            "failed_attempts": 1,
            "committed_successful_episodes": 4,
            "committed_debug_failures": 0,
            "complete": True,
        },
    }


def test_collection_config_validation_normalizes_safe_ranges() -> None:
    normalized = validate_dr_collection_config(**_valid_collection_config())

    assert normalized["friction_ratio_range"] == [0.7, 1.3]
    assert normalized["mass_ratio_range"] == [0.8, 1.2]
    assert normalized["camera_fovs_deg"] == [42.0, 42.0]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("dr_rebuild_every", 0, "positive integer"),
        ("table_color_jitter", -0.1, "non-negative"),
        ("fov_jitter_deg", 42.0, "smaller than every baseline"),
        ("friction_ratio_range", (0.0, 1.0), "values must be positive"),
        ("friction_ratio_range", (1.2, 0.8), "lower bound"),
        ("mass_ratio_range", (-0.1, 1.0), "values must be positive"),
        ("cam_pos_jitter", -0.01, "non-negative"),
        ("cam_lookat_jitter", float("inf"), "finite number"),
    ],
)
def test_collection_config_validation_rejects_unsafe_values(
    field: str, value: object, message: str
) -> None:
    config = _valid_collection_config()
    config[field] = value

    with pytest.raises(DomainProvenanceError, match=message):
        validate_dr_collection_config(**config)


def test_seed_schedule_uses_attempts_for_runtime_and_successes_for_appearance() -> None:
    schedule = plan_seed_schedule(
        [False, True, True],
        runtime_base_seed=1100,
        appearance_base_seed=50,
        rebuild_every=1,
    )

    assert [row["runtime_seed"] for row in schedule] == [1100, 1101, 1102]
    assert [row["appearance_domain_index"] for row in schedule] == [0, 0, 1]
    assert [row["appearance_seed"] for row in schedule] == [50, 50, 51]
    assert [row["committed_episode_index"] for row in schedule] == [None, 0, 1]


def test_seed_schedule_keeps_one_inert_appearance_domain_when_disabled() -> None:
    schedule = plan_seed_schedule(
        [True, True, True],
        runtime_base_seed=1100,
        appearance_base_seed=50,
        rebuild_every=1,
        appearance_enabled=False,
    )

    assert [row["appearance_domain_index"] for row in schedule] == [0, 0, 0]
    assert [row["appearance_seed"] for row in schedule] == [None, None, None]


def test_sidecar_round_trip_and_committed_episode_mapping(tmp_path) -> None:
    provenance = _provenance_fixture()

    path = write_domain_provenance(tmp_path, provenance)
    loaded = load_domain_provenance(tmp_path)
    records = committed_episode_records(loaded)

    assert path == tmp_path / DOMAIN_PROVENANCE_RELATIVE_PATH
    assert loaded == provenance
    assert [record["committed_episode_index"] for record in records] == [0, 1, 2, 3]
    assert [record["attempt_index"] for record in records] == [1, 2, 3, 4]


def test_sidecar_validation_rejects_a_seed_schedule_mismatch() -> None:
    provenance = _provenance_fixture()
    provenance["attempts"][2]["runtime_seed"] = 9999

    with pytest.raises(DomainProvenanceError, match="runtime_seed"):
        validate_domain_provenance(provenance)


def test_runtime_only_sidecar_keeps_one_inert_appearance_domain() -> None:
    provenance = _provenance_fixture()
    provenance["requested"]["appearance"]["enabled"] = False
    for attempt in provenance["attempts"]:
        attempt["appearance_domain_index"] = 0
        attempt["appearance_seed"] = None

    validated = validate_domain_provenance(provenance)

    assert {attempt["appearance_domain_index"] for attempt in validated["attempts"]} == {0}


def test_sidecar_validation_rejects_bad_commit_order_or_runtime_values() -> None:
    bad_commit_order = _provenance_fixture()
    bad_commit_order["attempts"][1]["committed_episode_index"] = 2
    with pytest.raises(DomainProvenanceError, match="dataset commit order"):
        validate_domain_provenance(bad_commit_order)

    bad_camera = _provenance_fixture()
    bad_camera["attempts"][0]["actual"]["world_camera_pose"]["pos"] = [0.5, -0.5]
    with pytest.raises(DomainProvenanceError, match="camera pos"):
        validate_domain_provenance(bad_camera)

    bad_friction = _provenance_fixture()
    bad_friction["attempts"][0]["actual"]["friction_ratio"] = 1.5
    with pytest.raises(DomainProvenanceError, match="friction ratio.*outside"):
        validate_domain_provenance(bad_friction)


def test_domain_split_modes_make_domain_overlap_explicit() -> None:
    records = committed_episode_records(_provenance_fixture())

    in_distribution = plan_domain_split(
        records, eval_fraction=0.5, mode="in_distribution"
    )
    held_out = plan_domain_split(records, eval_fraction=0.5, mode="held_out_domain")

    assert in_distribution["train_episode_ids"] == [0, 2]
    assert in_distribution["eval_episode_ids"] == [1, 3]
    assert in_distribution["train_domain_ids"] == [0, 1]
    assert in_distribution["eval_domain_ids"] == [0, 1]
    assert in_distribution["overlapping_domain_ids"] == [0, 1]
    assert held_out["train_episode_ids"] == [0, 1]
    assert held_out["eval_episode_ids"] == [2, 3]
    assert held_out["train_domain_ids"] == [0]
    assert held_out["eval_domain_ids"] == [1]
    assert held_out["overlapping_domain_ids"] == []


def test_domain_split_validator_rejects_episode_or_required_domain_overlap() -> None:
    records = committed_episode_records(_provenance_fixture())

    with pytest.raises(DomainProvenanceError, match="episode overlap"):
        validate_domain_split(records, [0, 1], [1, 2, 3])
    with pytest.raises(DomainProvenanceError, match="domain overlap"):
        validate_domain_split(
            records,
            [0, 2],
            [1, 3],
            require_disjoint_domains=True,
        )


def test_domain_split_requires_provenance_and_multiple_domains(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="provenance not found"):
        load_domain_provenance(tmp_path)

    provenance = copy.deepcopy(_provenance_fixture())
    for attempt in provenance["attempts"]:
        attempt["appearance_domain_index"] = 0
        attempt["appearance_seed"] = 20
    provenance["requested"]["appearance"]["rebuild_every"] = 10
    records = committed_episode_records(provenance)

    with pytest.raises(DomainProvenanceError, match="at least two distinct"):
        plan_domain_split(records, mode="held_out_domain")


def test_in_distribution_split_requires_repeated_episodes_per_domain() -> None:
    records = committed_episode_records(_provenance_fixture())
    records[-1]["appearance_domain_index"] = 2

    with pytest.raises(DomainProvenanceError, match="at least two episodes in every"):
        plan_domain_split(records, mode="in_distribution")
