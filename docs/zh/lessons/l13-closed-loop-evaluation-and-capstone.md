---
lesson: L13
slug: closed-loop-evaluation-and-capstone
locale: zh
title: "闭环评估与 Capstone"
duration_minutes: 120
hardware: gpu-required
status: planned
---

# L13 · 闭环评估与 Capstone

> **课程状态：**`planned`。本讲先给出评估机制和证据规范。配套 notebook、最终评估报告
> 规范以及完整的 GPU 加渲染运行尚未通过验收。本页命令展示的是项目当前接口，不能据此认定
> L13 实验已经实际运行。

## 本讲在课程中的位置

[L08](/zh/lessons/l08-demonstration-acquisition-and-scripted-experts) 定义了把香蕉放入碗中的任务
及其几何成功判据；[L09](/zh/lessons/l09-synthetic-data-recording-and-throughput) 录制了时序对齐的
演示，[L10](/zh/lessons/l10-dataset-anatomy-and-imitation-learning) 让数据结构可以被检查，
[L11](/zh/lessons/l11-domain-randomization) 又补充了域参数的来源记录。
[L12](/zh/lessons/l12-act-and-smolvla-policy-training) 随后训练并保存了能够重新加载的 ACT 和
SmolVLA checkpoint。

L13 要把这条链路真正闭合起来：

```text
环境 → 演示 → 数据集 → 策略 checkpoint
 ↑                         ↓
 └──── 实时观测 ← 动作 ← 策略 rollout
```

现在不再是让 checkpoint 针对一条已录制样本输出一次动作。策略会看到仿真器的当前状态、输出
动作、改变环境，再根据动作造成的后果继续决策。L13 要在结果出现前便已确定的协议下，衡量这段
交互过程。

开始前，你应该已经能够：

- 解释 L08 中物体进入碗内的 containment 判据；
- 从课程 LeRobot 数据集中找出两路相机特征、9 维机器人状态、9 维动作、任务文本和 FPS；
- 阅读 L11 引入的域随机化 provenance；
- 将一个数值 checkpoint 与保存的 processors 一起审计，判断它属于 ACT 还是 SmolVLA；
- 区分只用于验证工程链路的 checkpoint 和获得了有意义训练预算的策略。

### 聚焦重点的 120 分钟路线

| 时间 | 主题 | 学习产出 |
|---:|---|---|
| 0–15 分钟 | 反馈与证据层级 | 解释实时 rollout 为什么能检验离线 probe 无法暴露的行为 |
| 15–35 分钟 | 冻结评估协议 | 在查看结果前写出 protocol manifest |
| 35–50 分钟 | 判据、dwell、超时与发散 | 把一段判据序列归结为一个回合结果 |
| 50–65 分钟 | 参考、支持范围内、偏移和 OOD 条件 | 根据训练 provenance 命名一种比较条件 |
| 65–80 分钟 | 计数、Wilson 置信区间与配对 seed | 解读小样本结果而不过度声称精度 |
| 80–95 分钟 | Capstone 运行前检查 | 审计环境、数据集、checkpoint、相机、动作和输出路径 |
| 95–110 分钟 | 5 回合参考条件 smoke | 生成实时 rollout 视频和结构化结果 |
| 110–120 分钟 | 失败证据与报告设计 | 起草有明确边界的结论及 held-out 后续实验 |

第一次下载模型、L12 的长时间训练以及大规模 checkpoint sweep 都放不进这 120 分钟。请在课前
准备好模型文件。如果机器无法在同步课堂内完成第二组 5 回合条件，可以在课后继续运行并作为
Capstone 作业提交。

## 学习目标

完成 L13 后，你应该能够：

1. 解释闭环反馈如何让策略行为、环境状态和未来观测相互影响，以及误差累积和恢复能力为何由此
   成为策略能力的一部分；
2. 设计公平、可复现的任务级评估，使不同策略或不同评估条件下的结果具有清楚、可比较的含义；
3. 综合定量与定性证据，判断结果的不确定性、泛化边界、主要失败模式以及结论适用范围；
4. 把环境、数据、策略学习和闭环评估连接成一条完整的机器人学习工作流，并提出有证据依据的
   下一步改进。

## 闭环以后，发生了什么变化？

### 三个证据层级回答不同问题

| 证据 | 信息流 | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| 训练 loss | 已录制观测与动作 → 优化器 | 配置的目标能否在抽取的训练 batch 上计算 | 策略能否控制不断变化的环境 |
| 动作回放或单样本推理 | 已录制动作 → 仿真器，或已录制观测 → 一次预测 | 数据解码、特征兼容性以及输出 shape/有限性 | 策略改变自己的下一次观测后能否恢复 |
| 闭环 rollout | 实时观测 → 策略 → 动作 → 环境 → 下一次实时观测 | 一个已声明 rollout 协议下的任务行为 | 未测试条件或真实机器人上的表现 |

