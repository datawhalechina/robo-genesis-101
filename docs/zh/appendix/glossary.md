# 课程术语表

本术语表统一讲义、notebook 与 review 中的用词，但不替代各讲对机制的完整解释。在中文叙述中，
如果强行翻译会降低技术概念的辨识度，可以保留稳定的英文技术词。

## 仿真与控制

| 规范术语 | 中文用法 | 本课程中的含义 |
|---|---|---|
| backend | backend / 后端 | 实际 Genesis 计算 backend，例如 CPU 或 `gs.amdgpu`；必须报告实际值，不能根据命名空间猜测。 |
| degree of freedom (DOF) | 自由度（degree of freedom，DOF） | 描述或控制机器人运动的一项独立广义坐标。 |
| forward kinematics (FK) | 正运动学（forward kinematics，FK） | 根据关节坐标计算末端执行器位姿。 |
| inverse kinematics (IK) | 逆运动学（inverse kinematics，IK） | 为目标末端执行器位姿求解关节坐标。 |
| end-effector pose | 末端执行器位姿（end-effector pose） | 被控制机器人 link 的位置与姿态。 |
| control step | 控制步（control step） | 一次策略或控制器更新；其中可以包含多个 simulation step。 |
| simulation step | 仿真步（simulation step） | 按仿真时间步推进一次物理状态。 |
| parallel environment | 并行环境（parallel environment） | 一组批量独立仿真世界中的一个成员。 |
| selective update | 选择性更新（selective update） | 只对选定 environment index 应用命令或 reset。 |
| offscreen rendering | 离屏渲染（offscreen rendering） | 不打开交互 viewer 生成相机帧；在已验证环境中通常通过 EGL 完成。 |

## 任务与演示数据

| 规范术语 | 中文用法 | 本课程中的含义 |
|---|---|---|
| task specification (`TaskSpec`) | 任务规格（task specification） | 以声明方式描述抓取对象、放置目标、容差及相关任务值。 |
| scripted expert | 脚本化专家（scripted expert） | 通过显式阶段生成演示数据、可检查且确定性的控制器。 |
| scripted rollout | `scripted rollout` | 脚本化专家的一次执行。保留 `rollout` 英文，不强行翻译。 |
| rollout | `rollout` | 控制器或策略在环境中按时间顺序展开的一次执行。 |
| demonstration | 演示数据（demonstration） | 为分析或学习而录制的 observation/action 轨迹。 |
| seed demonstration | 种子演示数据（seed demonstration） | 用于启动采集、适配或进一步监督的初始演示数据。 |
| state machine | 状态机（state machine） | 决定专家下一步 action 的显式阶段与转换规则。 |
| success predicate | 成功判据（success predicate） | 可由程序检查的任务条件；主任务同时要求水平放置和低于碗沿的包含关系。 |
| dwell time | 连续保持时间（dwell time） | episode 被判成功前，成功判据必须连续为真的时长。 |

## 数据与学习

| 规范术语 | 中文用法 | 本课程中的含义 |
|---|---|---|
| episode | episode / 回合 | 有边界的一次任务尝试，对应按时间排序的序列；讨论数据字段或 API 时优先使用 `episode`。 |
| frame | 帧（frame） | 一个时间索引记录，通常包含 state、action 与同步图像。 |
| sample | 样本（sample） | 根据策略配置，由单帧或时间窗口形成的一项训练输入。 |
| schema | schema / 数据结构约定 | 让数据集可被消费的字段名、shape、dtype、频率和 metadata 约定。 |
| repository ID (`repo_id`) | repository ID（`repo_id`） | 数据集的逻辑 identity，不能与本地文件系统路径混用。 |
| temporal alignment | 时间对齐（temporal alignment） | 确保 observation、action、图像与 timestamp 描述预期的同一时刻。 |
| action chunk | 动作块（action chunk） | ACT 等 chunking policy 一次预测的未来 action 序列。 |
| imitation learning | 模仿学习（imitation learning） | 从演示数据的 observation/action 配对学习策略。 |
| open-loop reload | 开环重载（open-loop reload） | 加载 checkpoint 并生成 action，但不让 action 影响下一次 observation。 |
| checkpoint | checkpoint / 检查点 | 已保存的策略 artifact，以及重载所需配置与 processor 状态。 |
| dry-run | `dry-run` | 不执行昂贵训练或评估路径，只验证输入与命令构造。 |
| smoke run | `smoke run` | 有意缩小规模的真实执行，用于证明集成链路，而不是证明收敛或策略质量。 |

