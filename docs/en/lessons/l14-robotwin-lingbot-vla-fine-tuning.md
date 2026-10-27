---
lesson: L14
slug: robotwin-lingbot-vla-fine-tuning
locale: en
title: "Optional Advanced Practicum: Fine-Tuning LingBot-VLA-v2 with RoboTwin Data"
duration_minutes: 180
hardware: gpu-required
status: planned
---

# L14 · Optional Advanced Practicum: Fine-Tuning LingBot-VLA-v2 with RoboTwin Data

> **Course status:** `planned`. This lecture explains the reviewed L14 workflow,
> but the bilingual notebook, course-side helpers, and required four-GPU execution
> evidence have not been delivered yet. Do not treat the commands below as a
> RoboGenesis-verified run or the cited competition measurements as course results.

## Where this practicum fits

[L10](/en/lessons/l10-dataset-anatomy-and-imitation-learning) made LeRobot
features, episode metadata, normalization statistics, and action chunks
inspectable. [L12](/en/lessons/l12-act-and-smolvla-policy-training) connected
an action expert and flow-matching objective to training and checkpoint
evidence. [L13](/en/lessons/l13-closed-loop-evaluation-and-capstone) then froze
an evaluation protocol before comparing task outcomes.

L14 applies those ideas to the path-validated competition reference in the
pinned
[`Robotwin-radeon-cloud`](https://github.com/ZiguanWang/Robotwin-radeon-cloud/tree/27b2f6fcb6c715e2cbb6db4431381f87c94b86ed)
companion:

```text
RoboTwin demo_clean data
        ↓
50 LeRobot v3 task datasets + LingBot training contract
        ↓
base-model closed-loop evaluation
        ↓
4-GPU action-expert LoRA → distributed checkpoint (DCP)
        ↓
merge into a deployable Hugging Face checkpoint
        ↓
merged-model aggregate evaluation → scoped evidence card
```

The same source notebook also covers an official RoboTwin post-training
checkpoint, 4/8-GPU 1,000-episode benchmarks, merged-LoRA benchmarking, and a
full-parameter SFT path with depth/video teachers. Those sections remain part
of this lesson. They are explicit, high-cost competition extensions rather than
requirements for the 180-minute route.

![The complete L14 competition workflow keeps the base and official checkpoints, required LoRA path, optional 4/8-GPU benchmarks, and full-parameter SFT in one technical map. The blue lane is the required 180-minute route; purple branches are retained competition extensions.](/diagrams/l14-competition-training-paths.svg)

*Course-created diagram. Every branch from the source notebook remains visible;
an optional branch is not evidence that RoboGenesis executed it.*

### Hardware and runtime boundary

The complete required run has a strict minimum:

- four AMD Radeon Pro W7900 GPUs with 48 GiB each;
- the pinned companion container/runtime and mounted model/data content;
- Python 3.12, PyTorch 2.9.1, and ROCm 7.2.1 as defined by that companion;
- EGL rendering, MPLib end-effector planning, and CuRobo disabled;
- persistent writable storage under `/workspace/runtime`; and
- no CPU, single-GPU, or no-cloud completion fallback.

PyTorch still uses the device string `cuda` on ROCm builds. That string is an
API compatibility name; the environment evidence must show HIP and the actual
AMD devices.

The eight-GPU profile is preserved because it belongs to the competition
reference. It is not the minimum course contract, and an eight-GPU result does
not replace verification of the required four-GPU path.

### A focused 180-minute route

The clock below covers instruction and audits. It excludes image construction,
first model/data preparation, server startup waits, and training wall time.

| Time | Topic | Learner output |
|---:|---|---|
| 0–10 min | Positioning, hardware gate, and evidence boundaries | Separate pipeline completion from a policy-quality claim |
| 10–30 min | Source, model, data, GPU, backend, port, storage, and output preflight | Produce a structured PASS/FAIL identity report |
| 30–50 min | RoboTwin → LeRobot v3 → LingBot data contract | Audit one task dataset and the 50-entry training manifest |
| 50–75 min | Base server and ten-episode evaluation protocol | Freeze checkpoint, expert, seed, video, and denominator semantics |
| 75–105 min | Action-expert LoRA, batch arithmetic, and FSDP2 | Explain the update scope and audit the four-GPU command |
| 105–130 min | DCP identity and Hugging Face merge | Distinguish a training checkpoint from a serving artifact |
| 130–155 min | Merged-model evaluation and aggregate comparison | Preserve independent run identities, logs, videos, and denominators |
| 155–175 min | Wilson intervals and evidence card | Write a scoped 10+10-episode conclusion and mark matched outcomes unavailable |
| 175–180 min | Summary and one-variable extension design | Register a follow-up without mixing it into the core denominator |

The official checkpoint, full 1,000-episode benchmarks, eight-GPU profiles,
longer LoRA runs, and full SFT remain documented after the required route. They
can take hours and substantial persistent storage.

## Learning objectives

By the end of L14, you should be able to:

1. explain how RoboTwin demonstrations become training inputs for
   LingBot-VLA-v2;
2. configure and compare action-expert LoRA and full-parameter SFT for VLA
   fine-tuning;
3. convert distributed training checkpoints into deployable Hugging Face
   models and serve them for inference; and
4. compare base and fine-tuned policies under a controlled closed-loop
   evaluation and report appropriately scoped conclusions.

## Evidence levels and experiment identities

L14 crosses several evidence levels. Do not collapse them into a single
"training worked" statement.

| Evidence | What it establishes | What it does not establish |
|---|---|---|
| Source/data preflight | the declared revisions and required inputs are present | that the policy can complete a task |
| One optimizer update or 100-step run | data loading, forward/backward, update, and DCP saving execute | convergence or useful fine-tuning quality |
| DCP audit and merge | the training artifact can be converted with the declared base/config | that the merged policy behaves better |
| Server health | the selected checkpoint loads and answers the health endpoint | correct action semantics or task success |
| Closed-loop `k/n` and episode rows | observed outcomes under one frozen protocol | a stable benchmark, untested tasks, or sim-to-real performance |
| 1,000-episode benchmark | broad task coverage for one declared checkpoint/protocol | fairness across changed revisions or hidden retry policies |

Each run therefore needs an identity, not merely a directory name. At minimum,
record companion and upstream revisions, checkpoint path/revision, training
config, task/config, CLI and resolved seeds, GPU profile, backend flags, video
choice, output root, and whether the run started fresh or resumed.

## Preflight: fail before consuming GPUs

Run one structured preflight before model serving, evaluation, or training. A
failed infrastructure check aborts the run; it is not a failed policy episode.

### Source and software identity

The reviewed input is companion commit
`27b2f6fcb6c715e2cbb6db4431381f87c94b86ed`, which pins:

| Component | Reviewed identity |
|---|---|
| RoboTwin | `266f3aadf505a4f7fe9af0faa41a20f5f47cd123` |
| XPolicyLab | `c37109c500be67d0dea6b36bf7337bbd26e763cd` |
| LingBot-VLA-v2 source | `951475ae1b1d87553e7dc47c97b53a3d695c0d13` |
| LingBot-VLA-v2 6B base model | `11c703bf6a5c1f45b3b69168482da11fdbba53d7` |
| RoboTwin2.0 data | `a967b852afa21a9cbf19a198f7e653109042e87c` |
| LeRobot | `0.6.0` |

Dependency resolution is not runtime verification. The preflight must also
show Python, PyTorch, `torch.version.hip`, LeRobot, visible device count and
names, per-device memory identity, `/dev/kfd`, `/dev/dri`, EGL, and a small ROCm
tensor operation.

### Paths, storage, port, and fresh outputs

The companion uses container paths intentionally:

```text
/RoboTwin                  source, assets, converted data, experiment scripts
/models/robotwin-persistent mounted model and persistent input content
/workspace/runtime         logs, checkpoints, evaluations, videos, evidence
```

Confirm that port `13400` is free, `/workspace/runtime` is writable, and the
new run names do not collide with old artifacts. Record free space for `/`,
`/workspace`, and the runtime output root. L14 does not publish a RoboGenesis
minimum-storage number until the four-GPU verification step measures it.

Never let a teaching notebook silently delete previous outputs. The retained
full-SFT storage cell will list exact cleanup candidates and perform a dry run;
deletion requires an explicit learner decision after final artifacts are
copied to persistent storage.

## RoboTwin data becomes a LingBot training contract

The companion image downloads the pinned `demo_clean` data for 50 tasks and
converts each task independently with XPolicyLab's LeRobot v3 converter:

```text
data/demo_clean/<task>
        ↓ transform_lerobot_v30_format.py
data/lerobot/<task>_joint_v30
        ↓ one manifest entry per dataset
data/robotwin_demo_clean_joint_v30.txt
```

The manifest is a 50-line list of dataset locations, not a single dataset
directory. `adjust_bottle_joint_v30` is one member of that list. The converter
limits each source task to 50 episodes in the reviewed build and writes H.264
media with a LeRobot-compatible reader backend.

![Fifty RoboTwin demo_clean task directories are converted into independent LeRobot v3 datasets. Their metadata, three camera streams, semantic joint groups, normalization statistics, and a 50-entry manifest jointly define the LingBot training input rather than any one filename or maximum dimension.](/diagrams/l14-robotwin-data-contract.svg)

*Course-created diagram. The audit follows actual metadata and config; it does
not infer tensor shapes from dataset names.*

### Three cameras, two naming layers

The training YAML declares three logical streams:

- `camera_top`;
- `camera_wrist_left`; and
- `camera_wrist_right`.

The direct policy request built by the RoboTwin evaluation patch uses:

- `observation.images.cam_high` from `head_camera`;
- `observation.images.cam_left_wrist` from `left_camera`; and
- `observation.images.cam_right_wrist` from `right_camera`.

Those names belong to different interfaces. Audit the converter metadata and
the serving adapter instead of assuming that similar camera labels are
interchangeable.

### Semantic groups are not storage-shape guesses

The LingBot training YAML declares:

```text
arm.position      14
end.position      14
effector.position  2
max_state_dim     55
max_action_dim    55
```

An inference probe in the companion uses a 14-D state, while the converter's
joint padding follows its conversion configuration. These facts are not a
contradiction: semantic groups, stored feature shape, and model capacity are
different layers.

The notebook audit must report all of them separately:

1. the actual LeRobot feature shapes and dtypes from `meta/info.json`;
2. the semantic group sizes from `lingbotvla_cli.yaml`;
3. the converter's joint layout and padding target;
4. `max_state_dim` and `max_action_dim` as model capacities; and
5. whether every required group has matching normalization statistics in
   `robotwin.json`.

## Base model and official RoboTwin checkpoint have different roles

The companion contains two important checkpoint roles:

| Checkpoint | Role in this lesson | Training use |
|---|---|---|
| `robbyant/lingbot-vla-v2-6b` base | deployment and pipeline reference; initialization for LoRA/full SFT | required starting point |
| official RoboTwin post-training checkpoint | optional effect-validation and benchmark reference | evaluation only; never initialize the competition reproduction from it |

The official RoboTwin checkpoint path remains in the notebook, but its exact
artifact revision must be pinned before that optional path is described as
RoboGenesis-verified or the lesson advances beyond `planned`. This provenance
requirement does not block implementing or teaching the base-to-LoRA/full-SFT
workflow.

### Start one server, then wait for health

The companion launches the selected model on GPU 0 and port 13400:

```bash
bash /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/scripts/launch_official_server.sh \
  0 13400 /workspace/runtime/outputs/logs/base_server.log False \
  /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/models/robbyant_lingbot-vla-v2-6b
```

Do not begin evaluation merely because the process exists. Poll
`http://127.0.0.1:13400/healthz`, fail if the process exits, and preserve the
server log. Before changing checkpoints or starting training, stop the server
process group and confirm that GPU memory and the port are released.

## Freeze the closed-loop protocol before running it

The required base and merged evaluations use the same protocol:

| Field | Required value or rule |
|---|---|
| Task/config | `adjust_bottle` / `demo_clean` |
| Policy/protocol | `LingBot-VLA-v2` / `lingbot_vla_v2` |
| Episodes | 10 base + 10 merged |
| CLI seed | `0`, while recording each actual resolved episode seed |
| Expert | `expert_check=true`, `accept_expert_info_on_failure=true` |
| Backend | EGL, MPLib, `ROBOTWIN_DISABLE_CUROBO=1` |
| Evaluation | `eval_batch=false` and the same timeout/control/success implementation |
| Video | explicitly enabled for the required 10+10 evidence path |
| Outputs | separate fresh base and merged directories; no successful-retry replacement |

The companion reference disables video by default to reduce encoding and disk
I/O. Keep the switch explicit. Single-task evaluation uses
`eval_video_log=true|false`; the benchmark script uses `--video|--no-video`.
Deleting an argument is not equivalent because entry-point defaults differ.

A representative command shape is:

```bash
ROBOTWIN_DISABLE_CUROBO=1 \
ROBOTWIN_EE_PLANNER=mplib \
PYOPENGL_PLATFORM=egl \
/opt/robotwin-env/bin/python /RoboTwin/scripts/eval_policy_xpolicylab.py \
  --task_name adjust_bottle \
  --task_config demo_clean \
  --policy_name LingBot-VLA-v2 \
  --protocol lingbot_vla_v2 \
  --host 127.0.0.1 \
  --port 13400 \
  --device_id 0 \
  --seed 0 \
  --seed_start 100000 \
  --test_num 10 \
  --expert_check true \
  --accept_expert_info_on_failure true \
  --eval_batch false \
  --additional_info eval_video_log=true
```

### Expert information and the denominator

`expert_check=true` asks the environment to prepare expert information before
the policy rollout. `accept_expert_info_on_failure=true` keeps that information
available even when the expert plan/task check fails instead of silently
filtering such seeds. The course keeps the companion's unmodified serial
evaluator and wraps it with a course-side collection loop.

During the course's four-GPU W7900 validation run, the serial
`eval_batch=false` loop exposed an important denominator mismatch. A requested
slot is consumed after the expert check but before the second environment
setup. If that second setup is unstable, the serial evaluator can complete
fewer policy episodes while still printing the requested denominator—for
example, five completed episodes followed by a fixed `Final success rate:
0/10`.

The notebook therefore reads the last incremental `Success rate: k/n` line,
which reflects the policy episodes that actually completed in that invocation.
If `n` is smaller than the requested slot count, it starts another serial
invocation for exactly the remaining number of episodes and advances
`--seed_start` by the preceding requested range. Each invocation has its own raw
log, and its videos are archived immediately under an invocation-specific
directory. This keeps invocation boundaries explicit even though each source
directory may begin again at the `episode0.mp4` basename. A versioned
attempts JSON and a synthesized aggregate summary record the requested slots,
completed count, and archived video paths. Collection stops only when exactly
ten policy episodes and ten newly archived videos are present. An infrastructure
failure that exits the evaluator still aborts the run. No companion source file
is modified.

The current pinned companion does not yet emit per-resolved-seed policy outcomes
in the deferred JSONL schema. The course-side attempts JSON is invocation-level
collection evidence, not a substitute for those episode rows. The notebook
therefore completes the full LoRA/full-SFT workflow without changing the
companion and reports base and merged results as independent aggregate
observations. Per-attempt JSONL remains a future evidence enhancement; its
absence limits comparison claims but does not block training, conversion,
serving, or aggregate closed-loop evaluation.

## Optional 100-task × 10-episode benchmarks

The benchmark script covers 50 clean and 50 randomized tasks, ten episodes per
task. With four or eight selected GPUs, it launches one model server and one
evaluation worker per GPU and assigns the next unfinished task from a shared
queue. `--resume` skips task completion markers in the same run directory;
change `--run-name` for an independent rerun. The course notebook defaults
each benchmark resume switch to `False`, rejects an existing output directory,
and requires an explicit opt-in to resume an already identified run.

The pinned companion notebook reports the following wall-clock observations.
They are **upstream competition-reference measurements**, not RoboGenesis
compatibility evidence, and success-rate details are intentionally absent:

| Machine | Config | Completion | Reported wall time |
|---|---|---:|---:|
| 4 × W7900 | clean | 50 tasks / 500 episodes | 8 h 26 min 41 s |
| 4 × W7900 | randomized | 50 tasks / 500 episodes | 10 h 29 min 07 s |
| 4 × W7900 | total | 100 tasks / 1,000 episodes | 18 h 55 min 48 s |
| 8 × W7900 | clean | 50 tasks / 500 episodes | 6 h 34 min 23 s |
| 8 × W7900 | randomized | 50 tasks / 500 episodes | 8 h 37 min 58 s |
| 8 × W7900 | total | 100 tasks / 1,000 episodes | 15 h 12 min 21 s |

These are end-to-end task timings, not linear model-throughput benchmarks. Task
durations vary, so the slowest remaining task determines the queue tail. Use
different run identities for the base model, official RoboTwin checkpoint,
merged LoRA, and full-SFT model.

## Action-expert LoRA on four GPUs

LoRA represents a trainable update to a frozen weight matrix as a low-rank
product:

```text
W' = W + (α / r) B A

A ∈ R^(r × d_in), B ∈ R^(d_out × r), r ≪ min(d_in, d_out)
```

The required configuration uses rank `r=8`, alpha `16`, scope
`action_expert`, and targets `q_proj,k_proj,v_proj,o_proj`. It therefore trains
low-rank attention-projection updates in the action expert rather than treating
"LoRA" as an update to every model weight.

![The base vision-language model remains the reference while rank-8 LoRA matrices update q, k, v, and o projections in the action expert. Four W7900 workers each process micro batch one; FSDP2 shard size four and accumulation one give global batch four. An optional eight-GPU profile raises the global batch to eight.](/diagrams/l14-action-expert-lora.svg)

*Course-created diagram. The rank and batch numbers are configuration, not a
claim about learned quality.*

### Batch arithmetic must close

```text
global batch
  = micro batch per GPU
  × data-parallel process count
  × gradient accumulation
```

| Profile | Micro batch | Processes/shard size | Accumulation | Global batch |
|---|---:|---:|---:|---:|
| Required course path | 1 | 4 | 1 | 4 |
| Optional competition profile | 1 | 8 | 1 | 8 |

The YAML contains generic defaults, but the launcher overrides shard size,
accumulation, global batch, steps, save interval, and output directory. Audit
the resolved command, not just the YAML file.

### Three attention settings have different owners

| Setting | Owner and role |
|---|---|
| `model.attn_implementation=flash_attention_2` | Hugging Face/Qwen model attention |
| `model.vit_attn_implementation=flash_attention_2` | vision encoder attention |
| `train.attention_implementation=flex_cached` | joint VLM/action-expert attention with a custom 2-D block mask |

Replacing the third setting with `flash_attention_2` is not an optimization;
the reviewed path rejects it as an invalid implementation for that custom mask.

### Required four-GPU smoke command

The teaching path uses the companion's fixed Python interpreter instead of an
ambiguous `torchrun` from `PATH`:

```bash
cd /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/source/lingbot-vla-v2

export HIP_VISIBLE_DEVICES=0,1,2,3
unset ROCR_VISIBLE_DEVICES CUDA_VISIBLE_DEVICES

/opt/robotwin-env/bin/python -m torch.distributed.run \
  --standalone \
  --nproc-per-node=4 \
  -m tasks.vla.train_lingbotvla \
  /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/training/lingbotvla_cli.yaml \
  --train.data_parallel_shard_size 4 \
  --train.gradient_accumulation_steps 1 \
  --train.global_batch_size 4 \
  --train.max_steps 100 \
  --train.save_steps 100 \
  --train.output_dir /workspace/runtime/outputs/lora_100steps_4gpu
```

The course run also freezes training seed `42` in the resolved configuration.
The committed notebook will make that identity visible before execution.

One hundred steps test data loading, distributed forward/backward, optimizer
updates, DCP saving, merge, load, and evaluation plumbing. They do not establish
loss convergence or policy improvement. The companion suggests 1,000–5,000
steps as experiment scales, but checkpoint choice still requires held-out
closed-loop evidence rather than selecting the longest run automatically.

## DCP is a training artifact; Hugging Face is the serving artifact

FSDP2 writes a distributed checkpoint whose state is partitioned across ranks.
It may contain sharded model state, optimizer state, scheduler/RNG state,
dataloader state, and the resolved training configuration. A server cannot be
pointed at that directory as if it were a normal Hugging Face model.

![Four training ranks write DCP shards and a resolved training identity. The LoRA path validates the base model, rank, alpha, and adapter state before merging them into a fresh Hugging Face directory. Config, processor, safetensor index, weight references, and a health check gate serving.](/diagrams/l14-dcp-to-hf-merge.svg)

*Course-created diagram. Full SFT uses a gather/convert operation instead of
the LoRA adapter merge shown here.*

For LoRA, the conversion identity is:

```text
global_step_100 DCP
  + exact base model
  + action-expert LoRA rank 8 / alpha 16
  + saved training config
  → fresh merged Hugging Face checkpoint
```

The pinned merge entry point is:

```bash
/opt/robotwin-env/bin/python \
  /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/scripts/merge_lora_dcp.py \
  --checkpoint /workspace/runtime/outputs/lora_100steps_4gpu/checkpoints/global_step_100 \
  --training-output /workspace/runtime/outputs/lora_100steps_4gpu \
  --base-model /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/models/robbyant_lingbot-vla-v2-6b \
  --output /workspace/runtime/outputs/lora_100steps_4gpu/merged_checkpoint/global_step_100/hf_ckpt \
  --rank 8 \
  --alpha 16
```

Before serving, audit at least:

- DCP and saved training-config existence;
- the exact base checkpoint used for initialization;
- LoRA scope, target modules, rank, and alpha;
- a fresh output directory;
- model config and processor assets;
- `model.safetensors.index.json` and every referenced shard; and
- a health check after launching the merged checkpoint.

## Compare base and merged checkpoints by resolved seed

This section defines the stronger comparison protocol to use once final
per-resolved-seed outcomes are available. The current pinned companion cannot
perform this join: the notebook reports the two `k/n` values and Wilson
intervals, marks matched outcomes as unavailable, and does not infer seed
identity from episode index.

Stop the training processes, launch the merged checkpoint on the same GPU,
port, and flags as the base checkpoint, then repeat ten episodes. Checkpoint
identity is the intended variable; task, config, evaluator, expert semantics,
backend, video setting, and output schema stay fixed.

The evaluator starts from a seed derived from CLI `--seed 0`, but an unstable
setup can advance the seed. Match rows by the actual key:

```text
(task_name, task_config, resolved_seed)
```

not by episode index.

![Base and merged checkpoints pass through the same frozen server and evaluation protocol. Counted episode rows are joined by task, config, and actual resolved seed, producing unchanged success, unchanged failure, failure-to-success, and success-to-failure counts plus unmatched seed sets.](/diagrams/l14-matched-checkpoint-evaluation.svg)

*Course-created diagram. Missing seeds remain visible; they are not repaired by
pairing unrelated episode indices.*

For a checkpoint with `k` observed successes in `n=10` counted episodes,
report the raw count and a 95% Wilson interval. Then classify matched rows as:

- `unchanged-success`;
- `unchanged-failure`;
- `failure-to-success`; or
- `success-to-failure`.

If seed sets differ, compare only the intersection and report base-only and
merged-only seeds. Mark the complete matched comparison as unsatisfied. Do not
replace a failed row with a successful retry or pool a new run into the old
denominator.

The current aggregate evidence card must reconcile:

- base and merged `k/n`;
- both Wilson intervals;
- checkpoint and run identities;
- raw logs and the available videos; and
- limitations, including 100-step training and 10+10 small samples.

Because the unchanged evaluator writes below its shared `eval_result` tree,
the notebook snapshots MP4 metadata immediately before each required run and
copies only new or replaced videos into condition-specific directories under
the fresh course run. This preserves separate base and merged evidence without
changing the companion evaluator.

After the companion gains final per-attempt outcomes, the enhanced card should
also reconcile counted rows, setup attempts, matched outcome changes,
unmatched seed sets, and JSONL rows against actual video paths.

Even if the merged count is higher, the correct conclusion is an observation
about this run, not that 100-step LoRA has established a generally better
RoboTwin policy.

## Full-parameter SFT is a separate training path

Full SFT does not continue from the LoRA adapter. It sets `use_lora=false` and
updates all trainable model parameters. The retained default competition path
also enables current/future depth and video-teacher supervision.

| Dimension | Action-expert LoRA | Full-parameter SFT |
|---|---|---|
| Updated weights | rank-8 updates on action-expert `q/k/v/o` projections | all trainable model parameters |
| Core course budget | 4 GPUs, global batch 4, 100-step pipeline smoke | optional; not required for the 180-minute route |
| Default teacher | none | complete depth/video teacher |
| Training checkpoint | DCP plus LoRA adapter state/config | full-model and optimizer DCP |
| Deployment conversion | merge adapter into the exact base | gather/convert full trained model; no adapter merge |
| Storage/compute | lower | substantially higher |

The full teacher needs the LingBot depth asset, MoGe teacher asset, and DINO
video checkpoint/config. It adds alignment heads used during training. The
deployment patch filters those training-only heads while keeping strict checks
for inference weights.

### Global batch 256 on four or eight GPUs

The retained validated profiles use micro batch 16:

```text
4 GPU: 16 × 4 × 4 accumulation = 256
8 GPU: 16 × 8 × 2 accumulation = 256
```

`enable_full_shard=true` maps to FSDP2 `reshard_after_forward=true`. Each
wrapped module is sharded again after forward, reducing peak memory but
requiring another all-gather before backward. `false` retains full parameters
through backward; it may reduce communication but usually costs more peak
memory. It does not disable FSDP2.

### Companion capacity measurements, not course verification

The following table is retained from the pinned competition notebook because
it documents the tested capacity envelope. It enabled the full depth/video
teachers, gradient checkpointing, and FSDP2 full-shard. "Steady" is the mean of
optimizer steps 2 and 3; VRAM was sampled once per second. These values are
**attributed companion measurements**, not claims about a RoboGenesis run:

| Platform | Micro batch/GPU | Accumulation | Reported steady step | Reported peak VRAM/GPU | Source result |
|---|---:|---:|---:|---:|---|
| 4 × W7900 48 GiB | 1 | 64 | 245.580 s | 40.329–40.375 GiB | passed |
| 4 × W7900 48 GiB | 2 | 32 | 136.748 s | 41.337–41.349 GiB | passed |
| 4 × W7900 48 GiB | 4 | 16 | 76.010 s | 43.509–43.521 GiB | passed |
| 4 × W7900 48 GiB | 8 | 8 | 54.031 s | 47.729–47.761 GiB | passed; limited headroom |
| 4 × W7900 48 GiB | 16 | 4 | 41.392 s | 47.890–47.975 GiB | passed; nearly full |
| 4 × W7900 48 GiB | 32 | 2 | — | 47.648–47.956 GiB | HIP OOM |
| 8 × W7900 48 GiB | 1 | 32 | 143.665 s | 27.520–27.558 GiB | computed |
| 8 × W7900 48 GiB | 2 | 16 | 80.319 s | 27.818–27.832 GiB | passed |
| 8 × W7900 48 GiB | 4 | 8 | 47.055 s | 29.498–29.523 GiB | passed |
| 8 × W7900 48 GiB | 8 | 4 | 27.108 s | 33.004–33.386 GiB | passed |
| 8 × W7900 48 GiB | 16 | 2 | 24.682 s | 41.344–41.356 GiB | passed |
| 8 × W7900 48 GiB | 32 | 1 | — | 47.878–47.947 GiB | HIP OOM |

The source guide also reports a roughly 70-GB-class full AdamW DCP directory.
That is an upstream storage observation, not a course minimum. Model shards,
first/second optimizer moments, scheduler, RNG, and dataloader state all
contribute. Check actual free space before training and preserve the final
checkpoint, logs, conversion, and evaluation evidence before removing any DCP.

### Convert, do not merge an adapter

Full SFT has no LoRA adapter. The correct conversion is:

```bash
/opt/robotwin-env/bin/python \
  /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/scripts/convert_full_sft_dcp.py \
  --checkpoint /workspace/runtime/outputs/full_sft_full_4gpu_10steps/checkpoints/global_step_10 \
  --training-output /workspace/runtime/outputs/full_sft_full_4gpu_10steps \
  --output /workspace/runtime/outputs/full_sft_full_4gpu_10steps/merged_checkpoint/global_step_10/hf_ckpt
```

After conversion, retain the source workflow: validate the weight index, launch
the converted model on port 13400, run a separate ten-episode evaluation, and
optionally run the 4/8-GPU 1,000-episode benchmark under a new run identity.
Do not merge those outcomes into the required base-versus-LoRA 10+10 evidence.

## Failure diagnosis by layer

| Symptom | First checks | Do not conclude yet |
|---|---|---|
| Preflight sees fewer than four GPUs | visibility variables, device nodes, PyTorch/HIP identity | that training code is broken |
| EGL or MPLib setup fails | `/dev/dri`, EGL packages, planner flags, assets | that the policy failed an episode |
| Data loader shape/stat error | actual metadata, joint groups, padding config, norm-stat keys | that `max_action_dim=55` is the stored action shape |
| Server never becomes healthy | checkpoint index/shards, config/processor, log, port ownership, GPU memory | that task behavior is poor |
| DCP exists but merge fails | saved config, exact base identity, rank/alpha, fresh output | that LoRA training produced no updates |
| Low base `k/n` | video, action flow, expert/setup rows, task semantics | that deployment is broken; base is a pipeline reference |
| Base/merged seeds differ | actual resolved seeds and setup skips | that episode indices are a matched comparison |
| Full SFT OOM | micro batch, accumulation, resharding, teacher mode, actual free VRAM | that FSDP2 is disabled |
| Disk pressure | exact output sizes and persistent/ephemeral mounts | that automatic broad deletion is safe |

## Exercises and checks

1. **Data contract audit.** For `adjust_bottle_joint_v30`, list actual image,
   state, and action shapes from metadata. Place them beside the YAML joint
   groups and explain every difference without using `55` as a guess.
2. **Batch arithmetic.** Recalculate LoRA accumulation for four and eight GPUs.
   Then calculate full-SFT accumulation for global batch 256 and micro batch 16.
3. **Checkpoint identity.** Given a DCP directory and a Hugging Face directory,
   write the minimum checks that distinguish LoRA merge from full-SFT conversion.
4. **Matched outcomes.** Given two ten-row episode files with one shifted setup
   seed, compute the intersection, base-only/merged-only sets, and four matched
   outcome counts. State why a complete comparison is unsatisfied.
5. **One-variable extension.** Choose one of training length, GPU profile,
   checkpoint type, or video setting. Give it a new run identity and state which
   core fields must remain fixed. Do not mix its episodes into the required
   denominator.

## Summary

L14 preserves the complete competition-reference workflow while giving it a
course evidence structure:

- audit source, runtime, data, hardware, and outputs before spending GPUs;
- inspect actual LeRobot metadata together with LingBot semantic groups and
  normalization statistics;
- use the base checkpoint as a deployment reference and the official RoboTwin
  checkpoint as a separately identified optional reference;
- train rank-8/alpha-16 action-expert LoRA on the required four-GPU profile;
- treat DCP as distributed training state and create a fresh deployable Hugging
  Face checkpoint through the correct LoRA merge;
- compare base and merged policies under one frozen, resolved-seed-aware
  closed-loop protocol;
- retain 4/8-GPU full benchmarks and full-parameter SFT without pretending that
  unrun optional sections are course verification; and
- limit 100-step and 10+10-episode conclusions to what those observations can
  actually support.

## Sources and provenance

The lecture is an original course adaptation of the following pinned external
materials. RoboGenesis does not copy or rehost their container, models,
datasets, checkpoints, generated videos, or full runtime tree.

- [Robotwin-radeon-cloud companion at `27b2f6f`](https://github.com/ZiguanWang/Robotwin-radeon-cloud/tree/27b2f6fcb6c715e2cbb6db4431381f87c94b86ed), especially
  [`RoboTwin_ROCm_Reproduction.ipynb`](https://github.com/ZiguanWang/Robotwin-radeon-cloud/blob/27b2f6fcb6c715e2cbb6db4431381f87c94b86ed/RoboTwin_ROCm_Reproduction.ipynb)
  and
  [`Reproduce_Guide.md`](https://github.com/ZiguanWang/Robotwin-radeon-cloud/blob/27b2f6fcb6c715e2cbb6db4431381f87c94b86ed/Reproduce_Guide.md).
- [RoboTwin at `266f3aa`](https://github.com/RoboTwin-Platform/RoboTwin/tree/266f3aadf505a4f7fe9af0faa41a20f5f47cd123), MIT licensed.
- [XPolicyLab at `c37109c`](https://github.com/XPolicyLab/XPolicyLab/tree/c37109c500be67d0dea6b36bf7337bbd26e763cd), Apache-2.0 licensed.
- [LingBot-VLA-v2 at `951475a`](https://github.com/robbyant/lingbot-vla-v2/tree/951475ae1b1d87553e7dc47c97b53a3d695c0d13), Apache-2.0 licensed.
- [LingBot-VLA-v2 6B base model at `11c703b`](https://huggingface.co/robbyant/lingbot-vla-v2-6b/tree/11c703bf6a5c1f45b3b69168482da11fdbba53d7), whose model card declares Apache-2.0.
- [RoboTwin2.0 data at `a967b85`](https://huggingface.co/datasets/TianxingChen/RoboTwin2.0/tree/a967b852afa21a9cbf19a198f7e653109042e87c), whose dataset card declares MIT.

All five diagrams in this lecture are course-created SVGs. The benchmark and
full-SFT capacity tables are explicitly attributed observations from the
pinned companion notebook, not results produced by the current RoboGenesis
repository.
