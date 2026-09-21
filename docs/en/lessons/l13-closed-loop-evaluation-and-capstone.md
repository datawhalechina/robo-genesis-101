---
lesson: L13
slug: closed-loop-evaluation-and-capstone
locale: en
title: "Closed-Loop Evaluation and Capstone"
duration_minutes: 120
hardware: gpu-required
status: planned
---

# L13 · Closed-Loop Evaluation and Capstone

> **Course status:** `planned`. This lecture defines the evaluation mechanism and
> evidence contract. The companion notebook, the final evaluation-report contract,
> and the complete GPU-plus-rendering run have not yet been accepted. Commands on
> this page show the current project interfaces; they are not evidence that an L13
> experiment has already run.

## Where this lesson fits

[L08](/en/lessons/l08-demonstration-acquisition-and-scripted-experts) defined the
banana-to-bowl task and its geometric success predicate. [L09](/en/lessons/l09-synthetic-data-recording-and-throughput)
recorded aligned demonstrations, [L10](/en/lessons/l10-dataset-anatomy-and-imitation-learning)
made their schema inspectable, and [L11](/en/lessons/l11-domain-randomization)
added domain provenance. [L12](/en/lessons/l12-act-and-smolvla-policy-training)
then produced reloadable ACT and SmolVLA checkpoints.

L13 closes the loop:

```text
environment → demonstrations → dataset → policy checkpoint
     ↑                                      ↓
     └──── live observation ← action ← policy rollout
```

The checkpoint is no longer asked for one action on a recorded sample. It sees
the current simulator state, produces an action, changes the world, and must act
again on the consequences. L13 measures that interaction under a protocol that
was fixed before the result was known.

Before starting, you should be able to:

- explain the L08 containment predicate for placing an object in the bowl;
- identify the two camera features, 9-D robot state, 9-D action, task text, and
  FPS in a course LeRobot dataset;
- read the domain-randomization provenance introduced in L11;
- audit a numeric ACT or SmolVLA checkpoint together with its saved processors;
  and
- distinguish a pipeline-only checkpoint from a policy that has received a
  meaningful training budget.

### A focused 120-minute route

| Time | Topic | Learner output |
|---:|---|---|
| 0–15 min | Feedback and evidence levels | Explain why a live rollout tests behavior that offline probes cannot expose |
| 15–35 min | Freeze the evaluation protocol | Write a protocol manifest before seeing outcomes |
| 35–50 min | Predicate, dwell, timeout, and divergence | Convert a predicate trace into one episode result |
| 50–65 min | Reference, in-support, shifted, and OOD conditions | Name one comparison relative to training provenance |
| 65–80 min | Counts, Wilson intervals, and matched seeds | Interpret a small result without overstating precision |
| 80–95 min | Capstone preflight | Audit environment, dataset, checkpoint, cameras, action, and output paths |
| 95–110 min | Five-episode reference smoke | Produce live rollout videos and a structured result |
| 110–120 min | Failure evidence and report design | Draft a scoped conclusion and the held-out follow-up |

The first model download, a long L12 training run, and a large checkpoint sweep
do not fit inside this 120-minute route. Prepare model content before class. The
second five-episode condition can continue as the Capstone submission when the
machine cannot finish it during the synchronous session.

## Learning objectives

By the end of L13, you should be able to:

1. explain how closed-loop feedback makes policy behavior, environment state,
   and future observations interact, and why error accumulation and recovery
   therefore become part of policy capability;
2. design a fair, reproducible task-level evaluation whose results have a clear,
   comparable meaning across policies or evaluation conditions;
3. combine quantitative and qualitative evidence to judge uncertainty,
   generalization boundaries, major failure modes, and the scope of a conclusion;
   and
4. connect environment, data, policy learning, and closed-loop evaluation into
   one robot-learning workflow, then propose an evidence-based next improvement.

## What changes when the loop closes?

### Three evidence levels answer different questions

| Evidence | Information flow | What it can establish | What it cannot establish |
|---|---|---|---|
| Training loss | recorded observation and action → optimizer | the configured objective is computable on sampled training batches | that the policy can control a changing environment |
| Action replay or one-sample inference | recorded action → simulator, or recorded observation → one prediction | data decode, feature compatibility, and output shape/finiteness | recovery after the policy changes its own next observation |
| Closed-loop rollout | live observation → policy → action → environment → next live observation | task behavior under one declared rollout protocol | performance in untested conditions or on a physical robot |

An open-loop result can be valuable. L09 replay can reveal a broken recorder,
and L12 single-sample inference can reveal a missing processor. The problem is
not that those checks are weak; it is assigning them a stronger claim than they
support.

