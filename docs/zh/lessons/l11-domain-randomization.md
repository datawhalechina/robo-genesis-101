---
lesson: L11
slug: domain-randomization
locale: zh
title: "域随机化"
duration_minutes: 90
hardware: gpu-recommended
status: gpu-verified
---

# L11 · 域随机化

> **课程状态：** `gpu-verified`。双语诊断路径、CPU+EGL 完整路径，以及参考 R9700 上的
> bounded DR 录制、回读与 provenance 完整路径均已通过。正常实验需要相机渲染，因此仍推荐
> 使用 GPU。无渲染路径只检查配置和调度逻辑，不能代替视觉与数据集实验。

## 本讲在课程中的位置

[L09](./l09-synthetic-data-recording-and-throughput.md) 录制了对齐、经过成功判定的演示；
[L10](./l10-dataset-anatomy-and-imitation-learning.md) 随后打开这些 episode，检查 metadata 与
媒体，并在不让轨迹跨 split 泄漏的前提下构造模仿学习 target。

前两讲有意使用了一套较窄的固定仿真设置。L11 要回答另一个问题：怎样让未来的学习器接触受控
变化，同时不悄悄改变任务，也不丢失“到底采样了什么”的记录？

```text
L09：对齐演示 + episode 事务
  ↓
L10：可读 sample + statistics + 可信的 episode split
  ↓
L11：域分布 + 有界随机化 + provenance
  ↓
L12：ACT / SmolVLA 优化与 checkpoint 重载
  ↓
L13：在已声明条件下进行闭环评估
```

域随机化比本课程的 recorder 更广。它是一种从一族仿真环境中生成数据或经验的方法。配套实验
使用 L09 recorder，是因为模仿学习是本课程下一位数据消费者；强化学习 rollout、感知数据和
鲁棒控制实验同样可以使用这一思想。

开始之前，你应该已经能够：

- 识别 L07 场景中的桌面、YCB 物体、Franka、world camera 和 wrist camera；
- 根据 L03 解释为什么摩擦属于接触对，而不能只孤立地看一个刚体；
- 区分一次 L08 attempt 与成功的任务结果；
- 解释为什么 L09 只提交通过验收的 episode；
- 从 L10 中识别 episode 边界和 dataset identity。

### 一条聚焦的 90 分钟路线

| 时间 | 主题 | 学习产出 |
|---:|---|---|
| 0–12 分钟 | reality gap、domain 与 distribution | 把 DR 定义为跨一族采样环境进行学习 |
| 12–27 分钟 | 六类 domain parameter | 判断某项变化属于 observation、physics、actuation 还是 disturbance |
| 27–38 分钟 | 相邻概念、分布策略与采样时机 | 分清随机化什么、怎样选择域，以及值何时改变 |
| 38–50 分钟 | 课程 Layer A | 解释 build-time 颜色/FOV 变化及其限制 |
| 50–62 分钟 | 课程 Layer B | 解释 reset-time friction、mass 与 world-camera 变化 |
| 62–72 分钟 | seed、attempt、success 与随机化记录 | 追溯每条已保存 episode 使用的 appearance seed、runtime seed 和实际采样参数 |
| 72–84 分钟 | 固定 seed 预览与 2-episode DR smoke | 产出可检查图像和可读本地数据集 |
| 84–90 分钟 | split、selection effect、诊断与证据边界 | 设计可信的后续对照实验 |

在部分机器上，渲染、重建场景和录制成功 episode 可能比课堂本身耗时更久。这个小实验验证的是
链路集成，不代表生产级采集预算。

## 学习目标

完成 L11 后，你应该能够：

1. 把域随机化解释为：在任务含义基本不变时，从 domain-parameter distribution 中采样多个环境；
   并说明它为什么可能缓解过拟合，却不保证 sim-to-real 迁移；
2. 识别主要的 observation、sensor、geometry、physics、actuation、timing 与 disturbance
   随机化，并将其与 task randomization、data augmentation、system identification 和 domain
   adaptation 区分开；
3. 选择具有物理意义的采样时机和有界范围，再用固定 seed 生成并审计本课程较小的 appearance、
   camera 与 dynamics 子集；
4. 区分“randomizer 确实运行过”的证据与“覆盖有效、policy 鲁棒、闭环成功或真实迁移”的证据。

## 一个任务，一族环境分布

### Domain 不只是一种图像风格

用 `xi` 表示选定一个具体环境的参数。根据问题不同，`xi` 可以影响：

- 由物理状态生成的 observation；
- 执行 action 之后发生的 transition；
- policy command 到 actuator response 的转换；
- initial condition；
- trajectory 中施加的 disturbance。

域随机化从一个分布中采样这些参数：

```text
domain xi ~ p_phi(xi)
learning objective = expected loss or return over sampled domains
```

对监督感知或模仿学习而言，这意味着从多个采样 domain 构造 example，而不是只依赖一个固定的
renderer 和 simulator。对强化学习而言，它意味着在多个采样环境上优化 return，而不是只优化
一个 nominal model。

参数向量可能很大，但核心思想很简单：

