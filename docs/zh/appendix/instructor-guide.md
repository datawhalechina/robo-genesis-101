# 教师指南

RoboGenesis 101 是一条渐进学习路径：机制讲义建立概念，notebook 暴露关键代码与证据，可复用
实现保证跨讲行为一致。不要把讲义和 notebook 教成彼此独立的两条轨道，也不要在学习者能够
审计 dataset 合同之前开始策略训练。

`course.json` 中的讲次时长是规划估计，不是课堂实测时间。下表是一种 12 周组织建议；教师可以
调整接触课时，但不能改变先修关系或证据标准。

## 学习成果

完成 13 讲核心路径后，学习者应能够：

- 诊断 Genesis runtime，并区分请求的 backend 与实际 backend 行为；
- 构建和检查 scene、刚体交互、机器人控制、IK、camera 与批量环境；
- 定义抓取任务、执行 scripted expert，并陈述机器可检查的成功判据；
- 录制并审计时间对齐的 LeRobot 演示数据；
- 解释 dataset sample、模仿学习监督关系和 domain provenance；
- 构造并检查 ACT/SmolVLA 训练命令与 checkpoint；
- 执行声明的闭环评估，并区分集成证据与任务性能。

L14 是可选进阶实践，不改变 13 讲核心课程的完成条件。

## 建议的 12 周顺序

| 周次 | 内容 | 教学重点 | 要求的证据 |
|---:|---|---|---|
| 1 | L01 | Runtime identity、状态/证据等级、CPU 与 AMD backend | 环境报告与最小场景结果 |
| 2 | L02–L03 | Scene 生命周期、状态读取、接触、摩擦、时间步与受控对照 | 测量状态与稳定物理对照 |
| 3 | L04 | 机器人模型、DOF index、关节状态与位置/速度/力控制 | 关节命令与测量状态检查 |
| 4 | L05 | FK、IK、末端执行器位姿与 camera 的作用 | 位姿误差，以及显式 camera 结果或 `SKIP` |
| 5 | L06 | 并行环境、批量控制与 selective update | 各环境 shape、误差与独立性检查 |
| 6 | L07 | 任务场景、经审计资产、任务状态与成功条件 | 场景/资产检查和成功判据推理 |
| 7 | L08 | 演示数据方法、scripted expert 阶段与 rollout trace | Action/state trace、阶段顺序与结果判据 |
| 8 | L09 | 采样频率、时间对齐、事务、schema 与吞吐 | 可回读双相机数据集与 metadata 审计 |
| 9 | L10–L11 | Dataset 解剖、模仿学习、domain randomization 与 provenance | 只读 dataset 审计与 bounded DR 证据 |
| 10 | L12 | ACT/SmolVLA 输入、训练命令、checkpoint 与 open-loop reload | Dry-run；GPU 路径还要求已审计 smoke checkpoint |
| 11 | L13 | 闭环协议、视频、报告、不确定性与 Capstone | 已审计报告/视频和范围明确的结论 |
| 12 | 核心证据 review；可选 L14 | 复现一条纵向交接；资源允许时另行介绍固定 RoboTwin/LingBot 实践 | 核心验收材料，或固定 profile 内的 L14 aggregate evidence |

规划课堂时应使用各讲 metadata 的时长。如果一周包含两讲，应把讲授、实验和 review 分配到
多次课，或把 notebook 作为有指导的实践任务。

## 面向硬件条件的教学安排

### CPU-first 基础路径

L01–L07 和 L10 有可接受的 CPU 完成路径，能够组成连贯的仿真、控制、任务和 dataset 读取基础。
建议所有学习者先完成这条共享路径，再预约 GPU 资源。

L08 可以在 CPU 上执行 scripted rollout 与数值证据。L09 和 L11 提供 CPU 诊断，但完整的数据
生成实验要求真实 camera 渲染；CPU+EGL 与参考 AMD+EGL 路径均已通过。使用
[环境配置与 fallback 附录](setup-and-fallbacks.md)准确标记诊断路径与完成路径。

### GPU 实验

L12 和 L13 为 `gpu-required`。实验前应验证：

- 实际加速器名称、PyTorch/HIP 版本与 Genesis backend；
- 精确 dataset repository ID 与本地 root；
- checkpoint 或模型 snapshot identity；
- 本地 output 容量与新的 run name；
- 计划离线执行时，所需 cache 已准备完毕。

硬件紧张时，可以让学习者围绕准备好的机器分组。分配 operator、protocol reviewer、artifact
auditor 和 evidence reviewer 等角色，让每个人参与完整合同，而不是只观看进度条。

