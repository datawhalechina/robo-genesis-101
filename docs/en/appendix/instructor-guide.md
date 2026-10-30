# Instructor Guide

RoboGenesis 101 is one progressive learning path: mechanism-level lectures establish the
ideas, notebooks expose the important code and evidence, and reusable implementations keep
cross-lesson behavior consistent. Do not teach the lecture and notebook as independent
tracks, or begin policy training before learners can audit the dataset contract.

The lesson durations in `course.json` are planning estimates, not measured classroom timing.
The schedule below is one suggested 12-week organization; instructors should adapt contact
hours without changing prerequisites or evidence standards.

## Learning outcomes

By the end of the 13-lesson core path, learners should be able to:

- diagnose a Genesis runtime and distinguish requested from actual backend behavior;
- build and inspect scenes, rigid-body interactions, robot control, IK, cameras, and batched
  environments;
- define a grasping task, execute a scripted expert, and state a machine-checkable success
  predicate;
- record and audit time-aligned LeRobot demonstrations;
- explain dataset samples, imitation-learning supervision, and domain provenance;
- construct and inspect ACT/SmolVLA training commands and checkpoints;
- run a declared closed-loop evaluation and separate integration evidence from task
  performance.

L14 is an optional advanced practicum. It does not change completion of the 13 core lessons.

## Suggested 12-week sequence

| Week | Material | Teaching emphasis | Required evidence |
|---:|---|---|---|
| 1 | L01 | Runtime identity, status/evidence levels, CPU versus AMD backend | Environment report and minimal-scene result |
| 2 | L02–L03 | Scene lifecycle, state reads, contact, friction, time step, controlled comparisons | Measured state and stable physics comparison |
| 3 | L04 | Robot model, DOF indexing, joint state, position/velocity/force control | Joint-command and measured-state checks |
| 4 | L05 | FK, IK, end-effector pose, and the role of cameras | Pose error plus explicit camera result or `SKIP` |
| 5 | L06 | Parallel environments, batched control, and selective update | Per-environment shapes, errors, and independence checks |
| 6 | L07 | Task scene, audited assets, task state, and success conditions | Scene/asset checks and task predicate reasoning |
| 7 | L08 | Demonstration methods, scripted expert phases, and rollout traces | Action/state trace, phase order, and outcome predicate |
| 8 | L09 | Sampling rates, temporal alignment, transactions, schema, and throughput | Readable dual-camera dataset and metadata audit |
| 9 | L10–L11 | Dataset anatomy, imitation learning, domain randomization, and provenance | Read-only dataset audit plus bounded DR evidence |
| 10 | L12 | ACT/SmolVLA inputs, training command, checkpoint, and open-loop reload | Dry-run and, on the GPU path, audited smoke checkpoint |
| 11 | L13 | Closed-loop protocol, videos, reports, uncertainty, and Capstone | Audited report/video and scoped conclusion |
| 12 | Core evidence review; optional L14 | Reproduce one vertical handoff; separately introduce the pinned RoboTwin/LingBot practicum when resources permit | Core acceptance packet, or L14 aggregate evidence within its fixed profile |

Use each lesson's metadata duration when planning sessions. If two lessons share a week,
split lecture, lab, and review across meetings or assign the notebook as supervised work.

## Hardware-aware delivery

### CPU-first foundation

L01–L07 and L10 have accepted CPU completion paths. They form a coherent simulation,
control, task, and dataset-reading foundation. This is the recommended shared path before
learners reserve GPU resources.

L08 can execute its scripted rollout and numerical evidence on CPU. L09 and L11 provide CPU
diagnostics, but their complete data-producing experiments require real camera rendering;
CPU+EGL and the reference AMD+EGL paths have passed. Use the
[setup and fallback appendix](setup-and-fallbacks.md) to label diagnostic and completion
paths accurately.

### GPU labs

L12 and L13 are `gpu-required`. Before the lab, verify:

- the actual accelerator name, PyTorch/HIP versions, and Genesis backend;
- the exact dataset repository ID and local root;
- checkpoint or model snapshot identity;
- local output capacity and a fresh run name;
- offline cache readiness when the exercise is meant to run without downloads.