```text
一个 nominal simulator                 一族随机化 simulator
----------------------                 ------------------
一套 camera calibration               camera calibration distribution
一种 contact model                    contact-parameter distribution
一种 actuator response               actuator/timing distribution
一种 rendered appearance             rendering distribution
```

真实系统不会自动落在这个环境族之内。选择 `p_phi(xi)` 是对不确定性的建模决策，不是已经覆盖
所有重要差异的证明。

![固定任务被置于一族 domain 分布中。六类参数描述“什么可以变化”，分布策略与采样时机则是两条独立设计轴；本课程已实现的参数以高亮显示。](/diagrams/l11-domain-parameter-map-zh.svg)

*课程自制图。图中把“随机化什么”“怎样选择 domain”和“何时采样”分开。高亮项只是本讲的
实践子集，不代表完整覆盖。*

### 为什么要随机化？

学习器可能利用 simulator 中任何稳定的捷径。视觉模型可能把目标与某一种固定桌面颜色或相机
构图绑定；控制器可能依赖某个摩擦系数、某种延迟或 physics engine 的数值伪影。捷径在 nominal
simulator 中可能表现很好，换成稍有差异的 simulator 或真实机器人后却会消失。

域随机化相当于在环境维度上施加 regularization：若某个特征或行为在多个采样 domain 中都有用，
它就不那么依赖一个 nominal model。从概率视角看，这个分布表示我们对目标环境的不确定性。
两种视角都不意味着随机性越多越好。无关变化会浪费数据，不合理变化可能让仿真不稳定，或使
policy 学得过分保守。

::: warning 域随机化不是迁移证书
不同的画面只能说明某个 rendering knob 改变了；有限次 rollout 只能说明采样仿真仍可数值运行。
二者都不能证明 policy 性能更好。要声称 sim-to-real，必须冻结训练协议，并在真实目标系统上
完成评估。
:::

## 哪些内容可以随机化？

领域内没有唯一强制的列表。对机器人问题，一种实用分类方式是询问数据生成和控制流程的哪一部分
存在不确定性。

| 类别 | 代表性参数 | 所建模的差异 | L11 实验覆盖 |
|---|---|---|---|
| Rendering 与 appearance | 颜色、纹理、材质、roughness、metallic/specular response、灯光、阴影、背景、clutter、distractor | 仿真与部署时的视觉外观差异 | 仅桌面颜色和受约束物体颜色 |
| Camera 与 sensor | intrinsics、extrinsics、FOV、畸变、曝光、模糊、RGB/depth noise、dropout、bias、drift、量化、latency；proprioception、force/torque 或 tactile noise | 理想传感与物理传感的差异 | camera FOV 和静态 world-camera pose |
| Geometry 与 kinematics | 物体形状/尺度、collision geometry、link length、joint zero/range、camera mount tolerance、terrain geometry | CAD、标定、制造和装配误差 | 未实现为 DR |
| Physics、contact 与 numerics | mass、inertia、center of mass、friction、restitution、compliance、damping、gravity、contact model、solver setting、timestep | transition 中的模型和参数误差 | shared friction ratio 和 per-object mass ratio |
| Actuation、control 与 timing | motor strength、efficiency、gear ratio、controller gain、limit、joint friction、backlash、dead zone、action noise、delay、control rate | command 与实际执行行为的差异 | 未实现 |
| Disturbance 与 system variation | 外力/力矩、冲击、风、payload、terrain、磨损、损坏、通信 jitter | 未建模的部署变化 | 未实现 |

类别会重叠，因为一个参数可能改变多个 channel。物体尺度既改变像素，也改变接触几何；simulator
timestep 是数值参数，但修改 action hold time 也可以近似 controller latency。world-camera
extrinsics 在概念上属于 sensor domain，即使本仓库在 reset 时把它与 physics 参数一起修改。

### 视觉随机化只是其中一个分支

![香蕉入碗任务保持不变，四个采样 visual domain 分别改变 appearance、camera geometry、scene 与 lighting 或 sensor pipeline。青色标签标出 L11 已实现的纯色、FOV 和 world-camera pose 子集；灰色标签表示实验尚未实现的概念参数。](/diagrams/l11-visual-domain-randomization-zh.svg)

*课程原创示意图，参数类别参考 Tobin et al.（2017）的视觉随机化工作，并非对论文图片的复制。
场景卡片用于建立 observation 变化的直觉，不代表当前 simulator 已实现图中的全部参数。*

Tobin et al. 为 sim-to-real object localization 随机化了物体和背景纹理、物体和相机位姿、
FOV、灯光、distractor 与图像噪声。这个有影响力的例子解释了为什么人们经常从视觉切入 DR，
但它并没有限定整个技术领域。

本仓库当前随机化的是**颜色**，不是纹理。启用 object recolor 时，`build_scene()` 会用从该物体
专属 HSV prior 采样的纯色 surface 替换原 mesh texture；它不会采样 texture map、材质粗糙度、
灯光或背景。把当前实现称作“纹理随机化”会夸大代码实际做的事情。

### Dynamics randomization 会进入控制回路

