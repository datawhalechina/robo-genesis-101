# 引用与第三方许可审计

本索引集中列出定义课程的上游系统、论文、dataset、model 与许可边界。某一主题的详细论文列表
仍位于对应讲义的 References 章节。链接或引用表示承认来源，不代表有权复制、rehost 或重新
许可链接材料。

仓库控制性记录是[第三方材料说明](https://github.com/datawhalechina/robo-genesis-101/blob/main/NOTICE.md)、
[许可政策](https://github.com/datawhalechina/robo-genesis-101/blob/main/LICENSE_POLICY.md)与[兼容性矩阵](https://github.com/datawhalechina/robo-genesis-101/blob/main/COMPATIBILITY.md)。

## 核心软件与平台来源

| 来源 | 课程用途与固定版本 |
|---|---|
| [Genesis 文档](https://genesis-world.readthedocs.io/en/latest/) | 仿真 API 参考；课程固定 `genesis-world==1.3.3`。 |
| [Genesis 源码](https://github.com/Genesis-Embodied-AI/genesis-world/tree/v1.3.3) | 用于核对 scene、entity、solver、control、asset 与 camera 行为的版本固定源码。 |
| [PyPI 上的 Genesis 1.3.3](https://pypi.org/project/genesis-world/1.3.3/) | 固定 release 的 package identity。 |
| [PyTorch HIP 语义](https://docs.pytorch.org/docs/stable/notes/hip.html) | 解释 ROCm 设备为何通过 `torch.cuda` 兼容接口出现。 |
| [LeRobot 源码](https://github.com/huggingface/lerobot/tree/v0.6.0) | Dataset、ACT、SmolVLA、training 与 policy loading 行为；课程扩展固定 `lerobot==0.6.0`。 |
| [PyAV 文档](https://pyav.org/docs/stable/) | 数据课程使用的视频解码与回读行为。 |

这些 package 是安装依赖，不是复制到本仓库的源码树。未来若复制其中代码，需要 file-level
许可审查并在 `NOTICE.md` 新增记录。

## 机器人、数据与学习引用

| 主题 | 课程使用的主要引用 |
|---|---|
| 机器人运动学 | [Modern Robotics](https://modernrobotics.northwestern.edu/nu-gm-book-resource/) 与 [Foundations of Robotics book](https://fbsbook.org/) |
| YCB 对象 | Calli 等，“Benchmarking in Manipulation Research: Using the Yale-CMU-Berkeley Object and Model Set”，[doi:10.1109/MRA.2015.2448951](https://doi.org/10.1109/MRA.2015.2448951) |
| Dataset aggregation | DAgger 论文记录，[PMLR v15](https://proceedings.mlr.press/v15/ross11a.html) |
| ACT | 论文记录 [arXiv:2304.13705](https://arxiv.org/abs/2304.13705) 与[参考实现](https://github.com/tonyzhaozh/act) |
| SmolVLA | 论文记录 [arXiv:2506.01844](https://arxiv.org/abs/2506.01844) 与 [LeRobot v0.6.0 实现](https://github.com/huggingface/lerobot/tree/v0.6.0/src/lerobot/policies/smolvla) |
| 基础 domain randomization | [arXiv:1703.06907](https://arxiv.org/abs/1703.06907)、[arXiv:1710.06537](https://arxiv.org/abs/1710.06537) 与 [arXiv:1910.07113](https://arxiv.org/abs/1910.07113) |
| 二项比例不确定性 | Wilson 区间记录 [doi:10.1080/01621459.1927.10502953](https://doi.org/10.1080/01621459.1927.10502953)，以及 Newcombe 比较记录 [doi:10.1214/ss/1009213286](https://doi.org/10.1214/ss/1009213286) |

L08 的采集方法综述与其他讲次专用论文继续放在它们支持的具体结论附近。这些内容只保留外部
链接；仓库没有复制论文插图或全文。

## 经审计的 YCB 与 Franka 来源

### 内置 YCB 子集

仓库只在 `assets/third_party/ycb/` 中包含 `011_banana`、`014_lemon`、`018_plum` 与
`024_bowl`。

- 直接分发者：[ManiSkill](https://github.com/haosulab/ManiSkill)。
- 原始集合：[YCB Object and Model Set](https://www.ycbbenchmarks.com/)。
- 已审查归档：[ManiSkill2 YCB archive](https://huggingface.co/datasets/haosulab/ManiSkill2/resolve/main/data/mani_skill2_ycb.zip)。
- 已记录适用条款：[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)。
- 本地 provenance、对象列表、归档校验和、修改记录、许可全文与逐文件校验和均与资产放在
  同一目录。

这些文件是已审查来源的 byte-for-byte 副本，不受项目 MIT License 覆盖，非商业限制继续有效。

### Franka 模型

课程不 vendor 源课程中的 Franka bundle，而是解析固定 Genesis 自带模型，并保留下列署名：

- [MuJoCo Menagerie Franka Emika Panda](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda)；
- model-level [Apache-2.0 license](https://github.com/google-deepmind/mujoco_menagerie/blob/main/franka_emika_panda/LICENSE)；
- [franka_ros robot description](https://github.com/frankaemika/franka_ros/tree/develop/franka_description)。

“Franka”与“Panda”只用于识别来源机器人/model，不表示官方背书或商标授权。

## 外部 dataset、checkpoint 与 model

下列引用是讲义指定的输入，不是由课程再分发的 artifact：

| 材料 | 固定引用 | 再分发决定 |
|---|---|---|
| L13 fruit-pick dataset | [Hugging Face dataset revision `475e8c6...`](https://huggingface.co/datasets/wangxun1010/fruit_pick/tree/475e8c6ec7079c4c52b20a0221bf959acb541abd) | 仅链接与 opt-in workflow；不内置 |
| L13 SmolVLA checkpoint | [Hugging Face model revision `cdf720f...`](https://huggingface.co/wangxun1010/smolvla-fruit-pick-0821/tree/cdf720f162e6ee86dbc856cdf15c5dcd4a673221) | 仅链接与 opt-in workflow；不内置 |
| SmolVLA base | [revision `c83c316...`](https://huggingface.co/lerobot/smolvla_base/tree/c83c3163b8ca9b7e67c509fffd9121e66cb96205) | 已验证训练使用本地固定 snapshot；不 rehost |
| SmolVLM2 base | [revision `7b375e1...`](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct/tree/7b375e1b73b11138ff12fe22c8f2822d8fe03467) | 已验证训练使用本地固定 snapshot；不 rehost |
| RoboTwin dataset | [revision `a967b85...`](https://huggingface.co/datasets/TianxingChen/RoboTwin2.0/tree/a967b852afa21a9cbf19a198f7e653109042e87c) | L14 外部输入；不 rehost |
| LingBot-VLA-v2 6B base | [revision `11c703b...`](https://huggingface.co/robbyant/lingbot-vla-v2-6b/tree/11c703bf6a5c1f45b3b69168482da11fdbba53d7) | L14 外部输入；不 rehost |

M5 必须对任何拟公开的课程 dataset 或 checkpoint 分别审查，包括创建者、源数据、base model、
许可、不可变版本、大小、SHA-256、托管 URL、生成配置与引用。

## L14 companion 来源

L14 绑定到精确外部 revision：

- [RoboTwin `266f3aa...`](https://github.com/RoboTwin-Platform/RoboTwin/tree/266f3aadf505a4f7fe9af0faa41a20f5f47cd123)；
- [LingBot-VLA-v2 source `951475a...`](https://github.com/robbyant/lingbot-vla-v2/tree/951475ae1b1d87553e7dc47c97b53a3d695c0d13)；
- [XPolicyLab `c37109c...`](https://github.com/XPolicyLab/XPolicyLab/tree/c37109c500be67d0dea6b36bf7337bbd26e763cd)；
- [Robotwin-radeon-cloud companion `27b2f6f...`](https://github.com/ZiguanWang/Robotwin-radeon-cloud/tree/27b2f6fcb6c715e2cbb6db4431381f87c94b86ed)。

Companion 继续是 runtime 真相源。课程不修改它，不把它的 container/runtime 复制进核心安装，
也不把外部 model 与 dataset 转成 MIT 材料。

## 仓库许可边界

| 类别 | 当前处理 |
|---|---|
| 原创课程代码、文字、练习与原创媒体 | 除另有注明外采用 MIT License |
| 四个内置 YCB 对象 | CC BY-NC 4.0；不属于 MIT |
| 安装的软件依赖 | 保留上游许可；仅有安装 metadata 不等于源码被 vendor |
| 链接的论文、dataset、checkpoint 与 model | 除非单独审计批准再分发，否则只做引用/链接 |
| 生成的 dataset、checkpoint、日志、frame 与视频 | 默认不进入 Git，也没有默认再分发批准 |
| Datawhale logo、模板动画、名称与商标 | 不属于 MIT 授权；本地没有记录品牌使用授权，release 前必须确认或替换媒体 |

不要给第三方文件统一粘贴仓库 MIT header，也不要把项目许可证描述成对它们重新许可。

## M4 引用与许可审计结论

M4 审计覆盖双语讲义 References 章节、公开辅助页面、`NOTICE.md`、`LICENSE_POLICY.md`、YCB
目录记录，以及固定 L13/L14 来源 identity。结论如下：

- M4.6 没有新增第三方 binary、dataset、checkpoint、论文插图或 model；
- 唯一 vendor 的第三方课程资产仍是四个已审计 YCB 对象；
- Genesis/Franka、LeRobot、论文与 model/data 来源仍属于链接或安装依赖，不是复制源码；
- L14 base model、RoboTwin 数据与 companion image 不得由课程 rehost；
- 除非 M5 完成 artifact-specific 审计，否则生成 output 继续排除在外；
- Datawhale 品牌/模板媒体授权仍是显式 release 前事项。

外部链接在本次静态审计后仍可能变化。损坏链接应更新到同一权威来源或归档 revision，不能替换
为未经审查的 mirror。

## 贡献者检查清单

增加外部引用或材料前：

1. 优先使用官方页面、DOI、release tag 或不可变 commit。
2. 说明来源支持哪项结论或实现。
3. 判断仓库是链接、安装、嵌入、修改还是再分发该材料。
4. 在文件或目录边界记录适用许可与署名。
5. 对 vendor asset 增加 checksum 与修改记录。
6. 除非仓库政策明确批准，否则 dataset、checkpoint 与生成媒体不进入 Git。
7. 处理方式从链接/依赖变成复制材料时，更新 `NOTICE.md`。