L14 的必做路径需要独立固定 companion 和 4× W7900D。不要把它的 stack 安装进核心环境，也
不要宣传 CPU/单卡 fallback。

## M5 前的 artifact 准备

M4 不发布版本化示例 dataset、ACT/SmolVLA 课程 checkpoint 或通用 artifact 下载器。M5 前，
如果教师提供本地输入，应记录：

- 创建者与来源；
- 不可变 revision 或生成命令；
- dataset repository ID、schema 与本地 root；
- model/checkpoint 配置与 base-model provenance；
- 许可与再分发决定；
- 分发 artifact 时的文件大小与 SHA-256；
- artifact 实际支持的讲次与检查。

这些应称为教师准备的输入，而不是 RoboGenesis 官方发布件。不要为了方便而 rehost
LingBot-VLA-v2 base model、RoboTwin dataset 或 L14 image。

## 实验运行模式

每个可执行讲次都使用同一模式：

1. **预测：**学习者先写出预期 shape、物理关系或失败模式。
2. **Preflight：**验证版本、backend、输入与 output 目标。
3. **运行：**从 clean kernel 或 fresh process 执行，不依赖隐藏状态。
4. **检查：**检查测量值、图像/视频、metadata 与结构化报告。
5. **解释：**把证据连接到机制，并指出没有测试的内容。
6. **扩展：**只改变一个声明因子，其他协议保持不变。

Genesis 初始化是 process-wide 的。使用 subprocess 隔离 case 的讲次应继续保持隔离，不要把它们
简化成同一 kernel 内多次不兼容初始化。

## 证据与评分

按照学习者真正支持的最强结论评分：

| 证据等级 | 可接受结论 | 不充分的替代项 |
|---|---|---|
| Diagnostic | 配置、输入、调度或命令检查通过 | 声称核心实验已经运行 |
| 数值仿真 | 声明的状态/控制/物理关系通过 | 没有 frame/outcome 却声称 camera 或任务证据 |
| 数据 pipeline | Dataset 按匹配 schema 与时间合同提交并回读 | 声称该数据集能训练出有能力的策略 |
| 训练集成 | 真实优化与 checkpoint 保存/重载工作 | 把 loss 或 open-loop action 当成任务成功 |
| 闭环任务 | 声明 episode 使用有效 action、终止原因、报告和视频完成 | 把小样本 `k/n` 泛化成鲁棒策略质量 |
| 对比结果 | 不同 condition 共享声明的比较协议，并报告不确定性 | 把独立 aggregate 称为配对或因果结果 |

合格报告应说明 seed、请求/实际 backend、输入 identity、协议、结果计数、失败分类、artifact 和
未运行工作。人工视觉检查可以发现损坏或空视频，但不能覆盖 evaluator 的 success label。

## 需要纠正的常见误解

- `torch.cuda` 是 ROCm 使用的兼容命名空间；应检查 `torch.version.hip` 和实际设备。
- Notebook 执行到最后一个 cell，不代表所有 optional 或 skipped 分支都运行了。
- Action tensor 与测量 joint state 可以 shape 相同，但不代表同一种量。
- 本地路径不是 dataset repository ID，也不是 artifact version。
- 没有 provenance 的 domain randomization 不能构成可复现证据。
- shifted condition 只有被证明位于声明训练 support 之外时，才可以称为 OOD。
- 一步训练、下降的 loss 与 open-loop reload 都不是闭环成功。
- 匹配的调度 seed 不能控制 seed 并未决定的因素。
- `gpu-verified` 讲次不会自动成为 `published`。

## 教师准备清单

- 把讲义与 notebook 一起阅读，包括先修关系和失败分支。
- 在学习者将使用的机器上，从 clean kernel 运行本讲最低路径。
- 验证本地链接、dataset/checkpoint identity 与可用磁盘空间。
- 决定需要哪些视觉证据，并测试真实 camera/video 路径。
- 准备新的 output root；不能把已有学习者可见结果冒充新生成结果。
- 记录课堂上不会运行的所有硬件密集或外部下载步骤。
- L14 的排期、环境、存储与结论必须与核心路径分开。
- 分发任何外部材料前，review [引用与许可审计](../references/)。

## 课程完成 review

在确认一届学习者完成课程前，应确认他们至少能够追踪一条从 task specification 到
demonstration、dataset、checkpoint 和 closed-loop report 的纵向路径。artifact 可以来自不同
实验，但 identity 与接口必须明确。

课程教学完成不代表有权修改仓库 canonical 状态。只有仓库自身证据与验收门禁通过后，才修改
`course.json`。