### Feedback exposes compounding error and recovery

![Recorded probes stop before action consequences return to the policy. In a closed loop, live world and wrist images plus robot state enter preprocessing and the policy, a 9-D target drives the controller and Genesis, and the resulting next state becomes the next observation. A separate third-person camera records evidence but never enters the policy.](/diagrams/l13-feedback-loop.svg)

*Course-created diagram. The lower lane is the actual causal loop; the upper
lane shows why a recorded sample or action replay does not test recovery. The
third-person camera is evidence-only.*

Suppose a gripper approaches the banana two centimeters off center. In an
offline sample, the model output can still look numerically plausible. In a live
rollout, that action moves the wrist camera, changes contact, and may rotate or
push the banana. The next decision is now conditioned on a state the expert may
rarely have visited. A capable policy must either recover or fail visibly.

Action chunking does not remove feedback. ACT and SmolVLA may queue several
predicted targets, but the runtime eventually requests a new chunk from a new
observation. The evaluation protocol must record that execution horizon. It
must also call `policy.reset()` before every episode so an old action queue or
recurrent state cannot leak into the next trial.

### The course rollout has two time scales

The policy is queried at the dataset FPS. Between queries, the current 9-D
joint-position target is held while Genesis advances at the course control rate:

```text
policy query rate = dataset FPS
simulation/control rate = 100 Hz
average simulation steps per query = 100 / dataset FPS
```

For rates such as 30 FPS, the ratio is fractional. The evaluator accumulates the
fraction instead of rounding every query independently, so the long-run ratio
remains correct. A policy FPS above the control rate is an invalid course
protocol: one simulator step cannot contain more than one policy decision in
this execution design.

The command is a joint-position target, not torque, Cartesian velocity, or an
end-effector pose. A finite vector with the wrong semantics can be more dangerous
than an obvious shape error, which is why data and checkpoint identity travel
with the action.

## Freeze the protocol before inspecting outcomes

An evaluation number is shorthand for a much larger statement:

> This checkpoint attempted this task, in these environments, with this
> observation/action/timing contract and this success rule, over these seeded
> episodes.

Changing any bold part changes the experiment. A reproducible run therefore
starts with a protocol manifest, not a percentage.

![A frozen protocol manifest determines artifacts, scene and cameras, timing and action semantics, task and success rules, and seeded evaluation conditions. Each episode then passes through reset, live rollout, the instantaneous predicate, a consecutive-dwell tracker, and a termination reason. Only afterward are successes and total episodes, Wilson intervals, per-condition records, and rollout videos assembled.](/diagrams/l13-evaluation-protocol.svg)

*Course-created diagram. Blue denotes fields frozen before execution, orange
denotes runtime decisions, and purple denotes evidence produced after the
episodes. The arrow from predicate to dwell is essential: one true frame is not
an episode success.*

### What belongs in the manifest?

| Boundary | Freeze and record |
|---|---|
| Code and runtime | course/code revision or dirty state, Python, Genesis, LeRobot, PyTorch, HIP/CUDA runtime, actual device, render backend |
| Dataset | logical repository ID, resolved local root, feature schema, FPS, camera shapes/keys, task table, domain provenance |
| Checkpoint | resolved numeric checkpoint, policy type, training dataset identity, model/processors, action horizon, camera rename, artifact revision/checksum when available |
| Scene and observation | scene/assets, world/wrist mapping, image resize, state order, which camera is evidence-only |
| Action and timing | 9-D joint-position semantics, policy FPS, 100 Hz hold/decimation, policy reset behavior |
| Task | pick pool, place target, pose/yaw reset, task text, tolerance, object schedule |
| Episode rule | containment predicate, dwell duration, timeout, exception and divergence treatment |
| Sampling | condition names, number of episodes, base and per-episode seeds, domain seeds, balanced schedule |
| Outputs | result-schema version, JSON/CSV, log, video directories, manual labels, skipped work |

This is not paperwork added after the experiment. It is the definition of the
measurement. If a field is unknown, record it as unknown and narrow the claim.
Do not silently reconstruct a convenient value after looking at the videos.

### “The same scene” is not a sufficient audit

Recording and evaluation both call the project scene builder, but they can still
differ in ways that affect the policy:

- scene or asset revisions;
- object-position and yaw jitter;
- world/wrist camera calibration or image resolution;
- Layer-A appearance and Layer-B dynamics/camera settings;
- policy FPS and action hold;
- task text, pick-object schedule, tolerance, dwell, or timeout.