![机器人闭环从 observation 依次经过 policy、action、actuation、physics、下一状态和 sensor mapping。采样的 domain parameter 可以进入 actuation、transition、sensing 与 disturbance 边界；图中只有 object mass 和 shared friction 高亮为 L11 已实现项。](/diagrams/l11-dynamics-control-loop-zh.svg)

*课程原创闭环示意图，实例参考 Peng et al.（2018）与 OpenAI et al.（2019）的 dynamics
randomization 工作，并非对论文图片的复制。青色表示当前实验实现，灰色与橙色参数在本讲只作
概念介绍。*

Peng et al. 展示了更宽的 dynamics vector：robot link 和物体 mass、damping、friction、table
height、position-controller gain、两次 action 之间的时间，以及 observation noise。OpenAI 的
灵巧操作工作还覆盖了 geometry、actuator property、backlash、latency、observation corruption、
visual parameter 和 disturbance。

这些例子说明 `friction + mass` 是有用实验，却不是 dynamics randomization 的完整定义。真实
control stack 还包含标定误差、饱和、带宽、延迟、量化和相关噪声。哪些参数重要取决于具体任务
和平台。

## 明确任务边界

域随机化通常希望一个 policy 或 model 能够在不同环境中解决同一个定性任务。这个边界由实验
操作定义，而不是由参数名称自动决定。

以物体位置为例，它可能表达不同含义：

- 对“在工作台任意位置找到香蕉”，position 是同一任务内部的 domain variation；
- 对初态已有严格规定的 benchmark，改变 position 会产生另一个 task instance；
- 把目标从 bowl 改到任意 shelf，可能同时改变 task semantics 与 difficulty。

本课程使用以下约定，以便证据可以审计：

| 概念 | 改变了什么 | 课程示例 | 核心问题 |
|---|---|---|---|
| Task randomization | initial condition、goal 或 task instance | 物体 `xy/yaw`、选中的 pick object、place target | 请求的任务是否仍是同一 instance 和 difficulty？ |
| Domain randomization | observation、transition、actuation、timing 或 disturbance domain | 颜色、FOV、friction、mass、camera pose | 同一任务能否承受合理的部署变化？ |
| Data augmentation | 已经生成的 sample | 读取后 crop、颜色变换或图像噪声 | 变换是否保留 sample semantics？ |
| System identification | 对真实参数或不确定性的估计 | 从 trajectory 推断 mass、friction 或 latency | 哪些 simulator setting 最能解释测量结果？ |
| Domain adaptation | 利用 target data 对齐 representation、model 或 simulator | 对齐仿真与真实图像 feature | 怎样利用 target-domain information 减小差异？ |

文献有时会采用不同边界。在宽泛的 MDP 表述中，initial state 和 goal 可以被纳入 domain
parameter；一些 visual-DR 系统也会包含本课程称作 data augmentation 的在线图像 distortion。
与其争论某个标签是否普遍正确，不如明确说明当前约定以及 transformation 发生在哪个阶段。

## 三条独立设计轴

六类参数回答**什么发生变化**。一套 DR 方案还需要回答两个问题：**怎样选择分布**，以及
**何时应用一次采样**。混淆这些轴会导致“camera pose 属于 dynamics”之类说法，仅仅因为它在
reset 时与 mass 一起更新。

### 怎样选择 domain distribution？

Muratore et al. 以 static、adaptive 和 adversarial randomization 组织算法版图。对本讲而言，
下面的问题地图比一长串算法名称更有用：

| 策略 | 分布行为 | 所需信息 | 课程深度 |
|---|---|---|---|
| Static/manual DR | 手工设计的范围保持固定 | 工程判断、规格或先前实验 | 实现并检查 |
| Measurement-informed DR | 由测量或 system identification 确定 nominal value 与 uncertainty | target-system observation | 概念连接 |
| Curriculum / automatic DR | 随模型表现扩大或缩小边界 | 训练期间在采样边界上的表现 | 概念概览 |
| Adaptive DR | 更新分布以减小仿真/目标 trajectory mismatch | target-domain data 和 update rule | 概念概览 |
| Adversarial / active DR | 寻找困难或信息量高且仍有效的 domain | adversary、acquisition objective 或 robustness criterion | 概念概览 |

例如，OpenAI 的 automatic domain randomization（ADR）从窄范围开始，再根据 performance 调整
各个边界。它是在训练期间修改 `p_phi(xi)` 的方法，而不是一种新的物理参数类别。

常见的 independent-uniform 设计很方便：

```text
friction_ratio ~ Uniform(low_friction, high_friction)
mass_ratio     ~ Uniform(low_mass, high_mass)
```

它仍可能是糟糕的模型。真实参数可能相关、带条件、偏斜或多峰；camera exposure 与 illumination
相关，payload 与 center of mass 相关，更大的物体也可能需要不同的有效初始位姿。对每个 knob
独立采样，可能产生各参数单独合法、组合起来却不可能存在的条件。

### 应该在什么时候采样？

