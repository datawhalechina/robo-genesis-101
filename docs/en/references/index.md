# References and Third-Party License Audit

This index centralizes the upstream systems, papers, datasets, models, and license boundaries
that define the course. The detailed paper list for a topic remains in that lesson's
References section. A link or citation acknowledges a source; it is not permission to copy,
rehost, or relicense the linked material.

The repository's controlling records are the [third-party notice](https://github.com/datawhalechina/robo-genesis-101/blob/main/NOTICE.md),
[license policy](https://github.com/datawhalechina/robo-genesis-101/blob/main/LICENSE_POLICY.md), and
[compatibility matrix](https://github.com/datawhalechina/robo-genesis-101/blob/main/COMPATIBILITY.md).

## Core software and platform sources

| Source | Course use and pin |
|---|---|
| [Genesis documentation](https://genesis-world.readthedocs.io/en/latest/) | Simulation API reference; the course pins `genesis-world==1.3.3`. |
| [Genesis source](https://github.com/Genesis-Embodied-AI/genesis-world/tree/v1.3.3) | Version-pinned source used to check scene, entity, solver, control, asset, and camera behavior. |
| [Genesis 1.3.3 on PyPI](https://pypi.org/project/genesis-world/1.3.3/) | Package identity for the pinned release. |
| [PyTorch HIP semantics](https://docs.pytorch.org/docs/stable/notes/hip.html) | Explains why ROCm devices appear through the `torch.cuda` compatibility interface. |
| [LeRobot source](https://github.com/huggingface/lerobot/tree/v0.6.0) | Dataset, ACT, SmolVLA, training, and policy-loading behavior; course extras pin `lerobot==0.6.0`. |
| [PyAV documentation](https://pyav.org/docs/stable/) | Video decode/readback behavior used by the data lessons. |

These packages are installed dependencies, not copied source trees in this repository. Any
future copied code requires a file-level license review and a new `NOTICE.md` entry.

## Robotics, data, and learning references

| Topic | Primary reference used by the course |
|---|---|
| Robot kinematics | [Modern Robotics](https://modernrobotics.northwestern.edu/nu-gm-book-resource/) and the [Foundations of Robotics book](https://fbsbook.org/) |
| YCB objects | Calli et al., “Benchmarking in Manipulation Research: Using the Yale-CMU-Berkeley Object and Model Set,” [doi:10.1109/MRA.2015.2448951](https://doi.org/10.1109/MRA.2015.2448951) |
| Dataset aggregation | DAgger proceedings record, [PMLR v15](https://proceedings.mlr.press/v15/ross11a.html) |
| ACT | Paper record [arXiv:2304.13705](https://arxiv.org/abs/2304.13705) and [reference implementation](https://github.com/tonyzhaozh/act) |
| SmolVLA | Paper record [arXiv:2506.01844](https://arxiv.org/abs/2506.01844) and [LeRobot v0.6.0 implementation](https://github.com/huggingface/lerobot/tree/v0.6.0/src/lerobot/policies/smolvla) |
| Foundational domain randomization | [arXiv:1703.06907](https://arxiv.org/abs/1703.06907), [arXiv:1710.06537](https://arxiv.org/abs/1710.06537), and [arXiv:1910.07113](https://arxiv.org/abs/1910.07113) |
| Binomial uncertainty | Wilson's interval record, [doi:10.1080/01621459.1927.10502953](https://doi.org/10.1080/01621459.1927.10502953), and Newcombe's comparison record, [doi:10.1214/ss/1009213286](https://doi.org/10.1214/ss/1009213286) |

L08's acquisition-method survey and the remaining lesson-specific papers stay next to the
claims they support. They were retained as external links; no paper figures or full text were
copied into the repository.

## Audited YCB and Franka sources

### Vendored YCB subset

The repository includes only `011_banana`, `014_lemon`, `018_plum`, and `024_bowl` under
`assets/third_party/ycb/`.

- Immediate distributor: [ManiSkill](https://github.com/haosulab/ManiSkill).
- Original collection: [YCB Object and Model Set](https://www.ycbbenchmarks.com/).
- Reviewed archive: [ManiSkill2 YCB archive](https://huggingface.co/datasets/haosulab/ManiSkill2/resolve/main/data/mani_skill2_ycb.zip).
- Applicable recorded terms: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
- Local provenance, object list, archive checksum, modification record, legal text, and
  per-file checksums are stored beside the assets.

The files are byte-for-byte copies of the reviewed source and are not covered by the project
MIT License. The noncommercial restriction remains in force.

### Franka model

The course does not vendor the source-course Franka bundle. It resolves the model included
with pinned Genesis and retains attribution to:

- [MuJoCo Menagerie Franka Emika Panda](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda);
- the model-level [Apache-2.0 license](https://github.com/google-deepmind/mujoco_menagerie/blob/main/franka_emika_panda/LICENSE);
- [franka_ros robot description](https://github.com/frankaemika/franka_ros/tree/develop/franka_description).

“Franka” and “Panda” identify the source robot/model and do not imply endorsement or a
trademark grant.

## External datasets, checkpoints, and models

The following references are inputs named by lessons, not redistributed course artifacts:

| Material | Pinned reference | Redistribution decision |
|---|---|---|
| L13 fruit-pick dataset | [Hugging Face dataset revision `475e8c6...`](https://huggingface.co/datasets/wangxun1010/fruit_pick/tree/475e8c6ec7079c4c52b20a0221bf959acb541abd) | Link and opt-in workflow only; not vendored |
| L13 SmolVLA checkpoint | [Hugging Face model revision `cdf720f...`](https://huggingface.co/wangxun1010/smolvla-fruit-pick-0821/tree/cdf720f162e6ee86dbc856cdf15c5dcd4a673221) | Link and opt-in workflow only; not vendored |
| SmolVLA base | [revision `c83c316...`](https://huggingface.co/lerobot/smolvla_base/tree/c83c3163b8ca9b7e67c509fffd9121e66cb96205) | Local pinned snapshot for verified training; not rehosted |
| SmolVLM2 base | [revision `7b375e1...`](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct/tree/7b375e1b73b11138ff12fe22c8f2822d8fe03467) | Local pinned snapshot for verified training; not rehosted |
| RoboTwin dataset | [revision `a967b85...`](https://huggingface.co/datasets/TianxingChen/RoboTwin2.0/tree/a967b852afa21a9cbf19a198f7e653109042e87c) | L14 external input; not rehosted |
| LingBot-VLA-v2 6B base | [revision `11c703b...`](https://huggingface.co/robbyant/lingbot-vla-v2-6b/tree/11c703bf6a5c1f45b3b69168482da11fdbba53d7) | L14 external input; not rehosted |

M5 must review any proposed public course dataset or checkpoint separately, including creator,
source data, base model, license, immutable version, size, SHA-256, hosting URL, generation
configuration, and citation.

## L14 companion sources

L14 is bound to exact external revisions:

- [RoboTwin `266f3aa...`](https://github.com/RoboTwin-Platform/RoboTwin/tree/266f3aadf505a4f7fe9af0faa41a20f5f47cd123);
- [LingBot-VLA-v2 source `951475a...`](https://github.com/robbyant/lingbot-vla-v2/tree/951475ae1b1d87553e7dc47c97b53a3d695c0d13);
- [XPolicyLab `c37109c...`](https://github.com/XPolicyLab/XPolicyLab/tree/c37109c500be67d0dea6b36bf7337bbd26e763cd);
- [Robotwin-radeon-cloud companion `27b2f6f...`](https://github.com/ZiguanWang/Robotwin-radeon-cloud/tree/27b2f6fcb6c715e2cbb6db4431381f87c94b86ed).

The companion remains the runtime source of truth. The course does not modify it, copy its
container/runtime into the core installation, or convert the external model and dataset into
MIT-licensed materials.

## Repository license boundary

| Category | Current treatment |
|---|---|
| Original course code, prose, exercises, and original media | MIT License unless otherwise noted |
| Four vendored YCB objects | CC BY-NC 4.0; outside MIT |
| Installed software dependencies | Their upstream licenses; not vendored by installation metadata alone |
| Linked papers, datasets, checkpoints, and models | Citation/link only unless a separate audit approves redistribution |
| Generated datasets, checkpoints, logs, frames, and videos | Excluded from Git and not approved for redistribution by default |
| Datawhale logo, template animation, name, and trademarks | Outside the MIT grant; local brand-use authorization is not recorded and must be confirmed or the media replaced before release |

Do not paste a repository-wide MIT header onto third-party files or describe the project
license as relicensing them.

## M4 citation and license audit result

The M4 audit reviewed the bilingual lesson reference sections, public auxiliary pages,
`NOTICE.md`, `LICENSE_POLICY.md`, the YCB directory records, and the fixed L13/L14 source
identities. Its conclusions are:

- no new third-party binary, dataset, checkpoint, paper figure, or model was added by M4.6;
- the only vendored third-party course assets remain the four audited YCB objects;
- Genesis/Franka, LeRobot, papers, and model/data sources remain links or installed
  dependencies rather than copied source;
- L14 base models, RoboTwin data, and the companion image must not be rehosted by the course;
- generated outputs remain excluded unless M5 performs an artifact-specific audit;
- Datawhale brand/template-media authorization remains an explicit pre-release item.

External-link availability can change after this static audit. A broken link should be
updated to the same authoritative source or archived revision; it must not be replaced with
an unreviewed mirror.

## Contributor checklist

Before adding an external reference or material:

1. Prefer an official page, DOI, release tag, or immutable commit.
2. State which claim or implementation the source supports.
3. Determine whether the repository links, installs, embeds, modifies, or redistributes it.
4. Record the applicable license and attribution at the file or directory boundary.
5. Add checksum and modification records for vendored assets.
6. Keep datasets, checkpoints, and generated media out of Git unless repository policy
   explicitly approves them.
7. Update `NOTICE.md` when the disposition changes from link/dependency to copied material.

