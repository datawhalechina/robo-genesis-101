# Setup and Fallback Paths

This appendix separates installation, lesson-completion paths, and diagnostics. A
dependency resolver finishing successfully is not GPU verification, and a diagnostic
branch is not automatically a substitute for the experiment that a lesson asks you to
complete. Exact verified platforms and wheel checksums remain in the
[compatibility matrix](https://github.com/datawhalechina/robo-genesis-101/blob/main/COMPATIBILITY.md).

## Choose the environment you need

### Documentation only

Use Node.js 24, the major version used by documentation CI:

```sh
npm ci
npm run docs:dev
```

Build the static site with `npm run docs:build`.

### Lightweight repository validation

This environment omits Genesis, PyTorch, LeRobot, and the training stack. It is for
course contracts, pure-logic tests, and source checks:

```sh
UV_PROJECT_ENVIRONMENT=.venv uv sync --only-group dev --locked
uv pip install --python .venv/bin/python --no-deps --editable .
.venv/bin/python -m robo_genesis.course_validation
.venv/bin/python -m pytest
```

It cannot execute simulation, rendering, data collection, training, or closed-loop
evaluation.

### Complete core-course environment

Install the portable dependency set with:

```sh
uv sync --locked --all-extras
uv run python -m robo_genesis.setup_assets
```

The second command verifies the four vendored YCB objects and returns their model
directory. The first command does not install or prove the separately tested AMD ROCm
wheel set. Follow the [compatibility matrix](https://github.com/datawhalechina/robo-genesis-101/blob/main/COMPATIBILITY.md) when reproducing
the reference AMD environment.

L14 is not part of this environment. It uses the pinned external companion runtime
described in the [L14 lesson](../lessons/l14-robotwin-lingbot-vla-fine-tuning.md).

## Workspace paths

The package resolves one workspace when its path module is first imported. Set path
variables before starting Python or a notebook kernel.

| Variable | Default | Purpose |
|---|---|---|
| `ROBO_GENESIS_ROOT` | current source checkout, otherwise the working directory | Base for relative overrides |
| `ROBO_GENESIS_ASSETS_DIR` | `<root>/assets` | Vendored and local assets |
| `ROBO_GENESIS_DATASETS_DIR` | `<root>/datasets` | Recorded or prepared LeRobot datasets |
| `ROBO_GENESIS_OUTPUTS_DIR` | `<root>/outputs` | Frames, training runs, reports, and videos |
| `ROBO_GENESIS_VIEWER` | `0` | Set to `1` only when a helper explicitly supports an interactive viewer |

Generated datasets, checkpoints, caches, videos, and logs stay outside Git. Use fresh
output names unless a lesson explicitly documents an overwrite opt-in.

## Runtime switches

The lesson notebooks validate these values instead of silently changing execution
paths:

| Variable | Accepted behavior |
|---|---|
| `ROBO_GENESIS_BACKEND=auto` | Select the verified AMD backend when available; otherwise select CPU |
| `ROBO_GENESIS_BACKEND=cpu` | Force the CPU path |
| `ROBO_GENESIS_RENDER=0` | Disable lesson camera work; whether this is a complete path depends on the lesson |
| `ROBO_GENESIS_RENDER=1` | Require the lesson's real Genesis camera path; rendering failures remain visible |

Restart the kernel after changing a runtime switch. PyTorch exposes ROCm devices through
the `torch.cuda` namespace; the namespace name alone does not prove that CUDA hardware is
being used.

Lesson-specific variables narrow an input or permit an explicit destructive replacement:

- `RG101_L09_OVERWRITE=1` allows replacement of the exact validated L09 output root.
- `RG101_L10_DATASET_ROOT` and `RG101_L10_REPO_ID` select one compatible local L10 input.
- `RG101_L11_BASELINE_ROOT`, `RG101_L11_DATASET_ROOT`, `RG101_L11_PREVIEW_ROOT`, and
  `RG101_L11_BASELINE_REPO_ID` select explicit L11 locations and identity.
- `RG101_L11_OVERWRITE=1` allows replacement of the exact validated L11 dataset and
  preview roots.
- L12 uses `RG101_REPO_ID`, `RG101_DATASET_ROOT`, `RG101_OUTPUT_ROOT`, `RG101_SEED`, and
  `RG101_RUN_SMOKE`; SmolVLA smoke additionally requires both pinned local snapshot paths.

Do not set an overwrite variable merely to bypass an unexplained collision. Inspect the
existing directory first.

## Lesson fallback matrix

| Lessons | Minimum useful path | What the fallback does not prove |
|---|---|---|
| L01–L07 | CPU execution is the accepted completion path. Rendering can be disabled where the lesson says the numerical path is complete. | A render `SKIP` is not camera evidence. |
| L08 | The scripted rollout and numerical evidence run on CPU; CPU+EGL and the reference AMD+EGL visual paths have also passed. | `ROBO_GENESIS_RENDER=0` does not produce the stage-image evidence. |
| L09 | CPU diagnostics check sampling and schema. The complete lab requires both real camera streams; CPU+EGL and reference AMD+EGL collection paths have passed. | `ROBO_GENESIS_RENDER=0` does not record a dataset or complete L09. |
| L10 | CPU readback of an existing compatible L09 dataset is the accepted path. | L10 does not generate fallback data, train a policy, or infer task success. |
| L11 | CPU diagnostics check configuration, seed schedules, guardrails, and commands. The complete bounded-DR lab requires rendering and recording; CPU+EGL and reference AMD+EGL paths have passed. | `ROBO_GENESIS_RENDER=0` does not create the randomized dataset, preview, or provenance result. |
| L12 | CPU dry-runs can validate data and command construction. Actual ACT/SmolVLA smoke training requires a GPU and audited inputs. | A dry-run, one-step loss, or open-loop reload is not policy quality or closed-loop success. |
| L13 | CPU/no-checkpoint diagnostics can audit configuration and local inputs. Course completion requires the GPU closed-loop protocol, structured reports, and real videos. | Open-loop action generation and a diagnostic report are not a completed closed-loop evaluation. |
| L14 | Only the pinned companion runtime and required 4-GPU W7900D profile are accepted for the practicum's required path. | There is no CPU, single-GPU, core-environment, or no-companion completion fallback. |

## Data and checkpoint handoffs

The default local handoffs are explicit:

- L09 writes `ROBO_GENESIS_DATASETS_DIR/l09_banana_demo` with logical ID
  `local/l09_banana_demo`.
- L10 reads that dataset without scanning for substitutes.
- L11 reads the L09 baseline and writes `l11_banana_dr` plus domain provenance.
- L12's verified training default is a separately prepared `genesis/fruit_pick` dataset,
  not the tiny L09 or L11 teaching dataset.
- L13 requires a dataset/checkpoint identity match before evaluation.

L13 contains commit-pinned, opt-in Hugging Face source declarations for its own workflow,
but M4 does not provide a general course artifact downloader. Versioned example datasets,
course checkpoints, checksums, and clean-environment download acceptance remain M5 work.
Until then, do not describe a locally prepared artifact as an official course release.

## Diagnose failures without hiding them

Classify a failure before changing the environment:

1. **Installation:** an import, locked dependency, or native library is missing.
2. **Backend:** the requested CPU or AMD device is unavailable or differs from the report.
3. **Rendering:** EGL, camera creation, or frame validation failed.
4. **Input identity:** a dataset, checkpoint, snapshot revision, schema, or repository ID does
   not match the command.
5. **Output safety:** the destination already exists or lies outside the allowed root.
6. **Task evidence:** the process ran, but success predicates, video, or report checks failed.

Do not replace a failed GPU run with an unannounced CPU result, fabricate a camera image,
or use training loss as a substitute for closed-loop task evidence. Record the requested
and actual backend, the exact input identity, the command, and every unrun check.

## Setup checklist

- The repository and selected lesson inputs are on local storage.
- Python is `3.12.x`, and the installed package versions match the compatibility record.
- `robo_genesis.setup_assets` validates all four vendored YCB objects.
- Dataset and output roots are writable and outside tracked source files.
- The notebook kernel was started after all environment variables were set.
- The requested backend and rendering path are visible in the first diagnostic output.
- GPU-required work has an audited GPU, dataset, and checkpoint rather than a silent
  diagnostic fallback.
- L14 is run only in its pinned external companion profile.