| 生命周期 | 合适示例 | 需要保持的不变量 |
|---|---|---|
| Build time | mesh/material 选择、geometry、Genesis 在 `scene.build()` 前固定的参数 | 已构建场景保持声明过的结构 |
| Episode/reset time | mass、friction、固定标定偏差 | 物理设备不会在 trajectory 中途改变身份 |
| Step time | 不相关 sensor noise、action noise、通信 jitter、外部 disturbance | 快速变化遵循明确的 stochastic process |
| Event time | 依碰撞触发的 perturbation、已声明 fault 或 payload event | 记录 trigger 与 state transition |

采样频率应服从物理意义，而不是实现便利。每帧重采样 mass、物体尺寸或固定安装相机位姿，会创造
另一个通常不真实的系统；只在 build 时采一个白噪声值，也无法表示逐帧 sensor noise。

## 选择能保持任务可用的范围

DR distribution 应该宽到足以覆盖相关不确定性，又窄到能够维持物理可行性和任务含义。采集之前，
应按四项约束检查每个候选范围：

1. **语义有效性：** 物体、observation、instruction 与 success predicate 仍然指向同一任务。
2. **物理有效性：** mass 保持正值，geometry 不穿插，camera frustum 覆盖工作区，solver input
   保持有限。
3. **运行有效性：** expert 或学习过程能够遇到该条件，不会让数据集坍缩到几乎没有 accepted
   example。
4. **目标相关性：** 范围表示一项已说明的不确定性或 stress condition，而不是仅仅因为有这个
   knob 就添加变化。

::: tip 从窄范围和单一变量开始
固定 task pose 和其他 domain parameter，只改变一个类别；检查采样值与 observation 后，再组合
多个因素。这不能证明最终分布最优，但会让配置错误和 confounding 更容易被发现。
:::

更宽不一定更好。过宽分布可能使 simulator 不稳定、破坏视觉身份、增加 expert failure，或迫使
policy 把容量浪费在无关极端上；过窄分布则可能只增加噪声，却没有覆盖目标变化。因此，选定的
范围属于 experiment provenance，而不应只藏在源码默认值里。

## 本课程有意实现一个子集

领域 taxonomy 告诉我们“可以建模什么”，仓库中的 Layer A 和 Layer B 则告诉我们 Genesis
“何时可以应用已选子集”。

| 课程层 | 采样边界 | 已实现参数 | 重要缺项 |
|---|---|---|---|
| Layer A | `scene.build()` 之前 | table RGB、受约束 object RGB、world/wrist/video vertical FOV | texture、material、lighting、background、geometry |
| Layer B | 每次 `EnvRandomizer.reset()` | shared contact-surface friction ratio、per-object mass ratio、静态 world-camera `pos/lookat` | inertia/CoM、damping、restitution、robot morphology、actuator/timing 与 sensor noise |

这是一种实现生命周期，而不是通用 DR taxonomy。Layer B 因 runtime path 得名，但其中的 camera
extrinsics 仍是 observation-side parameter。两层可以组合，却不代表它们的影响在统计上独立。

### Layer A：build-time appearance 与 intrinsics

场景 build 之前，将 `SceneDomainRandomizationConfig` 传给 `build_scene()`：

```python
from robo_genesis.build_scene import SceneDomainRandomizationConfig, build_scene

scene_dr = SceneDomainRandomizationConfig(
    enabled=True,
    table_color_jitter=0.15,
    randomize_object_color=True,
    fov_jitter_deg=2.0,
    seed=0,
)
bundle = build_scene(scene_dr=scene_dr)
```

一个由 `scene_dr.seed` 初始化的 NumPy RNG stream 决定该次 build 的所有 Layer-A draw。

#### 桌面颜色

桌面顶板和桌腿从各自配置的 RGB 值开始。每个 channel 独立接收
`[-table_color_jitter, +table_color_jitter]` 内的 uniform offset，再 clip 到 `[0, 1]`。Clip 能
保证输出合法，但 amplitude 过大时会让 sample 集中到 0 或 1。

#### 受约束的物体重着色

只有列在 `DR_APPEARANCE_PRIORS` 中的物体会被重着色。hue、saturation 与 value 从该物体专属
interval 内采样，再转换为 RGB。这个 prior 是语义护栏：香蕉应保持为可识别的目标物体，而不是
变成任意颜色。

当前 surface 是纯色。它会替换原 mesh texture，不会合成新纹理。解读 montage 时必须保留这个
实现限制。

#### Camera FOV

每个已创建 camera 的 vertical FOV 都会独立接收 `[-fov_jitter_deg, +fov_jitter_deg]` 内的
uniform offset。FOV 是 camera intrinsic parameter：它不移动 camera center，却会改变构图。
安全配置既要让所有结果 FOV 为正，也要让操作工作区保持可见。

当前 build path 会固定这些值。新的 Layer-A sample 需要新建 scene，因此必须支付
`scene.build()` 成本。

### Layer B：reset-time physics 与 world-camera pose

`DomainRandomizationConfig` 嵌套在 `RandomizationConfig` 中，并由
`EnvRandomizer.reset()` 应用：

```python
from robo_genesis.randomize import DomainRandomizationConfig, RandomizationConfig

runtime_dr = DomainRandomizationConfig(
    enabled=True,
    friction_ratio_range=(0.7, 1.3),
    mass_ratio_range=(0.8, 1.2),
    cam_pos_jitter=0.01,
    cam_lookat_jitter=0.02,
)
reset_cfg = RandomizationConfig(
    randomize_pick=False,
    dr=runtime_dr,
)
```