开环结果并非没有价值。L09 的回放能发现录制器故障，L12 的单样本推理能发现 processor 缺失。
问题不在于这些检查太弱，而在于不能把它们解释成超出其证据范围的结论。

### 反馈会暴露误差累积与恢复能力

![已录制样本的检查会在动作后果返回策略之前停止。闭环中，实时世界相机、腕部相机和机器人状态经过预处理进入策略；9 维目标驱动控制器和 Genesis，得到的新状态再成为下一次观测。独立的第三人称相机只记录证据，不进入策略。](/diagrams/l13-feedback-loop-zh.svg)

*课程原创图。下方才是真正的因果闭环；上方说明为什么已录制样本或动作回放无法检验恢复能力。
第三人称相机只用于留存证据。*

假设夹爪接近香蕉时横向偏了两厘米。在离线样本上，模型输出的数值看起来仍可能完全合理；但在
实时 rollout 中，这个动作会移动腕部相机、改变接触，甚至旋转或推走香蕉。下一次决策所面对的
状态，可能是专家演示很少到达的。一个有能力的策略要么从偏差中恢复，要么在闭环中明确失败。

动作分块不会消除反馈。ACT 和 SmolVLA 可能把多个预测目标放进队列，但运行时最终仍要根据新的
观测请求下一个动作块，因此评估协议必须记录实际执行 horizon。每个回合开始前还必须调用
`policy.reset()`，防止上一回合的动作队列或循环状态泄漏到下一次试验。

### 课程 rollout 包含两个时间尺度

系统按照数据集 FPS 查询策略。两次查询之间维持当前 9 维关节位置目标，同时让 Genesis 按课程
控制频率推进：

```text
策略查询频率 = 数据集 FPS
仿真/控制频率 = 100 Hz
每次策略查询对应的平均仿真步数 = 100 / 数据集 FPS
```

当查询频率为 30 FPS 之类的数值时，这个比值不是整数。评估器会累积小数余量，而不是每次查询
都独立取整，从而让长期平均比例保持正确。在本课程的执行设计中，一个仿真步无法容纳多次策略
决策，因此策略 FPS 高于控制频率属于无效协议。

策略发出的是关节位置目标，不是力矩、笛卡尔速度或末端位姿。一个 shape 正确且数值有限、但
语义错误的向量，可能比明显的 shape 错误更危险。因此，数据集和 checkpoint 身份必须始终与
动作一起记录。

## 在查看结果前冻结协议

一个评估数字其实是下面这段完整陈述的缩写：

> 这个 checkpoint 在这些环境中，按照这套观测、动作与时序合同和这条成功规则，对这些由 seed
> 确定的回合尝试了这个任务。

改变其中任何一项，实验就变了。因此，可复现的运行从 protocol manifest 开始，而不是从一个
百分比开始。

![冻结的协议清单确定 artifact、场景和相机、时序与动作语义、任务和成功规则，以及带 seed 的评估条件。每个回合随后依次经历 reset、实时 rollout、瞬时判据、连续保持计数和终止原因。全部回合结束后，才汇总成功次数与总回合数、Wilson 置信区间、分条件记录和 rollout 视频。](/diagrams/l13-evaluation-protocol-zh.svg)

*课程原创图。蓝色表示运行前冻结的字段，橙色表示运行时判定，紫色表示回合结束后形成的证据。
从 predicate 指向 dwell 的箭头十分关键：一帧为真不等于整个回合成功。*

### Manifest 中应该包含什么？

| 边界 | 需要冻结并记录的内容 |
|---|---|
| 代码与运行环境 | course/code revision 或 dirty 状态、Python、Genesis、LeRobot、PyTorch、HIP/CUDA runtime、实际设备、渲染后端 |
| 数据集 | 逻辑 repository ID、解析后的本地根目录、特征 schema、FPS、相机 shape/key、任务表、domain provenance |
| Checkpoint | 解析后的数值 checkpoint、策略类型、训练数据集身份、模型/processors、action horizon、相机重命名、可用时的 artifact revision/checksum |
| 场景与观测 | 场景/资产、world/wrist 映射、图像 resize、状态顺序、哪一路相机只用于证据 |
| 动作与时序 | 9 维关节位置语义、策略 FPS、100 Hz 保持/降频规则、策略 reset 行为 |
| 任务 | 抓取对象池、放置目标、位置/偏航角 reset、任务文本、容差、对象调度 |
| 回合规则 | containment 判据、dwell 时长、超时、异常和发散如何处理 |
| 采样 | 条件名称、回合数、base seed 与逐回合 seed、domain seed、是否平衡调度 |
| 输出 | 结果 schema 版本、JSON/CSV、日志、视频目录、人工标签、跳过的工作 |

这不是实验结束后补填的文书，而是测量本身的定义。如果某个字段未知，就如实记为 unknown 并
缩小结论范围；不要看完视频后再悄悄还原一个方便的取值。

### “同一个场景”不是充分的审计

数据录制和评估即使都调用项目的 scene builder，仍可能在影响策略的地方有所不同：

