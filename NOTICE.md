# Third-Party Notices and Asset Audit

This document records third-party material considered for RoboGenesis 101. It is
an audit ledger, not a replacement for the original license texts and not a
grant of rights by this project. M0.4 approved the audit, and M0.5 approved the
license boundary and dispositions reflected below.

Initial audit date: 2026-08-28. Dataset/checkpoint candidate review: 2026-10-30.
Final V1 release-readiness review: 2026-11-01.

The four YCB objects identified below were vendored during M1.4. No other
reviewed third-party assets have been copied into this repository.

## Audit summary

| Material | Location reviewed | License evidence | Approved disposition |
|---|---|---|---|
| ManiSkill-distributed YCB meshes and textures | `franka_fruit_pick_demo/assets/ycb/` at the recorded `course` baseline | ManiSkill identifies its assets as CC BY-NC 4.0 | M1.4 vendors only banana, lemon, plum, and bowl with the original license, provenance, and checksums |
| Franka Emika Panda MJCF model | `franka_fruit_pick_demo/assets/robots/franka/` at the recorded `course` baseline | Model README and MuJoCo Menagerie upstream identify the model as Apache-2.0 | Do not copy the incomplete source bundle; use the model bundled with the pinned Genesis version |
| Source-course renders and slide exports | Both source courses at their recorded baselines | Project lead confirmed on 2026-08-28 that the course code, lectures, and teaching content are original | Original portions use MIT after migration; preserve notices for depicted or embedded third-party material |
| Datasets, checkpoints, and training/evaluation outputs | Local source worktrees and fixed external releases | The non-DR fruit-pick dataset and matching SmolVLA checkpoint passed checksum, clean-environment, consumer, and reference AMD release acceptance; both pinned revisions have reviewed cards, license declarations, attribution, and usage limits; the additional ACT candidate failed closed-loop selection | Keep outside the repository MIT License; `rg101-fruit-pick@1.0.0` and `rg101-fruit-pick-smolvla@1.0.0` are approved releases, while ACT remains unavailable |

The course MIT License must not be presented as relicensing any item in this
table. Third-party terms continue to apply to third-party material.

## 1. YCB objects distributed by ManiSkill

### Reviewed scope

The source baseline
`wangxunx/franka_fruit_pick_demo@0de3ae0df2a91acbda7f4fb537c65d9e54190527`
contains these ten directories under `assets/ycb/`:

- `003_cracker_box`
- `006_mustard_bottle`
- `011_banana`
- `013_apple`
- `014_lemon`
- `016_pear`
- `017_orange`
- `018_plum`
- `024_bowl`
- `025_mug`

The reviewed tree contains 60 files and 11,255,029 bytes. Each object has an
OBJ render mesh, a PLY collision mesh, two material files, and two texture
images. The SHA-256 of the sorted per-file SHA-256 manifest, with paths relative
to `assets/ycb/`, is:

```text
40465c3b1f59c0b1e0c88ce507d0957b4b5ca4b29e637c80fb6d72611a8d9fa6
```

All ten directories are byte-for-byte identical to the corresponding
`models/<object>/` directories in a local ManiSkill 3.0.1 YCB download.

### Provenance

