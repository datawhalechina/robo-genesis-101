# API and Command Cheatsheet

Reusable behavior lives in `src/robo_genesis/`; notebooks are teaching entry points, not
independent implementations. This page lists the stable course-facing surfaces that the
lessons currently use. Read the linked source and the relevant lesson before changing a
protocol.

The package root exports only `__version__`. Import helpers from their defining modules.
Names beginning with `_` are implementation details and are intentionally omitted.

## Paths and diagnostics

| Surface | Purpose |
|---|---|
| [`ProjectPaths`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/paths.py), `resolve_project_paths()` | Resolve project, asset, dataset, and output roots from portable defaults and `ROBO_GENESIS_*` overrides. |
| `resolve_cli_path()` | Resolve a CLI path from the current working directory or an absolute default. |
| [`environment_report()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/course_utils.py) | Print Python, platform, Genesis, PyTorch/HIP, and accelerator identity. |
| `select_backend()` | Prefer verified AMD ROCm when available; otherwise return the Genesis CPU backend. |
| `to_numpy()` | Convert Genesis, Torch, or NumPy values to a detached CPU NumPy array. |
| `assert_pose_close()` | Validate a measured vector against a target and return the Euclidean error. |
| `notebook_mode()` | Create one output directory and resolve the optional viewer switch. |

Set path variables before importing `robo_genesis.paths`, because the module-level constants
are resolved at import time.

## Assets and scenes

| Surface | Purpose |
|---|---|
| [`setup_assets()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/setup_assets.py) | Validate the vendored YCB license/provenance files and SHA-256 manifest, then return the models directory. |
| [`build_scene()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/build_scene.py) | Build the course Franka/table/YCB scene with declared cameras, environment count, and optional build-time DR. |
| `SceneBundle` | Hold the scene, Franka entity, YCB entities, cameras, and table entities. Use `update_wrist_cam()` before wrist rendering. |
| `SceneDomainRandomizationConfig` | Configure build-time appearance and camera-intrinsic randomization; a new appearance domain requires a scene rebuild. |
| [`get_ycb_assets()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/scene_config.py) | Return audited YCB metadata derived from the configured models directory. |

Initialize Genesis exactly once per process before calling `build_scene()`. Cameras must be
added before `scene.build()`; a render-disabled branch must not fabricate replacement frames.

## Scripted task execution

| Surface | Purpose |
|---|---|
| [`TaskSpec`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/grasp_demo.py) | Declare `pick_object`, `place_target`, and `success_tol`. |
| `GraspProfile` | Store per-object top-down grasp parameters. |
| `run_pick_place()` | Execute the explicit scripted expert phases and optionally feed an episode recorder. |
| `check_success()` | Evaluate the shared horizontal-placement and below-rim containment predicate. |
| [`EpisodeRecorder`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/record_dataset.py) | Sample synchronized state, action, and camera observations during a scripted rollout. |
| `build_features()` | Construct the course LeRobot feature schema for a declared image size. |

Use the recorder CLI for normal dataset creation. Direct use of `EpisodeRecorder` is for
lesson-level inspection or an intentional extension that preserves the same timing contract.

## Domain randomization and provenance