- 场景或资产 revision；
- 物体位置与偏航角扰动；
- world/wrist 相机标定或图像分辨率；
- Layer-A 外观以及 Layer-B 动力学/相机设置；
- 策略 FPS 与动作保持方式；
- 任务文本、抓取对象调度、容差、dwell 或超时。

评估相机的图像会先 resize 到数据集 metadata 记录的 shape，再交给策略 processor。SmolVLA
随后还可能把 `world/wrist` 重命名为它使用的标准相机 key。第三人称视频相机只负责记录，不得
加入策略特征。应逐项核对这些事实，而不是只说“同一个仿真器”便假定二者等价。

### 配对 seed 改善控制，但本身不能消除不确定性

对于第 `i` 个回合，当前评估器使用 `base_seed + i`。当抓取对象不止一种时，balanced 模式会
先生成数量尽可能相等的对象安排，再以可复现方式打乱顺序。在不同 checkpoint 或不同条件中
复用同一组 seed，就能得到相互配对的初始任务实例。

这种设计减少了一种比较噪声，但它不会让不同 domain 条件完全相同，不保证跨平台逐 bit
确定性，也不能自动证明观察到的差异具有统计显著性。一个回合由 seed、代码、资产、后端、协议
和 domain 配置共同定义。

## 把任务判据转化为回合结果

### 空间判据由 L08 定义

对于碗这个放置目标，课程判据检查两个几何事实：

```text
within_footprint = horizontal_distance < min(success_tol, bowl_rim_radius)
inside_bowl = object_aabb_bottom_z < bowl_rim_z - rim_margin
instantaneous_containment = within_footprint and inside_bowl
```

使用物体 AABB 的底部，可以让细长的香蕉在中心仍靠近碗沿时，只要已有一部分稳定落入碗中就
满足判据；同时也会排除仍被夹在碗上方的物体。L13 复用 L08 的判据，评估器不会另造第二套放置
几何定义。

### 连续保持时间会排除只出现一帧的“飞过”

物体横穿碗、发生弹跳或仍在夹爪中运动时，某一瞬间也可能满足 containment。令 `c_t` 表示策略
第 `t` 步之后的瞬时判据：

```text
dwell_frames = max(1, ceil(dwell_seconds × policy_fps))

仅当下列判据全部为真，才在第 t 步成功：
    c_t, c_t-1, ..., c_t-dwell_frames+1
```

任何一次判据为假都会把连续计数清零。课程要求至少连续保持 0.4 秒；在 5 FPS 下，也就是连续
两次检查成功。当 `0.4 × FPS` 不是整数时，必须使用 `ceil`：既然要求“至少 0.4 秒”，就不能
向下取整成更短的时间。

超时不会免除 dwell。若在超时边界只有最后一帧为真，却没有达到所需的连续次数，这个回合仍然
失败。真正成功后，评估器可以维持最后一个动作并额外录制一小段仅用于观察的结尾，让人看清
物体是否静止；这些额外帧不会改变回合结果或策略步数。

::: warning 计划中的运行门禁
L13 的正式证据要求连续 dwell 规则通过配套实验的合同测试，其中包括超时边界。在本讲仍为
`planned` 时，不要把未经检查的本地评估器结果发布成已经验证的课程成功率。
:::

### 策略失败与基础设施错误不是同一类事件

一个正常开始的回合可能以下列方式结束：

- `success`：判据连续满足了完整 dwell；
- `timeout`：未在规定时间内完成任务；
- `diverged`：Genesis 报告物理发散，计为任务失败；
- `invalid_action`：策略返回的 shape 错误或数值非有限，计为策略/运行时失败，并保留独立原因。

checkpoint 缺失、数据集不可读、对象不存在、指定 GPU 不可用或观测相机缺失则不同。这些是
run-level 的运行前错误，应在任何回合进入分母前中止；否则会把基础设施问题误报成策略行为。

## 根据训练 provenance 定义评估条件

### “打开 DR”不等于“OOD”

分布相关的名称描述的是相对关系：评估条件必须与已知训练分布比较后才能命名。

| 标签 | 在本讲中的含义 |
|---|---|
| 参考条件（Reference） | 本次报告预先声明的基线条件；理想情况下与已审计的数据生成条件对齐 |
| 未见但仍在支持范围内（Unseen in-support） | 新 seed 或新 domain 样本仍来自训练 provenance 记录的同一参数支持范围 |
| 分布偏移（Shifted） | 至少一个因素发生变化，但 provenance 缺失或范围重叠，无法声称评估范围与训练范围不相交 |
| 分布外（OOD） | 某个明确因素的取值/范围可证明位于训练数据记录的支持范围之外，同时其他重要因素保持受控 |

![一棵判定流程根据训练 provenance 区分四类评估条件。报告中预先声明的基线是参考条件；另一条件若缺少 provenance 或与训练范围重叠，则是分布偏移；支持范围可审计时，完全落在已记录范围内的新取值属于未见但仍在支持范围内，可证明不相交的取值范围才可称为 OOD，且其他重要因素需要保持受控。](/diagrams/l13-condition-labels-zh.svg)