上述数值 interval 是当前 friction/mass class default，加上用于说明的小幅 camera offset；它们
不是其他 robot、object、solver 或 task 的通用安全范围。

reset 顺序经过有意设计：

```text
恢复机器人并放置物体
  → 采样并应用 friction + mass
  → 在采样 dynamics 下 settle
  → 扰动静态 world camera
  → 选择任务
```

在 settle 前应用 dynamics，意味着初始接触已经使用本 episode 的 domain。之后再移动 camera
是安全的，因为它不会改变物理 settle。

#### 摩擦属于接触双方

[L03](./l03-rigid-body-physics-and-stable-simulation.md) 已经建立了这里使用的 Genesis 1.3.3
contact-pair 规则：

```text
effective_pair_friction = max(friction_side_A, friction_side_B)
```

如果只缩放低摩擦物体，未改变的 finger 或 table friction 可能主导这个最大值。因此 randomizer
会把同一个 ratio 应用到 YCB object、Franka link 和 table entity。这是针对锁定 engine 的有意
实现，不是所有 simulator 都适用的通用摩擦定律。

#### 质量按比例变化且不会累积

对每个物体，randomizer 只捕获一次原始 per-link base mass，并采样一个正 ratio：

```text
sampled_mass = base_mass * mass_ratio
mass_shift   = base_mass * (mass_ratio - 1)
```

按“正负若干千克”做绝对扰动，可能让轻物体质量变成负数；正的 multiplicative ratio 能保持
符号。每次从缓存的 base mass 重新计算 shift，也能避免多次 reset 在上一 episode 的变化上继续
累积。Robot mass 保持不变，因此已经调好的 Franka gain 不会被悄悄重新解释。

#### 只移动静态 world camera

`cam_pos_jitter` 与 `cam_lookat_jitter` 分别围绕已配置 world-camera baseline 独立扰动三个坐标。
wrist camera 是 eye-in-hand，每一步都根据所附着的 hand link 更新；本讲不随机化它的 mounting
transform。

实现暴露 `last_friction_ratio` 和每个物体的 `last_mass_ratio` 供诊断使用。要使数据集可复现，
还必须记录 camera pose 与配置范围。

## Seed 必须服从采集事务

一个 seed 不足以标识一条已录制 episode，因为 recorder 有两套调度，并且会拒绝失败 attempt。

![Build-time appearance seed 只有在达到 committed-success quota 后才前进，而 runtime seed 在每次 attempt 后都会前进；失败 attempt 从训练数据集丢弃，但仍保留在 provenance 中。](/diagrams/l11-domain-schedule-zh.svg)

*课程自制图，以 `dr_rebuild_every=1` 为例。Attempt 0 失败并消耗 runtime seed，却不推进
appearance domain；attempt 1 和 2 分别提交 episode 0 和 1，两者之间发生一次 rebuild。*

当前确定性调度为：

```text
appearance_base_seed = dr_seed if provided else seed
appearance_domain_index = committed_successes // dr_rebuild_every
appearance_seed = appearance_base_seed + appearance_domain_index

runtime_episode_seed = seed + attempt_index
reset(runtime_episode_seed)
```

这里有两个不同 counter：

- 无论 rollout 成功还是失败，`attempt_index` 都会前进；
- 只有 recorder 接受一条 episode 后，`committed_successes` 才会前进。

因此，失败 attempt 会在 runtime seed 序列中形成缺口，却不会消耗当前 appearance domain 的
success quota。使用 `dr_rebuild_every=1` 时，触发下一个 appearance build 的是第一次成功，
不是第一次 attempt。

### 为什么失败 attempt 也属于 provenance

L09 正确地把失败 attempt 排除在 success-only demonstration dataset 之外。这个事务规则会在
DR 下产生 **selection effect**：scripted expert 更容易失败的 domain 会贡献更少、甚至完全没有
committed demonstration。请求采样的分布可能不同于最终保存数据集中的分布。

把失败 frame 保存成训练演示不是解决办法。应该在标准 sample schema 之外保留 audit trace。
L11 实验合同使用课程自有的 provenance sidecar，至少包含：

- schema 和 implementation version；
- requested range 与 base seed；
- attempt index 与 runtime seed；
- appearance-domain index 与 seed；
- 实际 friction、每个物体的 mass ratio 和 world-camera pose；
- success/commit 结果；
- 如果发生提交，则记录 committed episode index。

若 LeRobot finalize 能保留额外课程 metadata file，首选位置是
`meta/robo_genesis_domain_randomization.json`；否则 recorder 必须使用明确的 sibling
provenance path。它不能修改标准 LeRobot feature schema，也不能只把 provenance 藏在目录名中。

::: warning 当前实现边界
现有 recorder 已经实现两套 seed 调度和 DR knob，但 L11 专属参数验证与 provenance sidecar
属于配套实验的实现合同。在这些工作完成并验证之前，console output 或名为 `dr` 的目录都不等价于
machine-readable audit trail。
:::