## 随机化与评估

| 规范术语 | 中文用法 | 本课程中的含义 |
|---|---|---|
| domain randomization (DR) | 域随机化（domain randomization，DR）；后文可直接写 `domain randomization` 或 DR | 对声明的视觉或物理因子采样，以扩展训练或评估条件。工程叙述中可以不翻译英文词组。 |
| provenance | 来源与生成记录（provenance） | 对配置、seed、attempt、已提交 episode 与生成 artifact 的机器可读证据。 |
| support | 训练支持范围（support） | 声明的训练数据实际覆盖的值或条件，不是假设出的连续分布。 |
| shifted condition | 偏移条件（shifted condition） | 相比 reference 有变化，但证据不足以称为 OOD 的评估条件。 |
| out of distribution (OOD) | 分布外（out of distribution，OOD） | 能够证明其变化因子位于声明训练 support 之外的条件。 |
| reference condition | 参考条件（reference condition） | 声明的基准评估协议，不表示通用真实世界 baseline。 |
| closed-loop evaluation | 闭环评估（closed-loop evaluation） | 重复 observation、policy inference、action 应用与环境转移，直到终止。 |
| matched seeds | 匹配 seed（matched seeds） | 不同条件使用相同调度初始 seed；它只能控制协议真正绑定到 seed 的因素。 |
| aggregate result | 汇总结果（aggregate result） | `k/n` 形式的条件级计数；相互独立的 aggregate 不会自动产生配对结果。 |
| Wilson interval | Wilson 区间（Wilson interval） | 与小样本成功计数同时报告的二项比例区间。 |
| Capstone | `Capstone` / 综合实践 | L13 的集成作业；必须保留底层评估的证据边界。 |

## 状态与证据

| 规范术语 | 本课程中的含义 |
|---|---|
| `planned` | metadata 与结构位置已确定，但不声称内容已经可供学习者使用。 |
| `draft` | 已有实质内容，但尚未通过完整 review。 |
| `reviewed` | 内容 review 已通过；运行验证仍可能不完整。 |
| `cpu-verified` | 本讲声明的 CPU 完成合同已通过；它也可能同时拥有额外 GPU 证据。 |
| `gpu-verified` | 本讲声明的 GPU 合同已在记录的参考平台通过，不代表所有 GPU。 |
| `published` | 发布 artifact、公开入口与 release acceptance 已通过发布门禁；`verified` 不会自动等于 `published`。 |
| diagnostic | 对配置、逻辑或输入的有限检查；必须说明哪个核心实验没有运行。 |
| integration evidence | 证明接口连接并执行的证据，本身不能证明策略质量。 |
| task-performance evidence | 声明协议下的闭环结果，包含计数、终止原因与 artifact 检查。 |

## 写作规则

- 专业词仅用中文可能产生歧义时，首次出现应采用简短中文解释并保留原英文词组。
- `rollout`、`domain randomization`、`dry-run`、`checkpoint` 等技术词直接保留英文更清晰时，
  不强行翻译。
- 不要把 dataset path、repository ID 与 artifact version 随意互换。
- 只有满足声明成功判据时才使用 `success`；pipeline 阶段应使用“完成”“通过”或“已执行”。
- 给出结论前，先说明证据属于 diagnostic、open-loop、closed-loop 还是 aggregate。
- Genesis、LeRobot、ACT、SmolVLA、RoboTwin、LingBot-VLA-v2、Franka 与 YCB 保留上游拼写。