L11 已记录的摩擦和质量范围内换用新随机 seed，只会产生未见过的实例，并不会自动变成 OOD。
只有 provenance 能证明新的摩擦区间与训练范围不相交，而且该区间仍能构成有效且数值稳定的
任务时，才能把它称为物理因素上的 OOD。把香蕉换成柠檬属于对象/任务偏移，与摩擦系数偏移并非
同一种结论。

即使参考条件与数据生成参数一致，策略自己的错误也可能把闭环轨迹推入演示从未覆盖的状态。
因此，本讲的“支持范围内”只描述经过审计的 domain 参数，并不声称闭环访问到的完整状态分布与
训练时完全相同。

### 先隔离一个因素，再组合多种偏移

第一次比较时，适合固定 checkpoint、任务、seed、对象调度、超时、判据和 dwell，只改变一个
domain 因素。这样既更容易解释结果，也能降低激进的组合 DR 破坏接触稳定性的风险。

运行前写下：

```text
参考条件：
改变的因素：
训练数据对该因素的支持范围：
评估取值/范围：
支持关系：支持范围内 | 分布偏移 | 范围不相交的 OOD
保持不变的因素：
安全性/任务有效性检查：
```

如果训练 provenance 缺失，标签最多只能写到 `shifted`。如实表达标签的不确定性，比武断却没有
依据的 OOD 声明更可靠。

## 先报告计数，再报告百分比

在一个固定条件下，每个完成的回合贡献一个二元结果 `Y_i`：

```text
k = sum(Y_i)
n = 已完成的评估回合数
观测成功率 = k / n
```

始终报告“`k` 次成功 / `n` 个回合”。单独一个百分比会掩盖它究竟来自 5 个回合还是 500 个
回合。还要在汇总值旁保留发散次数、分对象计数、条件名称和逐回合表格。

### 成功率是估计，不是最终判决

观测成功率 `k/n` 准确描述的是已经运行的这些回合发生了什么，却不能让我们确定策略真正的成功
概率。即使完整复用同一套冻结协议，只换一组回合 seed 再运行一次，有限样本中初始状态难易程度
不同，成功次数也可能改变。

因此，分母会改变一个百分比所承载的证据量。`1/1`、`5/5` 和 `50/50` 显示出来都是 100%，但
可信程度并不一样：一次成功提供的可重复性证据远少于五十次。只报告“100%”会把这个差异隐藏
起来。

置信区间能让这种抽样不确定性显现出来。项目使用双侧 95% Wilson score interval，因为它在
本讲常见的小样本和接近 0 或 1 的极端结果下仍有合理表现。例如：

| 观测结果 | 点估计 | 95% Wilson 置信区间 | 结果能够支持的说法 |
|---|---:|---:|---|
| `0/5` | 0% | 约 `[0%, 43%]` | 没有观察到成功，但不能证明成功绝无可能。 |
| `3/5` | 60% | 约 `[23%, 88%]` | 60% 是当前最佳单点估计，但 5 个回合仍留下很大不确定性。 |
| `5/5` | 100% | 约 `[57%, 100%]` | 观察到的回合全部成功，但尚未证明每次都能成功。 |
| `50/50` | 100% | 约 `[93%, 100%]` | 点估计同样是 100%，却有多得多的数据支持。 |

`5/5` 应理解为：“策略在观察到的五个回合中全部成功；数据太少，所以明显低于 100% 的成功率
仍与这一结果相容。”不能把它读成“已经知道该策略永远有 100% 成功率”。同理，`0/5` 记录了
这一批样本全部失败，却没有证明潜在成功概率恰好为零。

区间中的 95% 描述的是反复使用这套构造方法时的覆盖性质，而不是承诺未来有 95% 的回合会
成功。在二项模型和固定协议下，如果反复抽取许多批样本并分别构造区间，大约 95% 的区间会
覆盖那个固定但未知的真实成功概率。

为什么不使用最简单的正态近似？在 `0/n` 或 `n/n` 时，简单近似可能退化为 `[100%, 100%]`
这类宽度为零的区间；偏偏在小样本边界处，我们更应该谨慎。Wilson 区间始终位于 `[0, 1]`
之内，并且在这些边界上仍会保留非零的不确定性。

你不需要背下公式，但应该能找出 `k` 与 `n`、读懂所得区间，并让结论强度与区间宽度相称。对于
`p_hat = k/n` 和 `z = 1.96`，仓库按下式计算：

```text
denom  = 1 + z²/n
center = (p_hat + z²/(2n)) / denom
half   = z/denom × sqrt(p_hat(1-p_hat)/n + z²/(4n²))
interval = [max(0, center-half), min(1, center+half)]
```