## 按 episode 划分，同时考虑 domain

L10 已拒绝 random frame split，因为同一 trajectory 的相邻 frame 会跨 train/evaluation 泄漏。
L11 又增加了第二个 grouping variable：domain。

| 评估问题 | Train/evaluation 关系 | 可信标签 |
|---|---|---|
| Policy 能否处理同一已声明范围内的新 episode？ | episode 和 seed 互斥，parameter distribution 相同 | in-distribution holdout |
| 它能否处理训练中没有出现的已声明条件？ | 留出 seed group、appearance group 或 parameter subrange | held-out condition |
| 超出训练 support 后会怎样？ | 一个或多个参数位于已声明训练范围之外 | stress 或 OOD evaluation |

如果连续多个成功 episode 共享同一次 appearance build，按 collection order 划分可能把整个
appearance group 放到一侧，也可能把同组的相关 episode 拆到两侧。选择 ID 前应保留 episode 到
appearance domain 的映射。

实验使用 `dr_rebuild_every=2` 录制四条 smoke episode，因此 appearance-domain ID 为
`0, 0, 1, 1`。这个最小的重复分组可以让两种 split 直接表现出差别：

| 计划 | Train episode | Evaluation episode | Domain 关系 |
|---|---|---|---|
| In-distribution | `0, 2` | `1, 3` | 两侧都包含 domain 0 和 1 |
| Held-out domain | `0, 1` | `2, 3` | domain 0 只用于训练，domain 1 只用于评估 |

四条 smoke episode 可以演示 grouping 和 split 机制，但仍不足以估计 coverage、比较 policy
或形成有意义的 benchmark。

## 配套实验流程

Notebook 会把完整概念连接到一条有意缩小的实践路径。它不实现缺失的 sensor、geometry、
actuator、timing、disturbance 或 adaptive-distribution 类别。

### 运行之前

- 先完成 L09，或把 notebook 的显式 baseline dataset root 指向一份兼容本地副本。
- 正常路径使用 `ROBO_GENESIS_RENDER=1`：构建 camera、渲染固定 seed 预览、录制四条成功
  episode，再读取两路视频。
- `ROBO_GENESIS_RENDER=0` 是受限诊断：它不初始化 Genesis 或创建 dataset，只检查配置、
  调度、friction/mass 算术和 command 构造。
- Output root 会显式解析；若 L11 dataset 已存在，除非开启精确的 opt-in overwrite variable，
  否则运行会停止。
- 实验不会扫描任意目录、下载 fallback dataset，也不会提交生成的 image、video、cache 或
  provenance file。

### 第 1 步：渲染之前先预测

从 baseline 开始，只改变一个因素。看到图像之前，先说明：

- 该因素属于哪个技术类别；
- 它需要 build 还是 reset；
- 它可能改变哪路 camera observation；
- 它是否可能影响 expert success；
- provenance 必须出现哪个值和 seed。

这样可以把因果推理与看图猜测分开。

### 第 2 步：渲染固定的 Layer-A domain

当前 preview tool 会创建 DR-off baseline，并为每个请求的 appearance seed 启动独立 process：

```sh
.venv/bin/python -m robo_genesis.tools.dr_preview \
  --seeds 0 1 \
  --object-color \
  --table-jitter 0.15 \
  --fov-jitter 2.0 \
  --output-dir outputs/eval_results/l11_dr_preview
```

只有明确测试 CPU backend 时才使用 `--cpu`。生成的 world frame 应该可读、finite、非空，而且
能明显看出 task workspace 仍在画面中。不同图像只能证明已启用 knob 改变了 rendered
observation，不能证明覆盖已经充分或有效。

### 第 3 步：检查 Layer-B 护栏

运行完整场景前，notebook 会复现两个小计算：

1. Genesis contact-pair `max()` 规则，用来说明为什么只缩放物体可能被 finger 或 table 掩盖；
2. multiplicative mass scaling，用来说明为什么正 ratio 能避免负 mass，以及为什么每次 reset
   都必须以原始 base mass 为基准。

完整路径随后从 runtime object 读取实际采样 ratio 与 camera pose。在 notebook 中另写一套
random sampler，只会变成 notebook 对自己的测试。

### 第 4 步：录制四条 episode 的组合 smoke

紧凑实验使用：

| 设置 | 实验值 | 原因 |
|---|---:|---|
| 成功 episode | 4 | 让两个 appearance domain 各有两条 episode |
| 最大 attempt | 10 | 让失败行为有界 |
| Dataset FPS | 5 | 与小型 L09 baseline 一致 |
| 图像尺寸 | `640×360` | 恢复 recorder 默认的 16:9 输出，便于清晰查看画面 |
| Pick task | banana to bowl | 保留与 L09 的对照 |
| Layer-A rebuild interval | 每 2 条 accepted episode | 让同域与留出整域两种 split 都能直接观察 |
| Layer B | 有界 friction、mass 和 world-camera jitter | 测试当前 runtime 子集 |

下面是一条与 notebook subprocess 等价的显式命令：