The evaluation camera images are resized to the dataset metadata shape before
the policy processor sees them. SmolVLA may then rename `world/wrist` to its
canonical camera keys. The third-person video camera is cosmetic and must not be
added to the policy feature set. Check those facts explicitly instead of saying
“same simulator” and assuming equivalence.

### Matched seeds improve control, not certainty by themselves

For episode `i`, the current evaluator uses `base_seed + i`. With multiple pick
objects, its balanced mode creates nearly equal object counts and then shuffles
their order reproducibly. Reusing the same seed schedule across checkpoints or
conditions gives matched initial task instances.

That design reduces one source of comparison noise. It does not make different
domain conditions identical, guarantee cross-platform bitwise determinism, or
prove that an observed difference is statistically significant. Seed, code,
assets, backend, protocol, and domain configuration jointly define an episode.

## Turn the task predicate into an episode result

### L08 owns the spatial predicate

For a bowl target, the course predicate checks two geometric facts:

```text
within_footprint = horizontal_distance < min(success_tol, bowl_rim_radius)
inside_bowl = object_aabb_bottom_z < bowl_rim_z - rim_margin
instantaneous_containment = within_footprint and inside_bowl
```

Using the object's AABB bottom allows an elongated banana to rest partly inside
the bowl even if its center remains near the rim. It also rejects an object that
is still gripped above the bowl. L13 reuses this L08 predicate; the evaluator
does not invent a second geometric definition of placement.

### Dwell rejects a one-frame fly-by

Containment at one instant can occur while an object crosses the bowl, bounces,
or is still moving in the gripper. Let `c_t` be the instantaneous predicate
after policy step `t`:

```text
dwell_frames = max(1, ceil(dwell_seconds × policy_fps))

success at step t only if:
    c_t, c_t-1, ..., c_t-dwell_frames+1 are all true
```

Any false predicate resets the streak. The course target is at least 0.4 seconds
of consecutive containment. At 5 FPS that is two successful checks. The use of
`ceil` matters at rates where `0.4 × FPS` is not an integer: “at least 0.4 s”
must not be rounded down to a shorter requirement.

Timeout does not waive dwell. A final true frame at the timeout boundary is
still a failure if the required streak was not reached. After a genuine success,
the evaluator may hold the last action and record a short cosmetic tail so the
resting object is visible. Those extra frames do not alter the result or policy
step count.

::: warning Planned execution gate
Formal L13 evidence requires the consecutive-dwell rule, including the timeout
boundary, to pass the companion lab's contract tests. While this lesson remains
`planned`, do not publish a success rate from an unchecked local evaluator as a
verified course result.
:::

### Failure and infrastructure error are not the same event

A normal episode can end as:

- `success`: the predicate held for the complete dwell;
- `timeout`: the task was not completed in time;
- `diverged`: Genesis reported a physics divergence, counted as task failure;
- `invalid_action`: the policy returned the wrong shape or non-finite values,
  counted as a policy/runtime failure with its own reason.

A missing checkpoint, unreadable dataset, nonexistent object, unavailable
requested GPU, or absent observation camera is different. Those are run-level
preflight failures. Abort before adding an episode to the denominator; otherwise
an infrastructure problem is misreported as policy behavior.

## Define conditions relative to training provenance

### “DR on” does not mean “OOD”

Distribution language is relational. It compares evaluation conditions with a
known training distribution:

| Label | Meaning in this lesson |
|---|---|
| Reference | the predeclared baseline condition for this report; ideally aligned with audited data generation |
| Unseen in-support | new seeds or domains sampled from the same documented parameter support as training |
| Shifted | at least one factor changed, but missing or overlapping provenance prevents a disjoint-support claim |
| OOD | a named factor and value/range are demonstrably outside the documented training support, while other important factors remain controlled |