这个区间只涵盖一套冻结协议下的抽样不确定性。它不涵盖有偏的 seed 选择、仿真器误差、成功
规则变更、checkpoint 选择或 sim-to-real gap。两个条件各自的 Wilson 区间是否重叠，也不能
单独构成有效的配对显著性检验。

因此，聚焦路线中的 5 个参考条件回合只是集成 smoke，不是性能 benchmark。Capstone 会在一个
held-out 条件下复用同样 5 个 seed，得到透明的 `5 + 5` 教学比较。报告必须保留较宽的置信区间，
并明确指出该样本不足以支持稳定的模型排名。

不存在通用的“足够回合数”常量。更大规模的研究应根据期望精度、预期变异、对象/domain 分层和
计算成本，在查看结果前确定回合预算。

### 用同一组 seed 做公平比较

协议部分已经解释过，为什么两个条件应该复用相同的 seed 调度。下面用一个例子说明，这会如何
帮助我们阅读结果。假设参考条件和偏移条件得到以下五个回合：

| Seed | 参考条件 | 偏移条件 | 这个 seed 的结果怎样变化？ |
|---:|---|---|---|
| `1000` | 成功 | 成功 | 成功不变 |
| `1001` | 成功 | 失败 | 成功 → 失败 |
| `1002` | 失败 | 失败 | 失败不变 |
| `1003` | 失败 | 成功 | 失败 → 成功 |
| `1004` | 成功 | 失败 | 成功 → 失败 |

参考条件合计 `3/5`，偏移条件合计 `2/5`。汇总计数告诉我们，这批样本中偏移条件少成功了一次；
逐 seed 配对表则揭示了更多信息：两个初始实例由成功变为失败，一个由失败变为成功，另两个没有
变化。这个因素并没有以相同方式影响所有实例。

如果两个条件使用互不相关的 seed，偏移条件可能只是恰好抽到了更难的物体初始位姿。复用 seed
`1002` 意味着，在冻结协议允许的范围内，参考和偏移回合从同一个预定任务实例开始。声明的条件
因素可以改变后续轨迹——这恰好是比较要观察的对象。

课程比较只需记住三件事：

1. 两个条件使用同一组 seed；
2. 按 seed 并排列出两个条件的结果；
3. 同时报告两边汇总的 `k/n`，以及成功/失败发生翻转的回合。

五组配对仍然只是教学规模的样本。它们能指出哪些回合发生变化，并引导视频检查，却无法独自
证明某个条件会稳定地导致更高或更低成功率。这样的结论需要更多回合和专门用于配对结果的统计
方法，超出了核心实验范围。

## Rollout 证据解释汇总数字掩盖的现象

评估视频由课程的两路观测画面和一路诊断画面横向拼接而成：

```text
世界相机 | 腕部相机 | 第三人称视频相机
策略输入   策略输入        仅作证据
```

检查每个画面是否都在推进、方向是否符合预期，以及是否对应所记录的回合。使用 `yuv420p` 的
H.264 文件通常更容易播放，同时要求帧的宽高为偶数。文件有名字或容器能够解码，并不能证明
录下的是正确相机。

有用的人工失败分类包括：

- 超时前没有发生有效运动；
- 接近或对齐偏差；
- 碰撞把物体推走；
- 抓取失败或夹爪过早闭合；
- 抬升或运输途中掉落；
- 到达碗上方但没有释放；
- 释放位置不满足 containment；
- 持续弹跳，始终无法满足 dwell；
- 物理发散。

这些是通过观察得到的分类，不能只根据 `success=false` 自动推断。请观看 rollout，并引用画面中
可见的证据。

## 在一个冻结条件下运行一个 checkpoint

先完成最小而完整的闭环评估单元：

```text
一个 checkpoint + 一份数据集合同 + 一个冻结条件
    → 5 个闭环回合
    → 逐回合记录 + 汇总统计 + rollout 视频
```

这次运行要回答的是：某一个明确的 checkpoint 能否在一个明确条件下执行指定任务。它还不是
checkpoint sweep，也不是参考/偏移条件比较。每组命令行参数都会冻结协议的一部分：

| 评估选择 | 参数 | 冻结的内容 |
|---|---|---|
| 策略 artifact | `--policy-path` | 要加载的确切数值 checkpoint |
| 数据集合同 | `--repo-id`、`--dataset-root` | 匹配的 FPS、图像 shape、相机 key 和特征 schema |
| 运行设备 | `--device` | 策略推理必须使用的加速器 |
| 回合样本 | `--episodes`、`--seed`、`--balanced` | 分母以及可复现的 seed/对象调度 |
| 任务与超时 | `--pick`、`--place`、`--max-seconds` | 任务实例以及每个回合的最长时间 |
| 证据输出 | `--save-video`、`--video-dir`、`--results-out` | 视频和结构化结果的保存位置 |

把每个 `CHOOSE_...` 占位符替换为审计后的实际值。policy path 必须指向数值 checkpoint，数据集
身份必须匹配训练它时使用的合同。每次运行使用独立输出目录，避免不同条件的结果被意外混在
一起。

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