Group learners around prepared machines when hardware is scarce. Assign roles such as
operator, protocol reviewer, artifact auditor, and evidence reviewer so that every learner
works with the full contract rather than only watching a progress bar.

L14 needs the separate pinned companion and four W7900D GPUs for its required path. Do not
install its stack into the core environment or advertise a CPU/single-GPU fallback.

## Artifact planning before M5

M4 does not publish a versioned example dataset, ACT/SmolVLA course checkpoint, or general
artifact downloader. An instructor who supplies local inputs before M5 should record:

- creator and source;
- immutable revision or generation command;
- dataset repository ID, schema, and local root;
- model/checkpoint configuration and base-model provenance;
- license and redistribution decision;
- file size and SHA-256 when the artifact is distributed;
- which lessons and checks the artifact actually supports.

Call these instructor-prepared inputs, not official RoboGenesis releases. Never rehost the
LingBot-VLA-v2 base model, RoboTwin dataset, or L14 image as a convenience copy.

## Lab operating pattern

Use the same pattern for each executable lesson:

1. **Predict:** learners state the expected shape, physical relationship, or failure mode.
2. **Preflight:** verify versions, backend, inputs, and output destination.
3. **Run:** execute from a clean kernel or fresh process without hidden state.
4. **Inspect:** examine measured values, images/video, metadata, and structured reports.
5. **Explain:** connect the evidence to the mechanism and identify what was not tested.
6. **Extend:** change one declared factor while holding the rest of the protocol fixed.

Genesis initialization is process-wide. Lessons that isolate cases in subprocesses should
remain isolated; do not simplify them into repeated incompatible initialization inside one
kernel.

## Evidence and grading

Grade the strongest claim a learner actually supports:

| Evidence level | Acceptable claim | Insufficient substitute |
|---|---|---|
| Diagnostic | Configuration, input, schedule, or command checks passed | Claiming that the core experiment ran |
| Numerical simulation | Declared state/control/physics relationships passed | Claiming camera or task evidence without frames/outcomes |
| Data pipeline | Dataset committed and read back with matching schema and timing | Claiming that the dataset trains a capable policy |
| Training integration | Real optimization and checkpoint save/reload worked | Treating loss or open-loop actions as task success |
| Closed-loop task | Declared episodes ran with valid actions, termination reasons, reports, and videos | Generalizing a small `k/n` to robust policy quality |
| Comparative result | Conditions share the declared comparison protocol and uncertainty is reported | Calling independent aggregates paired or causal |

A passing report states seeds, requested/actual backend, input identity, protocol, result
counts, failure categories, artifacts, and unrun work. Visual inspection may detect corrupted
or empty videos, but it must not overwrite the evaluator's success labels.

## Common misconceptions to correct

- `torch.cuda` is the compatibility namespace used by ROCm; inspect `torch.version.hip` and
  the actual device.
- A notebook reaching its last cell does not prove every optional or skipped branch ran.
- An action tensor and measured joint state can share a shape without representing the same
  quantity.
- A local path is not a dataset repository ID or artifact version.
- Domain randomization without provenance is not reproducible evidence.
- A shifted condition is not OOD unless it is shown outside declared training support.
- One-step training, falling loss, and open-loop reload are not closed-loop success.
- Matched scheduled seeds do not control factors that the seed does not determine.
- A `gpu-verified` lesson is not automatically `published`.

## Instructor preparation checklist

- Read the lecture and notebook together, including prerequisites and failure branches.
- Run the lesson's minimum path from a clean kernel on the machine learners will use.
- Verify local links, dataset/checkpoint identities, and available disk space.
- Decide which visual evidence is required and test the real camera/video path.
- Prepare a fresh output root; do not reuse learner-visible results as if newly generated.
- Record every hardware-intensive or external-download step that will not run in class.
- Keep L14 scheduling, environment, storage, and conclusions separate from the core path.
- Review the [references and license audit](../references/) before distributing any external
  material.

## Course completion review

Before marking a cohort complete, confirm that learners can trace at least one vertical path
from task specification to demonstration, dataset, checkpoint, and closed-loop report. The
artifacts may come from separate labs, but their identities and interfaces must be explicit.

Course completion does not authorize changing canonical repository status. `course.json`
changes only after the repository's own evidence and acceptance gates pass.