| Surface | Purpose |
|---|---|
| [`DomainRandomizationConfig`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/randomize.py) | Configure per-episode runtime friction, mass, and world-camera extrinsic ranges. |
| `RandomizationConfig` | Configure pose/task randomization, settle steps, tolerance, seed, and nested runtime DR. |
| `EnvRandomizer` | Reset an already-built scene and sample one task/domain using an explicit seed. |
| [`validate_dr_collection_config()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/domain_provenance.py) | Validate the bounded collection contract before recording. |
| `plan_seed_schedule()` | Build the deterministic attempt and appearance-domain schedule. |
| `write_domain_provenance()` / `load_domain_provenance()` | Persist and validate machine-readable collection provenance. |
| `plan_domain_split()` / `validate_domain_split()` | Create or check a domain-aware dataset split. |

Build-time appearance DR and runtime DR are separate layers. Do not claim that changing one
layer exercises the other.

## Training, checkpoints, and evaluation

| Surface | Purpose |
|---|---|
| [`robo_genesis.train_policy`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/train_policy.py) | Thin CLI wrapper that builds audited ACT or SmolVLA `lerobot_train` commands. |
| [`audit_dataset_contract()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/evaluation_contract.py) | Check LeRobot identity, metadata, camera keys, state/action dimensions, and FPS before evaluation. |
| `validate_evaluation_protocol()` | Validate episode count, timing, objects, seeds, tolerance, and condition declaration. |
| `validate_action_vector()` / `normalize_policy_action()` | Reject wrong-shape or non-finite policy actions and normalize accepted outputs. |
| `build_evaluation_report()` / `validate_evaluation_report()` | Create and audit the structured closed-loop evidence report. |
| [`robo_genesis.eval_policy`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/eval_policy.py) | Load a supported policy and run the declared closed-loop protocol. |
| [`robo_genesis.eval_sweep`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/eval_sweep.py) | Evaluate numbered checkpoints under one fixed protocol and write JSON, CSV, and a curve. |
| [`wilson()` and `newcombe_diff()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/stats.py) | Compute the course's binomial interval and independent-proportion difference interval helpers. |

`train_policy` defaults to the PyAV dataset decoder. A successful command build, one training
step, or an open-loop reload proves interface integration only. Task-performance conclusions
come from the closed-loop protocol.

## L13 workflow helpers

[`l13_workflow.py`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/l13_workflow.py) keeps notebook orchestration
dependency-light until the evaluator process starts.

| Surface | Purpose |
|---|---|
| `prepare_l13_workflow()` | Resolve local inputs, output roots, and optional commit-pinned fallback declarations. |
| `audit_l13_inputs()` / `require_l13_inputs()` | Report or enforce dataset/checkpoint readiness. |
| `declare_l13_conditions()` | Validate reference and shifted/OOD condition declarations. |
| `build_l13_evaluation_command()` | Build the evaluator command without invoking a shell. |
| `run_l13_condition()` | Execute one declared condition with recorded environment overrides. |
| `audit_l13_evidence()` / `compare_l13_runs()` | Check reports/videos and compare results without overstating causal evidence. |
| `write_l13_capstone_report()` | Write JSON and Markdown Capstone evidence from audited runs. |

Hugging Face fallback resolution requires an exact repository ID, 40-hex commit, and
subfolder. Downloads are opt-in; an unresolved source remains unavailable rather than being
replaced by an unrelated local artifact.

## L14 isolated helpers

[`l14_workflow.py`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/l14_workflow.py) validates notebook-visible
configuration, paths, commands, checkpoint structure, logs, videos, and aggregate evidence.
It deliberately does not import, patch, or replace the external companion.

Common surfaces include `validate_l14_config()`, `l14_output_paths()`,
`audit_required_paths()`, `audit_hf_checkpoint()`, `build_single_task_eval_command()`,
`run_command_logged()`, `parse_final_success_rate()`, and
`build_aggregate_evidence_card()`.

These helpers are not a portable L14 runtime. The pinned companion commit and the required
4-GPU profile remain part of the lesson contract.

## Command entry points

Run `--help` before adapting a command:

```sh
uv run python -m robo_genesis.setup_assets
uv run python -m robo_genesis.build_scene --help
uv run python -m robo_genesis.grasp_demo --help
uv run python -m robo_genesis.record_dataset --help
uv run python -m robo_genesis.train_policy --help
uv run python -m robo_genesis.eval_policy --help
uv run python -m robo_genesis.eval_sweep --help
.venv/bin/python -m robo_genesis.course_validation
```

| Module | Normal role |
|---|---|
| `build_scene` | Scene/asset/camera smoke and build-time DR inspection |
| `grasp_demo` | One parameterized scripted pick-and-place execution |
| `record_dataset` | Transactional successful-episode recording into a local LeRobot dataset |
| `train_policy` | ACT or SmolVLA training command wrapper; arguments after `--` pass through to LeRobot |
| `eval_policy` | One checkpoint under one declared closed-loop condition |
| `eval_sweep` | Multiple numbered checkpoints under a matched protocol |
| `course_validation` | Bilingual structure, metadata, links, notebooks, source safety, and repository contracts |

## Minimal scene pattern

```python
import genesis as gs

from robo_genesis.build_scene import build_scene
from robo_genesis.course_utils import select_backend
from robo_genesis.grasp_demo import TaskSpec, check_success, run_pick_place

gs.init(backend=select_backend(), seed=0, precision="32", logging_level="warning")
bundle = build_scene(show_viewer=False, add_world_cam=False, add_wrist_cam=False)
task = TaskSpec(pick_object="011_banana", place_target="024_bowl")
run_pick_place(bundle, task)
print("success:", check_success(bundle, task))
```

This pattern executes a real task; it is not a substitute for lesson-specific traces,
dataset recording, or evaluation evidence.