这个例子中，`--episodes 5 --seed 1000` 从 1000 开始安排五个可复现的回合 seed。评估器加载
checkpoint，依据数据集合同构造实时观测，运行反馈回路，并先为每个回合记录一行数据，再计算
汇总计数和 Wilson 置信区间。

在 ROCm PyTorch 中，`--device cuda` 使用 PyTorch 共享的设备 API；请核对输出的硬件确实是
预期的 AMD GPU，并且 HIP 可用。静默回退 CPU 不满足本讲的 GPU-required 路径。

::: warning 当前接口边界
当前 CLI 能从 metadata 恢复数据集 FPS 和图像特征，也会在可用时恢复已保存的 SmolVLA 相机
重命名；它会输出逐回合明细、计数、Wilson 置信区间和视频。本讲仍为 `planned`，因此请另行
保留完整命令和环境信息：最终通过验收的 Capstone 报告 schema 和全部运行前检查还不是已验证的
公开接口。
:::

### 这次 5 回合运行能够证明什么？

第一次运行会产生集成证据和一份小样本行为记录。二者都有价值，但不能支持关于策略的所有
结论：

| 这次运行能够证明 | 这次运行不能证明 |
|---|---|
| checkpoint 能够与匹配的 processors 和数据集特征一起加载 | 策略已经可靠 |
| 实时观测进入策略，策略动作也确实影响仿真器 | 未测试条件下的表现 |
| 场景 reset、策略 reset、超时、判据和 dwell 得到执行 | 对偏移或 OOD 条件的鲁棒性 |
| 逐回合记录、计数、Wilson 置信区间和视频能够产出 | 相对于另一 checkpoint 的稳定排名 |

`0/5`、中间任意计数和 `5/5` 都是有效评估输出。判断闭环评估链路是否有效，应看每个回合是否
遵循冻结协议并留下完整证据。策略行为的结论必须与观测到的 `k/n`、置信区间、视频和声明范围
一起报告；不能设置一个未公开的成功率门槛，只有跨过它才承认运行有效。

L12 只训练一步的 smoke checkpoint 或许能证明评估器可加载并运行策略，但它的 rollout 结果
不能作为策略经过充分训练的证据。

## 可选扩展：比较已保存的 checkpoint

`eval_sweep.py` 会在一次训练 run 中发现数值 checkpoint。省略 `--steps` 时，它会评估找到的
所有可用数值 checkpoint；指定 `--steps` 则只比较明确列出的步骤。每个 checkpoint 都使用同一
套冻结任务协议和 seed 调度，避免初始任务实例差异干扰 checkpoint 比较。核心 Capstone 不要求
这项扩展，只需评估一个选定 checkpoint。

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

只保存了一个 checkpoint 的训练 smoke 只能形成一个点，不能形成学习曲线。存在多个 checkpoint
时，成功率可能上升、持平、振荡，也可能下降。配对 seed 能改善可比性，却不能消除所有 checkpoint
选择或训练混杂因素。请描述实际观察到的曲线，不要预先承诺它会“不断上升”。

运行成本随 checkpoint 数量直接增长：

```text
rollout 数量 = checkpoint 数量 × 回合数
```

例如，3 个 checkpoint 各自评估 5 个配对回合，需要运行 15 次 rollout。工具会把逐 checkpoint
和逐回合结果写入 `sweep.json`，把简要 checkpoint 汇总写入 `sweep.csv`，并把观测成功率曲线
写入 `success_curve.png`。

::: warning 可选路径，尚未通过 L13 验证
当前实现已经提供 checkpoint sweep，但本讲尚未接受一次完整的多 checkpoint GPU 加渲染 sweep
作为课程证据。把它当作探索性路径，而不是核心单 checkpoint Capstone 的必做要求。
:::

## Capstone：用可追溯证据回答一个问题

Capstone 从一个策略问题开始，而不是从一份命令检查清单开始：

> 对于一个身份明确的 checkpoint，它在一个参考条件和一个已声明的 held-out 条件下的闭环结果，
> 能让我们得出什么结论？

答案必须能够沿运行环境、训练数据、checkpoint、评估协议和实时 rollout 一路向前追溯。任何一环
缺少证据都会削弱结论；最后的百分比再漂亮，也无法弥补前面断开的链路。

![Capstone 依次通过六道证据门：环境身份、数据集与 provenance、checkpoint 与 processors、冻结的参考和 held-out 条件、实时反馈 rollout，以及结论范围明确的报告。每道门都说明它能够证明什么，以及哪些更强的结论仍在边界之外。](/diagrams/l13-capstone-evidence-chain-zh.svg)

*课程原创图。由左向右阅读：每道门回答一个必要的子问题，同时限制可以传递到下一道门的
结论。*

### 把每道证据门读成一个问题