- Immediate distributor: [ManiSkill](https://github.com/haosulab/ManiSkill).
- Download used by ManiSkill 3.0.1:
  [mani_skill2_ycb.zip](https://huggingface.co/datasets/haosulab/ManiSkill2/resolve/main/data/mani_skill2_ycb.zip).
- SHA-256 declared by ManiSkill 3.0.1 for that archive:
  `1551724fd1ac7bad9807ebcf46dd4a788caed5c9499c1225b9bfa080ffbefcb3`.
- Original collection: [YCB Object and Model Set](https://www.ycbbenchmarks.com/).
- Recommended scholarly citation: Calli et al., “Benchmarking in Manipulation
  Research: Using the Yale-CMU-Berkeley Object and Model Set,” IEEE Robotics &
  Automation Magazine, 2015,
  [doi:10.1109/MRA.2015.2448951](https://doi.org/10.1109/MRA.2015.2448951).

The source repository README names ManiSkill and YCB, and its asset setup code
names a local ManiSkill dataset as the fallback source. The extracted asset
directories themselves contain no README, license, or citation file.

### License evidence and obligations

The ManiSkill 3.0.1 package metadata and the official ManiSkill README both
state: “The assets are licensed under CC BY-NC 4.0.” The applicable license is
[Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/legalcode).
The YCB website returned HTTP 500 during this audit, so no separate original-YCB
license statement was confirmed there. This ledger therefore uses the explicit,
more restrictive ManiSkill asset license for the reviewed copies.

If these files are distributed with RoboGenesis 101, at minimum the project
must retain the CC BY-NC 4.0 terms, credit ManiSkill and the YCB Object and Model
Set, link the license and sources, indicate modifications, and avoid presenting
the assets as covered by the course's own content or code license. The
noncommercial restriction must remain visible to downstream users.

M0.5 approved vendoring only the four objects used by the course mainline:
`011_banana`, `014_lemon`, `018_plum`, and `024_bowl`. M1.4 copied their 24 files
(4,463,632 bytes) byte-for-byte from the fixed source commit into
`assets/third_party/ycb/models/`. The directory includes the CC BY-NC 4.0 legal
text, source archive checksum, object list, modification record, and a per-file
`SHA256SUMS` manifest. The SHA-256 of that manifest is:

```text
df3d55d6b357ee9acbc48453eeeac6a35549eecc4c24aea5eb8aff41f3059948
```

The other six audited objects remain excluded unless a later lesson requests
and separately reviews them.

### Apparent scaling discrepancy

`setup_assets.py` in the source course says that `013_apple` and `017_orange`
come from scaled copies. That statement does not describe the reviewed Git
baseline: both committed directories are byte-for-byte identical to the
ManiSkill download, including `textured.obj` and `collision.ply`. The separate
local `mani_skill_dataset_scaled` files are different and are not part of the
approved migration baseline.

Therefore the reviewed apple and orange files must be treated as unmodified
ManiSkill assets, but neither object is included in RoboGenesis 101. M1.4 removes
the stale fallback and all scaled-asset branches. The course does not use or
generate scaled assets; changing that decision would require a separate asset
and license review.

## 2. Franka Emika Panda MJCF model

### Reviewed scope

The source baseline contains 77 files under `assets/robots/franka/`: one README,
eight MJCF/XML files, one PNG, 59 OBJ meshes, and eight STL meshes. Its size is
36,562,008 bytes. The SHA-256 of the sorted per-file SHA-256 manifest, with paths
relative to `assets/robots/franka/`, is:

```text
b8924c554f16fd318af3a3afaf9637e884221393e220740dfbdbae5f9da29fc0
```

The tree is byte-for-byte identical to
`wangxunx/genesis-world@20d07d7447b27540dcd8869960f58dac4301cd0f`
under `genesis/assets/xml/franka_emika_panda/`, which is the immediate source
named by the source course's setup code.

### Provenance

- Immediate source: the Genesis `franka_emika_panda` asset directory.
- Model upstream: [MuJoCo Menagerie — Franka Emika Panda](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda).
- Earlier robot-description source named by the model README:
  [franka_ros/franka_description](https://github.com/frankaemika/franka_ros/tree/develop/franka_description).

The model README documents the URDF-to-MJCF conversion and subsequent model
changes. “Franka” and “Panda” are used only to identify the source robot/model;
the Apache license does not grant trademark rights.

### License evidence and missing file

Both the reviewed model README and the official MuJoCo Menagerie README identify
the model as Apache License 2.0. The official upstream supplies the referenced
[model-level LICENSE](https://github.com/google-deepmind/mujoco_menagerie/blob/main/franka_emika_panda/LICENSE).

However, neither the copied source-course directory nor its immediate Genesis
directory contains the `LICENSE` file linked by its README. A repository-level
Genesis Apache-2.0 license exists, but it does not repair the missing
model-level distribution record by itself.

M0.5 approved using `xml/franka_emika_panda/panda.xml` from the pinned Genesis
installation instead of copying the incomplete source-course folder. The
course must retain Genesis, MuJoCo Menagerie, and Franka attribution here and
must not hard-code a developer-machine `site-packages` path. If that bundled
model later proves incompatible, a new reviewed proposal must select an exact
MuJoCo Menagerie commit, include the model-level Apache-2.0 license, and record
any modifications before vendoring it.

## 3. Source-course media and exports

The Franka source repository contains 30 PNG/GIF paths in its bilingual course
tree plus three copies in top-level documentation. Together they represent five
unique simulation outputs: world-camera and wrist-camera frames, a
scripted-pick GIF, a domain-randomization montage, and its baseline montage.
Git history records Xun Wang as the author who added them. On 2026-08-28, the
project lead additionally confirmed that the source-course code, lectures, and
teaching content are original. The renders nevertheless depict the YCB and
Franka assets audited above, whose separate terms continue to apply.

The same source contains 14 PPTX exports and one PDF export. The Genesis
foundations source contains six SVG flow diagrams and twelve PPTX exports. No
separate stored third-party paper figures were identified by the static file and
link inventory, but exported presentations were not treated as proof of rights
for their embedded content.

These files are not part of the M1.3 code migration. During M2-M4, each selected
media file must receive one of these dispositions before import:

- record it as original source-course material under MIT;
- retain the YCB/Franka notices when those assets appear in a rendering;
- replace it with a reproducibly generated equivalent; or
- separately audit or omit any newly discovered external material.

Generated PPTX/PDF files must be regenerated from their reviewed source rather
than treated as the source of truth.

## 4. Datasets, checkpoints, models, and dependencies

M0.2 excluded all local datasets, checkpoints, evaluation outputs, videos,
frames, logs, and caches from migration. They receive no redistribution
approval from this audit.

If M5 publishes a dataset or checkpoint, add a separate entry here containing
its creator, source data, model provenance, license, immutable version,
checksum, hosting URL, and citation. A model name or Hugging Face repository
link in lesson text is not sufficient evidence of redistribution rights.

Genesis, ManiSkill, LeRobot, PyTorch, and other installable software packages
are dependencies rather than vendored source in the current plan. Their exact
versions and installation sources belong to M0.6-M0.7; any code later copied
from them must first receive a file-level license review and a new entry here.

### M5.1 fruit-pick dataset release

M5.1 selected the non-domain-randomized `fruit_pick` aggregation as the V1
example-dataset candidate. It is not the similarly named `fruit_pick_dr`
dataset used by some historical training and integration runs. The selected
payload contains 300 successful scripted-expert episodes: 100 each for banana,
lemon, and plum placement into a bowl, with 71,976 frames at 30 FPS, 9-D Franka
state/action vectors, and world/wrist RGB video at 640×360.

The nine LeRobot payload files contain 505,224,976 bytes. The SHA-256 of the
relative-path-sorted `sha256sum` stream is:

```text
26cb09b621aa43f3abbe39ce2e55a3c161c2f89c9fe174fbd5e317bec4426f23
```

The course manifest now pins
[`wangxun1010/fruit_pick@eab67399248de625506d43fdeb994788874a8492`](https://huggingface.co/datasets/wangxun1010/fruit_pick/tree/eab67399248de625506d43fdeb994788874a8492).
That immutable revision contains the dataset README/card, the
`license: cc-by-nc-4.0` metadata and license link, and ManiSkill/YCB attribution.
The Hub tree records all nine payload files as unchanged from the earlier
`475e8c6ec7079c4c52b20a0221bf959acb541abd` upload commit. Their sizes and
SHA-256 values still match `artifacts/manifest.json`. A separate standalone
LICENSE, NOTICE, or second hosting manifest is therefore not required for this
dataset gate.

The source recording was produced from
`wangxunx/franka_fruit_pick_demo@0de3ae0df2a91acbda7f4fb537c65d9e54190527`
with Python 3.12.3, Genesis 1.3.1, LeRobot 0.6.0, PyAV 15.1.0, and an AMD
Radeon AI PRO R9700. The three archived recording logs confirm 100/100
successful episodes per object and seed sequences beginning at zero. The logs
do not contain the original shell invocation, so the course provenance record
describes any reconstructed command as reconstructed from the fixed source,
defaults, metadata, and runtime logs rather than as an original transcript.

The artifact identity is `rg101-fruit-pick` version `1.0.0`, with
logical LeRobot ID `genesis/fruit_pick` and RoboGenesis dataset-schema version
`1.0.0`. Artifact versions are immutable and independent of schema versions;
any payload-byte change requires a new version and checksum set. Checkpoints
must record this precise version, hosting commit, and payload-manifest SHA-256,
not only the logical repo ID.

The project lead confirmed the creator identity and the following dataset license on
2026-10-30. The dataset license is
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/legalcode), not
the repository MIT License. The generated trajectories, task strings, and
course arrangement are credited to Xun Wang for RoboGenesis 101. The rendered
video depicts ManiSkill-distributed YCB banana, lemon, plum, and bowl assets,
whose CC BY-NC 4.0 terms require attribution and preserve the noncommercial
restriction. The Franka model is supplied through Genesis from the MuJoCo
Menagerie lineage and retains its separate attribution. The dataset hosting
materials are complete at the pinned `eab6739...` revision. The project lead
authorized the course artifact status promotion to `release` on 2026-11-01.

The release does not include people, personal data, real-robot user data,
depth, segmentation, force/torque, tactile signals, failed episodes,
checkpoints, logs, or evaluation output. It also has no per-episode domain
provenance and must not support claims about known training domains, held-out
domains, or OOD membership.

### M5.2 fruit-pick checkpoint artifacts

M5.2 defines separate V1 identities for `rg101-fruit-pick-act` and
`rg101-fruit-pick-smolvla`, each initially versioned `1.0.0` under checkpoint
schema `1.0.0`. Both must name the M5.1 `rg101-fruit-pick` dataset version,
immutable hosting commit, and payload-manifest SHA-256. A saved
`dataset.repo_id=genesis/fruit_pick` string alone is not sufficient provenance.

No ACT release payload exists. The original course ACT output is a 200-step
pipeline smoke trained on `genesis/m3_demo_banana`; it is excluded from the V1
candidate. A separate 20,000-step ACT candidate was generated on the reviewed
dataset and passed static, checksum, GPU reload, and open-loop audits, but it
timed out in all five reference and all five shifted-friction closed-loop
episodes. It was therefore not selected or hosted as a learner fallback. The
original course model that completed the task after 20,000 steps was SmolVLA,
not ACT.

The SmolVLA release is the non-DR 20,000-step checkpoint at
[`wangxun1010/smolvla-fruit-pick-0821@6649cc34576b1bf6a7ed1310251ece8c969dfafe`](https://huggingface.co/wangxun1010/smolvla-fruit-pick-0821/tree/6649cc34576b1bf6a7ed1310251ece8c969dfafe).
Its seven policy/configuration files contain 906,740,620 bytes. The SHA-256 of
the relative-path-sorted `sha256sum` stream is:

```text
97872e6db48a225a3425cbbb94894628acccaf7d7fe7c14d830526c5178ef555
```

The weight file SHA-256 is
`205bf82449f19542f2206dfeca007bcdcf214c6633b94159778154c4aecede72`.
It matches the local `smolvla_fruit_pick_0821/checkpoints/020000` output trained
on `datasets/fruit_pick`; it does not match the historical
`fruit_pick_dr` weight SHA-256
`2b0483f9aaa7bd4b56a304aa6e6c1362abeaabab8e29b307047ddcb11d5b1d72`.
The pinned `6649cc3...` revision contains the README/model card,
`license: apache-2.0` metadata and license link, SmolVLA/SmolVLM2 attribution,
training identity, load instructions, and limitations. Hub tree data confirms
that all seven policy/configuration files are unchanged from the earlier
`cdf720f...` payload commit, and a fresh fetch verifies the course checksums.
A separate standalone LICENSE, NOTICE, or second hosting manifest is not
required for this checkpoint gate.

The project lead approved Apache License 2.0 on 2026-10-30 for the
course-created checkpoint weights and packaging. LeRobot 0.6.0, the SmolVLA
base, and SmolVLM2 retain their upstream Apache-2.0 attribution; an ACT
checkpoint using TorchVision ResNet18
ImageNet-1K initialization must also retain the TorchVision BSD-3-Clause
notice. The M5.1 dataset and rendered YCB assets remain CC BY-NC 4.0 and are
not redistributed or relicensed by an Apache-2.0 checkpoint. The model card
states the upstream-model and training-asset boundary and links to this NOTICE
for the detailed course record.

Neither downloadable release is intended for real-robot safety, human interaction,
high-stakes automation, or claims of sim-to-real transfer, OOD robustness, or
stable success rate. The current-course reference AMD protocol observed 5/5
reference and 5/5 shifted-friction successes for the SmolVLA release, with
the small-sample and provenance limits recorded in `COMPATIBILITY.md`. These
counts do not establish a stable success rate, friction improvement, general
robustness, OOD behavior, or sim-to-real transfer. No M5 review performed a
new Hub upload; the project lead authorized the existing pinned artifacts to be
marked as course releases.

## 5. Approved decisions and remaining review

The project lead approved the following M0.5 decisions on 2026-08-28:

1. vendor only the four selected YCB objects under CC BY-NC 4.0;
2. use the Franka model bundled with the pinned Genesis version instead of
   copying the incomplete source directory;
3. release original source-course material under MIT while preserving the
   notices for depicted or embedded third-party material; and
4. keep datasets, checkpoints, and pretrained models outside the repository-wide
   license until each artifact is reviewed for M5.

The project lead approved the M5.1 fruit-pick dataset decisions on 2026-10-30,
including Xun Wang as creator and CC BY-NC 4.0 for the complete dataset
artifact. On the same date, the project lead approved the M5.2 checkpoint
identities, Apache-2.0 license for the course-created checkpoint portions,
required upstream attributions, independent CC BY-NC 4.0 dataset/YCB boundary,
model-card contract, and immutable versioning rules. On 2026-11-01 the project
lead accepted the reference AMD validation and the decision to keep ACT
unavailable. The corrected final release-readiness review confirmed that the
dataset revision `eab6739...` and SmolVLA revision `6649cc3...` satisfy their
card, license, attribution, and checksum gates without changing their payload
files. Exact artifact dependency and evaluation evidence remain recorded in
the course manifest and `COMPATIBILITY.md`; they do not need to be duplicated
as another Hub manifest. The project lead subsequently authorized both artifact
status promotions to `release` while explicitly leaving lesson `published`
status unchanged. No new Hub upload, Git push, GitHub Release, or deployment was
authorized.

M1.1 copied no third-party assets. M1.4 added only the four approved YCB objects
and their license/provenance files; the Franka model continues to come from the
pinned Genesis installation.