```sh
.venv/bin/python -m robo_genesis.record_dataset \
  --episodes 4 \
  --max-attempts 10 \
  --seed 1100 \
  --fps 5 \
  --img-width 640 \
  --img-height 360 \
  --vcodec h264 \
  --pick 011_banana \
  --repo-id local/l11_banana_dr \
  --output-dir datasets/l11_banana_dr \
  --dr-appearance \
  --dr-object-color \
  --dr-table-jitter 0.15 \
  --dr-fov-jitter 2.0 \
  --dr-rebuild-every 2 \
  --dr-runtime \
  --dr-friction 0.7 1.3 \
  --dr-mass 0.8 1.2 \
  --dr-cam-pos 0.01 \
  --dr-cam-lookat 0.02
```

实验会在未明确 opt in 时停止，而不是覆盖已有 root；如果 10 次 attempt 没能得到请求的
四次成功，它也会明确失败。这些 safeguard 已经针对最终 recorder 实现完成验证。

### 第 5 步：同时审计 data 与 provenance

使用 LeRobot 0.6.0 重新打开 L09 baseline 和 L11 DR dataset。对两者都报告精确 root、逻辑
repository ID、schema version、FPS、episode/frame count、camera key、image shape 和 codec。
从已标识 episode 中解码同步 world/wrist frame，而不是比较匿名截图。

随后，把每条 committed L11 episode 与 provenance trace 连接起来。审计必须能够回答：

- 哪次 attempt 产生了这条 episode？
- 使用了哪个 runtime seed 和 appearance seed？
- 实际采样了哪些 physics 与 camera 值？
- 在它之前发生过哪些失败 attempt？
- 两个 split group 是否意外共享 appearance domain？

Frame 可以配合描述性的 per-episode image statistic，但任何基于四条 episode 的统计量都不应称作
diversity、generalization 或 robustness 结果。

## 证据阶梯

| 证据 | 它能证明什么 | 它不能证明什么 |
|---|---|---|
| 固定 seed 能重现一套配置和预览 | 配置与 seed path 可追溯 | 所有平台都能 pixel-identical rendering |
| Baseline 与 sampled-domain 图像不同 | 选定 knob 影响 rendered observation | realism、充分 coverage 或 policy benefit |
| Ratio 和 pose 有限且位于范围内 | Layer-B application path 可用 | contact 或 grasp difficulty 单调变化 |
| 四条成功 DR episode 能以双路视频重新打开 | recorder、writer、codec、sidecar 与 reader 接通；重复 domain group 让 split 机制可见 | 数据充分或训练收敛 |
| Attempt/success count 与 provenance 一致 | smoke run 的 selection 可见 | 整体 expert success rate |
| 冻结 policy 在已声明 simulated holdout 上改善 | 该 simulator protocol 下的证据 | 真实世界迁移 |
| 冻结 policy 在真实机器人 protocol 上改善 | 针对该机器人、任务和条件集的证据 | 普遍鲁棒性 |

本讲止于 dataset 与 provenance 证据。L12 训练 policy，L13 执行 closed-loop evaluation。不要把
结论沿这条阶梯向上偷换。

## 按边界诊断失败

1. **缺少 baseline dataset：** 打印精确 root。运行 L09 或提供一份兼容本地 root；不要扫描无关
   目录或下载来源不明的替代品。
2. **Output 已存在：** 默认停止。确认精确 L11 target directory 后，才允许 overwrite。
3. **Preview 没有变化：** 检查 `enabled`、非零 knob、seed，以及是否真的 build 了新 scene。
4. **物体外观不合理：** 检查该物体是否存在 `DR_APPEARANCE_PRIORS` entry，并记住 flat
   recolor 会替换原 texture；不要任意扩大 hue。
5. **任务离开画面：** 隔离 FOV 与 camera-pose jitter，缩小范围，再用真实 world-camera frame
   检查工作台。
6. **Friction 看似没变：** 在推断 motion 前，检查 object、接触中的 Franka link 和 table 是否
   都收到 shared ratio。
7. **Mass 导致 NaN 或跨 reset 漂移：** 要求正 ratio，并从缓存的原始 mass 计算 shift，而不是
   使用上一 episode 的 mass。
8. **同一个 seed 看起来不同：** 对照 backend、code/asset version、appearance-domain index、
   attempt history 和完整 config。Seed 本身不是 environment identity。
9. **保存的数据缺少请求的 domain：** 先检查 failed-attempt provenance 与 success gate，不要先
   责怪 reader。
10. **Evaluation 异常好或异常差：** 改 policy 前，先检查 episode/domain leakage，以及一个完整
    appearance group 是否全部落到某一侧。

## 检查点与单变量练习

### 概念检查点

1. 为什么 DR 是一族环境上的分布，而不是 recorder flag 列表？
2. 对一个候选参数，它主要改变 observation、physics、actuation/timing 还是 disturbance？它能否
   同时影响多个类别？
3. 为什么 Layer A 和 Layer B 是仓库生命周期标签，而不是机器人领域的通用 taxonomy？
4. 为什么 object pose 在一个实验中可能是 task randomization，在另一个实验中却是 domain
   variation？
5. Data augmentation、system identification 和 domain adaptation 与 DR 有何不同，又如何与之
   配合？