| 证据门 | 子问题 | 最低证据要求 | 结论边界 |
|---|---|---|---|
| 1. 环境 | 声明的运行环境真的执行了吗？ | 环境报告、实际 GPU/后端和一帧实时相机画面 | 证明实际使用的 runtime；尚未说明数据或策略行为。 |
| 2. 数据集 | 策略依赖哪些演示和训练支持范围？ | 数据集身份、特征 schema、任务和已有 provenance | 让训练输入可解释；不能证明已经学到有用策略。 |
| 3. Checkpoint | 正在评估哪个策略 artifact？ | 数值 checkpoint 身份、保存的 processors 及数据集匹配关系 | 让策略包可重建；不能证明其动作能完成任务。 |
| 4. 协议 | 具体要比较什么？ | 冻结的任务/成功规则，以及使用同一组 5 个 seed 的参考与 held-out 条件 | 让两个结果可比；不会预先决定结果。 |
| 5. Rollout | 策略闭合反馈回路后发生了什么？ | 两个条件的完整逐回合记录、终止原因、计数和视频 | 只证明这套协议下的仿真行为。 |
| 6. 报告 | 证据支持什么结论，结论到哪里为止？ | `k/n`、Wilson 置信区间、配对记录、限制和复现命令 | 得到可追溯答案；不证明普遍鲁棒性或 sim-to-real transfer。 |

如果缺少一道门，就应该暂停或削弱结论。例如，没有数据集 provenance，就无法把改变后的条件
论证为 OOD；checkpoint 身份不固定，其他学习者便无法复现结果；没有实时 rollout，checkpoint
能够加载也不能升级成任务性能结论。

::: warning Checkpoint 可用性
本仓库目前没有发布带版本的课程 checkpoint。请使用自己在 L12 训练的 checkpoint，除非 release
artifact manifest 明确列出了其他选择。不要虚构 URL、静默搜索无关输出，或把提供的 checkpoint
说成自己训练所得。
:::

### 沿证据链撰写报告

根据这些证据门填写一份紧凑的报告，无需复制每一讲的全部输出：

```text
问题：
  对于 checkpoint [身份]，参考条件与 [held-out 条件] 的 rollout 能支持什么结论？

环境与 artifact：
  [运行环境身份] + [数据集身份] + [checkpoint 身份]

冻结协议：
  [任务和成功规则] + [配对 seed] + [条件定义]

观测证据：
  参考条件：[k/n 和置信区间]
  Held-out：[k/n 和置信区间]
  [配对结果变化、终止原因和视频证据]

结论：
  这些证据支持 [仅限已测试协议的结论]。

不能证明：
  [未测试条件、稳定排名、真实机器人表现……]

下一项实验：
  [能够减少最重要剩余不确定性的一项改变]

复现方式：
  [命令和输出位置]
```

只要评估有效，且诊断沿证据链展开，即使零次成功也能完成 Capstone。反过来，再高的观测成功率
也无法补偿身份不明的 checkpoint 或查看结果后才修改的协议。

讲义负责解释推理：为什么每道门必要，以及它允许什么强度的结论。配套实验负责机械细节：在
preflight、audit、rollout 和 report cells 中收集完整版本字段、特征名、processor 文件、manifest、
日志和输出路径。你不必记住所有字段，只需能够解释最终结论为什么依赖它们。

## 按边界诊断失败

1. **环境、GPU 或渲染：**确认项目环境、软件包版本、`torch.cuda.is_available()`、
   `torch.version.hip`、实际设备、Genesis 后端和一帧实时相机画面。要求 GPU 执行却回退到 CPU，
   表示完整路径检查失败。
2. **数据集身份：**确认 repository ID、解析后的根目录、metadata、任务、FPS、相机 key/shape、
   动作名称和 domain provenance，不要搜索一个方便的替代品。
3. **Checkpoint 身份：**在启动 Genesis 之前，检查数值目录、策略类型、processors、训练数据集、
   action horizon 和相机重命名。
4. **协议运行前检查：**在昂贵工作开始前，拒绝非正数的回合数/超时、空抓取对象池、不支持的
   对象、高于控制频率的策略 FPS、无效条件或输出路径冲突。
5. **实时观测：**检查 9 维有限状态、HWC `uint8` world/wrist 帧、resize 行为和 processor 期望的
   key；不要让视频相机进入策略输入。
6. **策略动作：**每回合重置策略状态；动作应用前要求得到一个数值有限的 9 维关节目标，然后再
   检查动作队列以及查询/保持时序。
7. **仿真：**找出接触爆炸、NaN 发散、无效 reset 或不安全的偏移范围，并保留失败 seed 和条件。
8. **任务结果：**结合视频与 predicate trace，区分接近、抓取、抬升、运输、释放、containment、
   dwell 和超时。
9. **采样与报告：**核对分母、缺失/重复 seed、分对象平衡、条件隔离、pooled 标签和区间输入。
10. **策略能力：**只有前九层边界都成立后，才讨论改变数据覆盖、训练预算、checkpoint 选择或
    模型容量。

## 检查点与练习

