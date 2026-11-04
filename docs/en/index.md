---
layout: home
title: RoboGenesis 101

hero:
  name: RoboGenesis 101
  text: Practical Robot Learning with Genesis
  tagline: A progressive path through simulation, control, data, policy training, and closed-loop evaluation for learners with basic Python experience
  actions:
    - theme: brand
      text: Start with L01
      link: /en/lessons/l01-introduction-and-environment-diagnostics
    - theme: alt
      text: 中文
      link: /zh/

features:
  - title: Genesis foundations
    details: Learn environment diagnostics, scenes, rigid-body physics, robot control, inverse kinematics, cameras, and parallel simulation.
  - title: From control to grasping
    details: Build a grasping scene and understand scripted experts and demonstration acquisition.
  - title: From data to policies
    details: Continue through data recording, imitation learning, domain randomization, policy training, and closed-loop evaluation.
---

## Course status

> The 14 lessons currently comprise 8 `cpu-verified` and 6 `gpu-verified` lessons,
> with 0 `planned` and 0 `published`. Every lesson has reached its declared verification
> status. The release identity, version, license, and per-file checksum manifest are
> frozen for the `rg101-fruit-pick@1.0.0` dataset and the
> `rg101-fruit-pick-smolvla@1.0.0` checkpoint, with a standard download/verification
> workflow plus bilingual local consumption paths. Both are now `release`, while the ACT
> artifact remains `unavailable`. Installation, artifact download, documentation builds, CPU smoke,
> and consumer verification in a fresh environment are complete. Reference AMD GPU
> release acceptance and the final V1 release-readiness audit are also complete. The pinned
> dataset revision `eab6739...` and SmolVLA revision `6649cc3...` both include their
> README/card, license declaration (CC BY-NC 4.0 for the dataset and Apache-2.0 for the
> checkpoint), upstream or third-party attribution, and usage limits.
> All nine dataset files and seven checkpoint files still match the course's per-file
> checksums. The project lead authorized both artifact status promotions to `release`.
> Lesson `published` status remains unchanged because it requires a separate review.
> L01–L07 are `cpu-verified` after their
> clean-kernel CPU verification; their
> additional AMD paths also passed their respective contracts on the reference R9700.
> L08 is `gpu-verified` after its bilingual CPU numerical paths, CPU+EGL path, and
> scripted-expert path on a reference R9700 all passed. L09 is also `gpu-verified`:
> its bilingual CPU diagnostics, CPU+EGL path, and dual-camera recording and readback
> on a reference R9700 all passed. The renumbered L12 training content is
> `gpu-verified` after ACT and SmolVLA GPU smoke, checkpoint audit, and reload checks.
> L10 is `cpu-verified` after its bilingual CPU-only data-readback and inspection
> paths passed. L11 is `gpu-verified` after its bilingual diagnostics, CPU+EGL path,
> and bounded-DR recording, readback, and provenance path on a reference R9700 passed.
> L13 is `gpu-verified` after its bilingual diagnostics, single-checkpoint closed-loop
> evaluation on a reference R9700 with AMD+EGL, matched Reference/shifted rollouts,
> and H.264 video and report evidence audit passed. This does not establish a stable
> success rate, OOD robustness, or sim-to-real transfer. L14 is an optional advanced
> practicum outside the completion path for the 13 core lessons. Its required path is
> `gpu-verified` in the pinned companion runtime on four W7900D GPUs: base `0/10`,
> 100-step LoRA, DCP-to-HF merge, merged `0/10`, and a 20-video audit. These are
> independent small aggregate observations, not evidence of improvement;
> resolved-seed matching and the higher-cost competition extensions remain unverified.

| Lesson | Topic | Planned duration | Hardware | Status |
|---|---|---:|---|---|
| L01 | [Introduction, Runtime Platforms, and Environment Diagnostics](/en/lessons/l01-introduction-and-environment-diagnostics) | 30 min | `cpu-ok` | `cpu-verified` |
| L02 | [Scenes, Entities, and the Simulation Lifecycle](/en/lessons/l02-scenes-entities-and-simulation-lifecycle) | 90 min | `cpu-ok` | `cpu-verified` |
| L03 | [Rigid-Body Physics and Stable Simulation](/en/lessons/l03-rigid-body-physics-and-stable-simulation) | 90 min | `cpu-ok` | `cpu-verified` |
| L04 | [Robot Models, Degrees of Freedom, and Joint Control](/en/lessons/l04-robot-models-dofs-and-joint-control) | 90 min | `cpu-ok` | `cpu-verified` |
| L05 | [Inverse Kinematics, End-Effector Poses, and Cameras](/en/lessons/l05-inverse-kinematics-end-effector-poses-and-cameras) | 120 min | `cpu-ok` | `cpu-verified` |
| L06 | [Parallel Simulation and Batched Franka Control](/en/lessons/l06-parallel-simulation-and-batched-franka-control) | 90 min | `cpu-ok` | `cpu-verified` |
| L07 | [Building a Grasping Task Scene](/en/lessons/l07-building-a-grasping-task-scene) | 90 min | `cpu-ok` | `cpu-verified` |
| L08 | [Demonstration Acquisition and Scripted Experts](/en/lessons/l08-demonstration-acquisition-and-scripted-experts) | 120 min | `gpu-recommended` | `gpu-verified` |
| L09 | [Synthetic Data Recording and Collection Throughput](/en/lessons/l09-synthetic-data-recording-and-throughput) | 120 min | `gpu-recommended` | `gpu-verified` |
| L10 | [Dataset Anatomy and Imitation Learning 101](/en/lessons/l10-dataset-anatomy-and-imitation-learning) | 90 min | `gpu-recommended` | `cpu-verified` |
| L11 | [Domain Randomization](/en/lessons/l11-domain-randomization) | 90 min | `gpu-recommended` | `gpu-verified` |
| L12 | [Training ACT and SmolVLA Policies](/en/lessons/l12-act-and-smolvla-policy-training) | 150 min | `gpu-required` | `gpu-verified` |
| L13 | [Closed-Loop Evaluation and Capstone](/en/lessons/l13-closed-loop-evaluation-and-capstone) | 120 min | `gpu-required` | `gpu-verified` |
| L14 | [Optional Advanced Practicum: Fine-Tuning LingBot-VLA-v2 with RoboTwin Data](/en/lessons/l14-robotwin-lingbot-vla-fine-tuning) | 180 min | `gpu-required` | `gpu-verified` |

## GPU compute resources

Learners are encouraged to use a suitable GPU throughout the course; policy training and
closed-loop evaluation in particular depend on GPU acceleration. The course's recorded GPU
verification was carried out on AMD Radeon hardware using the documented ROCm profiles.

If you do not have access to a local GPU, you can
[register as an AMD developer](https://developer.amd.com.cn/login?source=eHjyREaw5) and check
the free compute resources currently available through the AMD developer program. To help
learners skip local environment setup, this course has deployed a `robo-genesis-101-beta`
template on the [AMD Developer Cloud](https://developer.amd.com.cn/radeon/). After registering
and signing in, find the template under `Templates` and launch it to open and run the course
notebooks directly. Resource availability, quotas, regions, and hardware profiles are managed
by AMD and may change.

## Supporting materials

- [Setup and Fallback Paths](/en/appendix/setup-and-fallbacks)
- [Course Glossary](/en/appendix/glossary)
- [API and Command Cheatsheet](/en/appendix/api-cheatsheet)
- [Instructor Guide](/en/appendix/instructor-guide)
- [References and Third-Party License Audit](/en/references/)