6. 为什么 mass 通常应该在一条 trajectory 内固定，而 independent sensor noise 可以每一步改变？
7. 为什么失败 attempt 会消耗 runtime seed，却不消耗 appearance-domain success quota？
8. 为什么 success-only recorder 会扭曲请求的 domain distribution？
9. 为什么两张不同图像或更大的 RGB spread 不能证明 policy robustness？
10. 要声称 sim-to-real，还需要哪些额外 protocol 和证据？

### 单变量练习：隔离一个 domain parameter

回到 notebook 第 2 节的 `l11-appearance-preview` code cell。只把 `PREVIEW_PROFILE` 从
`combined` 改为 `table_color`、`object_color` 或 `fov`，然后重新运行第 2、3 节。每个 profile
都会把未选中的 knob 固定为零，保持 seed 0 和 1，并写入隔离的 preview 子目录。Runtime
world-camera pose 被有意排除：它属于 reset-time Layer B，需要录制 episode，而不是运行这个
快速的 build-time preview。

运行前，预测：

- 它所属的技术类别；
- 它的 build/reset sampling boundary；
- 哪路 observation 应该改变；
- 它是否会影响 task validity 或 expert success；
- 必须记录哪些 requested value 与 actual value。

运行后，用带标签的 frame 和 provenance 对照预测。只陈述证据实际支持的结论；没有受控训练和
闭环评估时，不得声称这个参数改善了 policy。

## 小结

- 域随机化在保持定性任务的前提下，从 environment parameter distribution 中采样；它不等同于
  visual noise 或 recorder flag。
- 机器人 DR 可以覆盖 rendering、sensor、geometry、physics、actuation、timing 和
  disturbance。“什么变化”“怎样选择 domain”“何时采样”是三条独立设计轴。
- Static manual DR 只是一种策略。Measurement-informed、automatic、adaptive 与 adversarial
  方法改变 domain distribution 的选择方式，而不是参数所属的物理类别。
- 本课程有意实践一个更小的子集：build-time color/FOV 与 reset-time
  friction/mass/world-camera pose；没有实现 texture、lighting、sensor noise、geometry、
  actuator 或 disturbance randomization。
- Seed、requested range、actual draw、failed attempt 和 commit decision 都属于数据身份。
  Success-only dataset 可能不同于请求的 randomization distribution。
- 有效 preview 与可读 smoke dataset 只能证明实现链路，不证明 policy robustness 或
  sim-to-real transfer。

## 来源

- Muratore et al., [“Robot Learning From Randomized Simulations: A
  Review”](https://doi.org/10.3389/frobt.2022.799893)——domain-parameter 表述、实用随机化考虑与
  static/adaptive/adversarial taxonomy。
- Tobin et al., [“Domain Randomization for Transferring Deep Neural Networks
  from Simulation to the Real World”](https://arxiv.org/abs/1703.06907)——涵盖 texture、scene
  object、camera、light 与 image noise 的视觉随机化。
- Peng et al., [“Sim-to-Real Transfer of Robotic Control with Dynamics
  Randomization”](https://arxiv.org/abs/1710.06537)——机器人控制中的 randomized dynamics、
  controller timing 与 observation noise。
- OpenAI et al., [“Solving Rubik's Cube with a Robot
  Hand”](https://arxiv.org/abs/1910.07113)——automatic domain randomization，以及宽泛的
  simulator-physics、custom-physics、observation、vision 与 disturbance parameter set。
- [Genesis World 文档](https://genesis-world.readthedocs.io/en/latest/)与 [PyPI 上的 Genesis
  World 1.3.3](https://pypi.org/project/genesis-world/1.3.3/)——官方 engine/API 文档与本课程锁定的
  精确版本。
- [Genesis 1.3.3 `RigidEntity`
  源码](https://github.com/Genesis-Embodied-AI/genesis-world/blob/v1.3.3/genesis/engine/entities/rigid_entity/rigid_entity.py)与
  [rigid-contact
  实现](https://github.com/Genesis-Embodied-AI/genesis-world/blob/v1.3.3/genesis/engine/solvers/rigid/collider/contact.py)——
  版本锁定的 runtime mass/friction API 与 contact-pair behavior。
- [Genesis 1.3.3 `Camera`
  源码](https://github.com/Genesis-Embodied-AI/genesis-world/blob/v1.3.3/genesis/vis/camera.py)——
  版本锁定的 camera construction、FOV、pose、attachment 与 rendering behavior。
- [RoboGenesis 101 scene
  builder](https://github.com/wangxunx/robo-genesis-101/blob/main/src/robo_genesis/build_scene.py)、
  [environment
  randomizer](https://github.com/wangxunx/robo-genesis-101/blob/main/src/robo_genesis/randomize.py)、
  [dataset
  recorder](https://github.com/wangxunx/robo-genesis-101/blob/main/src/robo_genesis/record_dataset.py)与
  [DR preview
  tool](https://github.com/wangxunx/robo-genesis-101/blob/main/src/robo_genesis/tools/dr_preview.py)——
  本讲所用的当前 Layer-A/Layer-B behavior 与 collection schedule。