### 概念检查

1. 单样本 checkpoint probe 缺少哪一条因果边？
2. 为什么必须在回合之间重置策略状态和动作块队列？
3. 在 5 FPS 和 0.4 秒 dwell 下，需要连续多少次 predicate 为真？使用 `ceil` 时，7 FPS 又是多少？
4. 为什么超时处的一帧 containment 为真仍然是失败？
5. 两个成功率可比之前，哪些事实必须一致？
6. 为什么来自 L11 同一参数范围的新 seed 可以是未见实例，却仍在支持范围内？
7. 为什么相机条件发生偏移不等于它自动成为 OOD？
8. Wilson 置信区间涵盖哪种不确定性？还有哪些不确定性不在其中？
9. 为什么物理发散仍应留在分母中？
10. 哪些证据能够区分“评估器成功运行”和“策略确实有用”？

### 协议练习

在配套 notebook 的 `l13-protocol` cell 中修改一条合成 predicate trace。运行前先预测它的最大
连续次数和回合结果。至少加入一条“最后一帧为真，但连续次数短于 dwell 要求”的 trace，并解释
超时为什么不能把它提升为成功。

### 单因素条件练习

在 `l13-condition-plan` 中只改变一个 domain 因素。依据训练 provenance，把它标记为
`unseen in-support`、`shifted` 或 `OOD`，说明哪些因素保持不变，以及新范围为何仍能维持一个
有效任务。如果 provenance 不能支持所选标签，就把它降级为 `shifted`。

### 失败证据练习

在 `l13-result-audit` 中，使用观看前就写好的规则选择一个实际失败回合，例如“第一个 timeout”。
添加一个人工类别和两条 rollout 中可见的现象。不要只根据汇总成功率推断训练数据或模型架构
方面的原因。

### Capstone 结论练习

在 `l13-capstone-report` 中写三句话：

1. 当前证据能支持什么；
2. 当前证据不能支持什么；
3. 下一项什么实验能减少最重要的不确定性。

下一项实验应该只改变一个有依据的因素，或增加预先声明的回合预算。没有先诊断边界就笼统地说
“训练更久”，并不是基于证据的建议。

## 总结

- 闭环评估衡量的是一个因果反馈过程：策略的每个动作都会改变下一次观测，从而暴露误差累积或
  恢复能力。
- 只有在 artifact、场景、观测、动作、时序、任务、seed、条件和成功协议全部冻结后，成功率才有
  明确含义。
- L08 的 containment 必须连续满足 dwell 才成为回合成功；超时和发散都不会构成例外。
- 参考条件、支持范围内、分布偏移和 OOD 都相对于训练 provenance 定义。打开随机化开关不构成
  OOD 证明。
- 报告成功次数与总回合数、Wilson 置信区间、分条件/对象明细、逐回合配对记录和 rollout 证据。
  即使观测成功率是 0% 或 100%，5 个回合仍然只是 smoke。
- Capstone 把环境、数据集、checkpoint、协议、实时 rollout 和报告证据连接起来。通过一道证据门
  永远不会自动获得后一道门才允许的结论。
- Checkpoint sweep 是可选扩展，成本随已保存 checkpoint 数量增长；必须描述实际观察到的曲线，
  不能假定它一定上升。

## 参考资料

- Wilson，[“Probable Inference, the Law of Succession, and Statistical
  Inference”](https://doi.org/10.1080/01621459.1927.10502953)——本课程对单个二项成功比例使用的
  score interval。
- Brown、Cai 与 DasGupta，[“Interval Estimation for a Binomial
  Proportion”](https://doi.org/10.1214/ss/1009213286)——比较多种二项比例区间的表现，包括 Wald
  区间的局限。
- [LeRobot 0.6.0 policy control utilities](https://github.com/huggingface/lerobot/blob/v0.6.0/src/lerobot/common/control_utils.py)——
  项目评估器使用的固定版本 `predict_action` 路径。
- [LeRobot 0.6.0 policy factory](https://github.com/huggingface/lerobot/blob/v0.6.0/src/lerobot/policies/factory.py)——
  重新加载 ACT 和 SmolVLA checkpoint 时使用的策略与前后处理器构造逻辑。
- [Genesis World 文档](https://genesis-world.readthedocs.io/en/latest/)与
  [Genesis World 1.3.3 on PyPI](https://pypi.org/project/genesis-world/1.3.3/)——仿真器文档和课程使用的
  确切版本。
- [RoboGenesis 101 任务判据](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/grasp_demo.py)、
  [单 checkpoint 评估器](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/eval_policy.py)、
  [checkpoint sweep](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/eval_sweep.py) 和
  [共享统计实现](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/stats.py)——
  本讲所述的当前项目行为和实现边界。
- [RoboGenesis 101 兼容性记录](https://github.com/datawhalechina/robo-genesis-101/blob/main/COMPATIBILITY.md)——
  已验证平台、历史 checkpoint probe，以及仍未验证的结论。