![A decision flow distinguishes four condition labels relative to training provenance. The report's predeclared baseline is Reference. If another condition has missing or overlapping provenance, it is Shifted. With auditable support, new values fully inside the documented range are Unseen in-support, while a demonstrably disjoint range is OOD when other important factors remain controlled. Small range diagrams show each relationship.](/diagrams/l13-condition-labels.svg)

New random seeds within L11's recorded friction and mass ranges are unseen
instances, not automatically OOD. A friction interval outside the recorded
training support can be a physics OOD condition only if the provenance proves
the ranges are disjoint and the proposed interval preserves a valid, numerically
stable task. Changing banana to lemon is an object/task shift, not the same claim
as a friction shift.

Even a reference domain can lead to unfamiliar states. The learned policy's own
mistakes may push the closed-loop trajectory outside the demonstration state
distribution. For that reason, this lesson uses “in-support” only for audited
domain parameters; it does not claim the complete state-visitation distribution
is identical to training.

### Isolate one factor before combining shifts

A useful first comparison holds checkpoint, task, seeds, object schedule,
timeout, predicate, and dwell fixed while changing one domain factor. This makes
the result easier to interpret and reduces the risk that aggressive combined DR
destabilizes contact.

Before running, write:

```text
reference condition:
changed factor:
training support for that factor:
evaluation value/range:
support relation: in-support | shifted | disjoint OOD
factors held constant:
safety/task-validity check:
```

If the training provenance is missing, stop at `shifted`. Honest uncertainty in
the label is stronger than a confident but unsupported OOD claim.

## Report counts before percentages

For one fixed condition, each completed episode contributes a binary outcome
`Y_i`:

```text
k = sum(Y_i)
n = number of completed evaluation episodes
observed success rate = k / n
```

Always report `k successes / n episodes`. A bare percentage hides whether it
came from five episodes or five hundred. Keep divergence counts, per-object
counts, condition names, and the episode table beside the aggregate.

### A success rate is an estimate, not a verdict

The observed success rate `k/n` describes exactly what happened in the episodes
that were run. It does **not** reveal the policy's success probability with
certainty. If the same frozen protocol were repeated with new episode seeds, the
count could change simply because a finite sample contains some easier or harder
initial states.

The denominator therefore changes how much evidence a percentage carries.
`1/1`, `5/5`, and `50/50` all display as 100%, but they do not justify the same
confidence. One success tells us much less about repeatability than fifty
successes. Reporting only “100%” hides that distinction.

A confidence interval makes this sampling uncertainty visible. The project uses
a two-sided 95% Wilson score interval because it behaves sensibly for the small
samples and extreme results common in this lesson. For example:

| Observed result | Point estimate | 95% Wilson interval | What the result supports |
|---|---:|---:|---|
| `0/5` | 0% | approximately `[0%, 43%]` | No success was observed, but success is not proven impossible. |
| `3/5` | 60% | approximately `[23%, 88%]` | The best single estimate is 60%, but five episodes leave substantial uncertainty. |
| `5/5` | 100% | approximately `[57%, 100%]` | Every observed episode succeeded, but perfect repeatability is not established. |
| `50/50` | 100% | approximately `[93%, 100%]` | The same point estimate is supported by much more evidence. |

Read the `5/5` row as: “the policy succeeded in all five observed episodes; with
so little data, success rates substantially below 100% are still compatible with
the observation.” Do not read it as: “the policy is now known to succeed 100% of
the time.” Similarly, `0/5` records a failed sample without proving that the
underlying success probability is exactly zero.

The 95% in the interval is a property of the repeated procedure, not a promise
that 95% of future episodes will succeed. Under the binomial model and a fixed
protocol, intervals constructed from many repeated samples would cover the fixed
underlying success probability about 95% of the time.

Why Wilson instead of the simplest normal approximation? At `0/n` or `n/n`, the
simple approximation can collapse to a zero-width interval such as `[100%,
100%]`, precisely when the small sample should make us cautious. Wilson stays
inside `[0, 1]` and retains nonzero uncertainty at those boundaries.

You do not need to memorize the formula. You should be able to identify `k` and
`n`, read the resulting interval, and keep the conclusion proportional to its
width. The repository computes the interval as follows for `p_hat = k/n` and
`z = 1.96`:

```text
denom  = 1 + z²/n
center = (p_hat + z²/(2n)) / denom
half   = z/denom × sqrt(p_hat(1-p_hat)/n + z²/(4n²))
interval = [max(0, center-half), min(1, center+half)]
```

This interval covers sampling uncertainty under one frozen protocol. It does not
cover biased seed selection, simulator error, a changed success rule, checkpoint
selection, or the sim-to-real gap. Overlapping or non-overlapping per-condition
Wilson intervals are also not, by themselves, a valid paired significance test.

The five reference episodes in the focused route are therefore an integration
smoke, not a performance benchmark. The Capstone repeats the same five seeds
under one held-out condition, producing a transparent `5 + 5` teaching
comparison. The report must retain the wide intervals and say that the sample
cannot support a stable model ranking.

There is no universal “enough episodes” constant. A larger study chooses its
episode budget from the desired precision, expected variability, object/domain
strata, and compute cost before looking at outcomes.

### Use the same seeds for a fair comparison

The protocol section explained why two conditions should reuse the same seed
schedule. Here is how that choice helps when you read the results. Suppose the
reference and shifted conditions produce these five episode outcomes:

| Seed | Reference | Shifted | What changed for this seed? |
|---:|---|---|---|
| `1000` | success | success | unchanged success |
| `1001` | success | failure | success → failure |
| `1002` | failure | failure | unchanged failure |
| `1003` | failure | success | failure → success |
| `1004` | success | failure | success → failure |

The aggregate counts are `3/5` for Reference and `2/5` for Shifted. Those totals
say that the shifted condition produced one fewer success in this sample. The
matched rows reveal more: two initial cases became failures, one became a
success, and two did not change. The effect was not identical for every case.

If the two conditions had used unrelated seeds, the shifted run might simply
have received harder initial object poses. Reusing seed `1002` means that its
Reference and Shifted episodes begin from the same scheduled task instance as
far as the frozen protocol allows. The declared condition factor can change the
subsequent trajectory—that is what the comparison is meant to expose.

For the course comparison, remember three actions:

1. run both conditions with the same seed schedule;
2. keep the two outcomes beside each other for every seed; and
3. report both aggregate `k/n` values and the success/failure flips.

Five matched pairs are still only a teaching-sized sample. They can reveal which
episodes changed and guide video inspection, but they do not by themselves prove
that one condition reliably causes a higher or lower success rate. Such a claim
needs more episodes and a statistical method designed for paired outcomes; that
analysis is outside the core lab.

## Rollout evidence explains what an aggregate hides

The evaluation video is a horizontal panel of the course observation views and
a diagnostic view:

```text
world camera | wrist camera | third-person video camera
 policy input   policy input      evidence only
```

Check that all panels advance, have the expected orientation, and correspond to
the recorded episode. H.264 with `yuv420p` makes the file broadly playable;
even frame dimensions are required. A filename or decodable container does not
prove that the correct cameras were recorded.

Useful manual failure categories include:

- no meaningful motion before timeout;
- approach or alignment miss;
- collision that pushes the object away;
- failed grasp or premature closure;
- loss during lift or transport;
- arrival above the bowl without release;
- release outside containment;
- unstable bounce that never satisfies dwell; and
- physics divergence.

These are observations, not labels that can be inferred from `success=false`.
Watch the rollout and cite visible evidence.

## Run one checkpoint under one frozen condition

Start with the smallest complete closed-loop evaluation unit:

```text
one checkpoint + one dataset contract + one frozen condition
    → five closed-loop episodes
    → episode rows + aggregate statistics + rollout videos
```

This run asks whether one specific checkpoint can execute the declared task under
one declared condition. It is not yet a checkpoint sweep or a Reference/Shifted
comparison. Each group of command-line options fixes part of the protocol:

| Evaluation choice | Options | What they fix |
|---|---|---|
| Policy artifact | `--policy-path` | the exact numeric checkpoint to load |
| Dataset contract | `--repo-id`, `--dataset-root` | the matching FPS, image shape, camera keys, and feature schema |
| Runtime device | `--device` | the accelerator on which policy inference must run |
| Episode sample | `--episodes`, `--seed`, `--balanced` | the denominator and reproducible seed/object schedule |
| Task and timeout | `--pick`, `--place`, `--max-seconds` | the task instance and maximum duration of each episode |
| Evidence outputs | `--save-video`, `--video-dir`, `--results-out` | where videos and structured results are stored |

Replace every `CHOOSE_...` placeholder with an audited value. The policy path
must name a numeric checkpoint, and the dataset identity must match the contract
used to train it. Keep each run in an isolated output directory so results from
different conditions cannot be mixed accidentally.

```sh
RG101_POLICY_PATH=CHOOSE_NUMERIC_CHECKPOINT_PRETRAINED_MODEL_DIR
RG101_REPO_ID=CHOOSE_TRAINING_DATASET_REPO_ID
RG101_DATASET_ROOT=CHOOSE_MATCHING_LOCAL_DATASET_ROOT
RG101_EVAL_ROOT=outputs/l13/reference

uv run python -m robo_genesis.eval_policy \
  --policy-path "$RG101_POLICY_PATH" \
  --repo-id "$RG101_REPO_ID" \
  --dataset-root "$RG101_DATASET_ROOT" \
  --device cuda \
  --episodes 5 \
  --seed 1000 \
  --max-seconds 15 \
  --pick 011_banana \
  --place 024_bowl \
  --balanced=true \
  --save-video \
  --video-dir "$RG101_EVAL_ROOT/videos" \
  --results-out "$RG101_EVAL_ROOT/results.json"
```

In this example, `--episodes 5 --seed 1000` schedules five reproducible episode
seeds beginning at 1000. The evaluator loads the checkpoint, constructs live
observations using the dataset contract, runs the feedback loop, and records one
row per episode before computing the aggregate count and Wilson interval.

On ROCm PyTorch, `--device cuda` selects the shared PyTorch device API; verify
that the printed hardware is the intended AMD GPU and that HIP is present. A
silent CPU fallback does not satisfy this lesson's GPU-required path.

::: warning Current interface boundary
The current CLI recovers dataset FPS and image features from metadata and
recovers a saved SmolVLA camera rename when available. It writes per-episode
details, counts, a Wilson interval, and videos. While the lesson remains
`planned`, preserve the full command and environment separately: the accepted
Capstone report schema and all preflight checks are not yet a verified public
interface.
:::

### What this five-episode run can establish

This first run produces integration evidence and a small-sample behavior record.
Those are useful, but they do not support every conclusion about the policy:

| This run can establish | This run cannot establish |
|---|---|
| the checkpoint loads with its matching processors and dataset features | that the policy is reliable |
| live observations reach the policy and its actions affect the simulator | performance under untested conditions |
| scene reset, policy reset, timeout, predicate, and dwell execute | robustness to a shifted or OOD condition |
| episode rows, counts, a Wilson interval, and videos are produced | a stable ranking against another checkpoint |

`0/5`, an intermediate count, and `5/5` are all valid evaluation outputs. Judge
the closed-loop evaluation path by whether every episode followed the frozen
protocol and produced complete evidence. Report policy behavior separately from
the observed `k/n`, interval, videos, and declared scope; do not require a hidden
success threshold before accepting the run as valid.

A one-step L12 smoke checkpoint may establish that the evaluator can load and
run a policy. Its rollout result is not evidence of a meaningfully trained
policy.

## Optional extension: compare saved checkpoints

`eval_sweep.py` discovers numeric checkpoints in one training run. Omitting
`--steps` evaluates every usable numeric checkpoint it finds; supplying
`--steps` restricts the comparison to an explicit list. Every checkpoint receives
the same frozen task protocol and seed schedule, so differences in initial task
instances do not obscure the checkpoint comparison. The core Capstone does not
require this extension; it can evaluate one selected checkpoint.

```sh
uv run python -m robo_genesis.eval_sweep \
  --run-dir CHOOSE_TRAINING_RUN_DIR \
  --repo-id CHOOSE_TRAINING_DATASET_REPO_ID \
  --dataset-root CHOOSE_MATCHING_LOCAL_DATASET_ROOT \
  --episodes 5 \
  --seed 1000 \
  --pick 011_banana \
  --output-dir outputs/l13/sweep
```

A training smoke that saved one checkpoint produces one point, not a learning
curve. With several checkpoints, success may rise, flatten, oscillate, or fall.
Matched seeds improve comparability, but they do not remove every checkpoint-
selection or training confound. Describe the curve that was observed; do not
promise a “rising” curve in advance.

The runtime cost grows directly with the number of checkpoints:

```text
number of rollouts = checkpoints × episodes
```

For example, three checkpoints evaluated on five matched episodes each require
15 rollouts. The tool writes per-checkpoint and per-episode results to
`sweep.json`, a compact checkpoint summary to `sweep.csv`, and the observed
success-rate curve to `success_curve.png`.

::: warning Optional path, not yet L13-verified
The checkpoint-sweep path exists in the current implementation, but this lesson
has not yet accepted a complete multi-checkpoint GPU-and-render sweep as course
evidence. Treat it as an exploration path, not a requirement for the core
single-checkpoint Capstone.
:::

## Capstone: answer one question with traceable evidence

The Capstone begins with a policy question, not a checklist of commands:

> For one identified checkpoint, what do its closed-loop outcomes under one
> Reference condition and one declared held-out condition allow us to conclude?

The answer must be traceable back through the runtime, training data, checkpoint,
evaluation protocol, and live rollouts. Missing evidence weakens the conclusion;
a strong-looking final percentage cannot repair an earlier gap.

![The Capstone moves through six evidence gates: environment identity, dataset and provenance, checkpoint and processors, frozen reference and held-out conditions, live feedback rollouts, and a scoped report. Every gate states what it establishes and what stronger claim remains outside its boundary.](/diagrams/l13-capstone-evidence-chain.svg)

*Course-created diagram. Read the gates from left to right: each one answers a
necessary subquestion and limits the claim that can pass to the next gate.*

### Read each gate as a question

| Gate | Subquestion | Minimum evidence | Claim boundary |
|---|---|---|---|
| 1. Environment | Did the declared runtime actually execute? | environment report, actual GPU/backend, and a live camera frame | Establishes the runtime used; says nothing yet about data or policy behavior. |
| 2. Dataset | What demonstrations and training support does the policy depend on? | dataset identity, feature schema, task, and available provenance | Makes the training input interpretable; does not show that a useful policy was learned. |
| 3. Checkpoint | Which policy artifact is being evaluated? | numeric checkpoint identity, saved processors, and dataset match | Makes the policy package reconstructable; does not show that its actions complete the task. |
| 4. Protocol | What exactly will be compared? | frozen task/success rule plus Reference and held-out conditions using the same five seeds | Makes the two results comparable; does not predetermine their outcomes. |
| 5. Rollouts | What happened when the policy closed the loop? | complete episode rows, termination reasons, counts, and videos for both conditions | Establishes simulated behavior under this protocol only. |
| 6. Report | What conclusion is supported, and where does it stop? | `k/n`, Wilson intervals, matched rows, limitations, and reproduction commands | Produces a traceable answer; does not establish universal robustness or sim-to-real transfer. |

If a gate is missing, stop or weaken the claim. Without dataset provenance, for
example, a changed condition cannot be justified as OOD. Without a fixed
checkpoint identity, another learner cannot reproduce the result. Without live
rollouts, checkpoint loading cannot become a task-performance claim.

::: warning Checkpoint availability
No versioned course checkpoint is currently published in this repository. Use
your own L12 checkpoint unless a release artifact manifest explicitly lists one.
Do not invent a URL, silently search unrelated outputs, or describe a provided
checkpoint as self-trained.
:::

### Write the report from the evidence chain

Use the gates to fill one compact report rather than copying every lesson output:

```text
Question:
  For checkpoint [identity], what do Reference and [held-out condition]
  rollouts support?

Environment and artifacts:
  [runtime identity] + [dataset identity] + [checkpoint identity]

Frozen protocol:
  [task and success rule] + [matched seeds] + [condition definitions]

Observed evidence:
  Reference: [k/n and interval]
  Held-out:  [k/n and interval]
  [matched outcome changes, termination reasons, and video evidence]

Conclusion:
  This evidence supports [claim limited to the tested protocol].

Does not establish:
  [untested conditions, stable ranking, physical-robot performance, ...]

Next experiment:
  [one change that would reduce the most important remaining uncertainty]

Reproduce with:
  [commands and output locations]
```

A zero-success result can still complete the Capstone when the evaluation is
valid and the diagnosis follows the evidence chain. Conversely, a high observed
rate cannot compensate for an unidentified checkpoint or a protocol changed
after the outcomes were seen.

The lecture owns the reasoning: why each gate is necessary and which claim it
permits. The companion lab owns the mechanical detail—collecting full version
fields, feature names, processor files, manifests, logs, and output paths in its
preflight, audit, rollout, and report cells. You should not memorize those field
lists; you should be able to explain why the final conclusion depends on them.

## Diagnose failures by boundary

1. **Environment, GPU, or rendering:** confirm the project environment, package
   versions, `torch.cuda.is_available()`, `torch.version.hip`, actual device,
   Genesis backend, and a live camera frame. Requested GPU execution that falls
   back to CPU is a failed full-path check.
2. **Dataset identity:** confirm repository ID, resolved root, metadata, task,
   FPS, camera keys/shapes, action names, and domain provenance. Do not search
   for a convenient substitute.
3. **Checkpoint identity:** inspect the numeric directory, policy type,
   processors, training dataset, action horizon, and camera rename before
   loading Genesis.
4. **Protocol preflight:** reject non-positive episode/timeout values, an empty
   pick pool, unsupported objects, policy FPS above control FPS, an invalid
   condition, or an output collision before expensive work starts.
5. **Live observation:** inspect 9-D finite state, HWC `uint8` world/wrist
   frames, resize behavior, and the processor's expected keys. Keep the video
   camera out of policy input.
6. **Policy action:** reset policy state each episode; require one finite 9-D
   joint target before applying it. Then inspect action queue and query/hold
   timing.
7. **Simulation:** identify contact explosion, NaN divergence, invalid reset,
   or an unsafe shifted range. Preserve the failing seed and condition.
8. **Task outcome:** separate approach, grasp, lift, transport, release,
   containment, dwell, and timeout using the video and predicate trace.
9. **Sampling and report:** verify denominator, missing/duplicated seeds,
   per-object balance, condition separation, pooled labels, and interval inputs.
10. **Policy capability:** only after the first nine boundaries hold should you
    change data coverage, training budget, checkpoint selection, or model
    capacity.

## Checkpoints and exercises

### Concept checkpoints

1. Which causal edge is absent from a one-sample checkpoint probe?
2. Why must policy state and an action-chunk queue reset between episodes?
3. At 5 FPS and a 0.4-second dwell, how many consecutive predicate checks are
   required? What changes at 7 FPS when the rule uses `ceil`?
4. Why is one true containment frame at timeout still a failure?
5. Which facts must match before two success rates are comparable?
6. Why can new seeds from the same L11 parameter ranges be unseen but in-support?
7. Why is a shifted camera condition not automatically OOD?
8. What does a Wilson interval capture, and which uncertainties remain outside it?
9. Why should a physics divergence remain in the denominator?
10. What evidence separates a successful evaluator run from a useful policy?

### Protocol exercise

In companion notebook cell `l13-protocol`, change one synthetic predicate trace.
Predict its maximum streak and episode outcome before running the cell. Include
a trace whose last frame is true but whose streak is shorter than the required
dwell, and explain why timeout must not promote it to success.

### One-factor condition exercise

In `l13-condition-plan`, change exactly one domain factor. Use the training
provenance to label it `unseen in-support`, `shifted`, or `OOD`. State which
factors remain fixed and why the new range still preserves a valid task. If the
provenance cannot justify the label, downgrade it to `shifted`.

### Failure-evidence exercise

In `l13-result-audit`, select one actual failed episode using a rule written
before watching it—for example, the first timeout. Add one manual category and
two visible observations from the rollout. Do not infer a training-data or
model-architecture cause from the aggregate rate alone.

### Capstone conclusion exercise

In `l13-capstone-report`, write three sentences:

1. what the current evidence supports;
2. what it cannot support; and
3. which next experiment would reduce the most important uncertainty.

The next experiment should change one justified factor or increase a
predeclared episode budget. “Train longer” without a diagnosed boundary is not
an evidence-based recommendation.

## Summary

- Closed-loop evaluation measures a causal feedback process: each policy action
  changes the next observation and exposes error accumulation or recovery.
- A success rate has meaning only inside a frozen artifact, scene, observation,
  action, timing, task, seed, condition, and success protocol.
- L08 containment becomes an episode success only after consecutive dwell;
  timeout and divergence do not create exceptions to the rule.
- Reference, in-support, shifted, and OOD are defined relative to training
  provenance. Enabling randomization is not an OOD proof.
- Report successes and total episodes, a Wilson interval, per-condition/object
  details, matched episode rows, and rollout evidence. Five episodes remain a
  smoke, even at 0% or 100% observed success.
- The Capstone links environment, dataset, checkpoint, protocol, live rollout,
  and report evidence. Passing one gate never grants the claim of a later gate.
- Checkpoint sweeps are optional extensions whose cost grows with the number of
  saved checkpoints; their curves must be observed, not assumed to rise.

## Sources

- Wilson, [“Probable Inference, the Law of Succession, and Statistical
  Inference”](https://doi.org/10.1080/01621459.1927.10502953) — the score
  interval used for one binomial success proportion.
- Brown, Cai, and DasGupta, [“Interval Estimation for a Binomial
  Proportion”](https://doi.org/10.1214/ss/1009213286) — comparison of binomial
  interval behavior, including the limitations of the Wald interval.
- [LeRobot 0.6.0 policy control utilities](https://github.com/huggingface/lerobot/blob/v0.6.0/src/lerobot/common/control_utils.py)
  — the version-pinned `predict_action` path used by the project evaluator.
- [LeRobot 0.6.0 policy factory](https://github.com/huggingface/lerobot/blob/v0.6.0/src/lerobot/policies/factory.py)
  — policy and pre/postprocessor construction used when reloading ACT and
  SmolVLA checkpoints.
- [Genesis World documentation](https://genesis-world.readthedocs.io/en/latest/)
  and [Genesis World 1.3.3 on PyPI](https://pypi.org/project/genesis-world/1.3.3/)
  — simulator documentation and the exact course version.
- [RoboGenesis 101 task predicate](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/grasp_demo.py),
  [single-checkpoint evaluator](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/eval_policy.py),
  [checkpoint sweep](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/eval_sweep.py),
  and [shared statistics](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/stats.py)
  — current project behavior and the implementation boundary described here.
- [RoboGenesis 101 compatibility record](https://github.com/datawhalechina/robo-genesis-101/blob/main/COMPATIBILITY.md)
  — verified platforms, historical checkpoint probes, and claims that remain
  unverified.
