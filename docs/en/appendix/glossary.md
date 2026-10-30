# Course Glossary

This glossary standardizes terms across lectures, notebooks, and reviews. It is a usage
guide, not a replacement for each lesson's mechanism-level explanation. Stable technical
terms may remain in English in Chinese prose when translating them would make the concept
less recognizable.

## Simulation and control

| Canonical term | Chinese usage | Meaning in this course |
|---|---|---|
| backend | backend / 后端 | The actual Genesis compute backend, such as CPU or `gs.amdgpu`; it must be reported, not inferred from a namespace. |
| degree of freedom (DOF) | 自由度（degree of freedom，DOF） | An independent generalized coordinate used to describe or control robot motion. |
| forward kinematics (FK) | 正运动学（forward kinematics，FK） | Computing an end-effector pose from joint coordinates. |
| inverse kinematics (IK) | 逆运动学（inverse kinematics，IK） | Solving joint coordinates for a target end-effector pose. |
| end-effector pose | 末端执行器位姿（end-effector pose） | Position and orientation of the controlled robot link. |
| control step | 控制步（control step） | One policy or controller update; it may contain multiple simulation steps. |
| simulation step | 仿真步（simulation step） | One physics advance at the simulator time step. |
| parallel environment | 并行环境（parallel environment） | One member of a batched set of independent simulated worlds. |
| selective update | 选择性更新（selective update） | Applying a command or reset only to selected environment indices. |
| offscreen rendering | 离屏渲染（offscreen rendering） | Producing camera frames without an interactive viewer, typically through EGL in the verified setup. |

## Tasks and demonstrations

| Canonical term | Chinese usage | Meaning in this course |
|---|---|---|
| task specification (`TaskSpec`) | 任务规格（task specification） | Declarative pick object, place target, tolerance, and related task values. |
| scripted expert | 脚本化专家（scripted expert） | A deterministic, inspectable controller that produces demonstrations through explicit phases. |
| scripted rollout | `scripted rollout` | One execution of the scripted expert. Keep `rollout` in English rather than forcing a Chinese translation. |
| rollout | `rollout` | A temporally ordered execution of a controller or policy in an environment. |
| demonstration | 演示数据（demonstration） | A recorded observation/action trajectory intended for analysis or learning. |
| seed demonstration | 种子演示数据（seed demonstration） | An initial demonstration used to bootstrap collection, adaptation, or further supervision. |
| state machine | 状态机（state machine） | Explicit phases and transitions that determine the expert's next action. |
| success predicate | 成功判据（success predicate） | A machine-checkable task condition; in the main task it includes horizontal placement and below-rim containment. |
| dwell time | 连续保持时间（dwell time） | How long the success predicate must remain true before an episode counts as successful. |

## Data and learning

| Canonical term | Chinese usage | Meaning in this course |
|---|---|---|
| episode | episode / 回合 | One bounded task attempt represented by a temporally ordered sequence. Use `episode` when discussing a dataset field or API. |
| frame | 帧（frame） | One time-indexed record, often containing state, action, and synchronized images. |
| sample | 样本（sample） | One training item produced from one frame or a temporal window, depending on policy configuration. |
| schema | schema / 数据结构约定 | The field names, shapes, dtypes, rates, and metadata that make a dataset consumable. |
| repository ID (`repo_id`) | repository ID（`repo_id`） | Logical dataset identity; it is not interchangeable with the local filesystem path. |
| temporal alignment | 时间对齐（temporal alignment） | Ensuring observation, action, image, and timestamp fields describe the intended instant. |
| action chunk | 动作块（action chunk） | A predicted sequence of future actions from a chunking policy such as ACT. |
| imitation learning | 模仿学习（imitation learning） | Learning a policy from demonstration observation/action pairs. |
| open-loop reload | 开环重载（open-loop reload） | Loading a checkpoint and generating actions without allowing those actions to affect the next observation. |
| checkpoint | checkpoint / 检查点 | A saved policy artifact plus the configuration and processor state needed to reload it. |
| dry-run | `dry-run` | Validation of inputs and command construction without performing the expensive training or evaluation path. |
| smoke run | `smoke run` | A deliberately small real execution that proves integration, not convergence or policy quality. |

## Randomization and evaluation

| Canonical term | Chinese usage | Meaning in this course |
|---|---|---|
| domain randomization (DR) | 域随机化（domain randomization，DR）；后文可直接写 `domain randomization` 或 DR | Sampling declared visual or physical factors to broaden training or evaluation conditions. The English term may remain untranslated in engineering prose. |
| provenance | 来源与生成记录（provenance） | Machine-readable evidence for configuration, seeds, attempts, committed episodes, and generated artifacts. |
| support | 训练支持范围（support） | The values or conditions represented by declared training data, not an assumed continuous distribution. |
| shifted condition | 偏移条件（shifted condition） | An evaluation condition changed from reference without enough evidence to call it OOD. |
| out of distribution (OOD) | 分布外（out of distribution，OOD） | A condition shown to lie outside the declared training support for the changed factor. |
| reference condition | 参考条件（reference condition） | The declared baseline evaluation protocol. It does not imply a universal real-world baseline. |
| closed-loop evaluation | 闭环评估（closed-loop evaluation） | Repeated observation, policy inference, action application, and environment transition until termination. |
| matched seeds | 匹配 seed（matched seeds） | Conditions use the same scheduled initial seeds; this controls only what the protocol actually binds to those seeds. |
| aggregate result | 汇总结果（aggregate result） | A condition-level count such as `k/n`; independent aggregates do not create paired outcomes. |
| Wilson interval | Wilson 区间（Wilson interval） | A binomial proportion interval reported with small-run success counts. |
| Capstone | `Capstone` / 综合实践 | The integrative L13 assignment; it must preserve the evidence boundaries of the underlying evaluation. |

## Status and evidence

| Canonical term | Meaning in this course |
|---|---|
| `planned` | Metadata and position are fixed, but learner-ready content is not claimed. |
| `draft` | Substantial content exists but has not passed full review. |
| `reviewed` | Content review passed; runtime verification may still be incomplete. |
| `cpu-verified` | The lesson's declared CPU completion contract passed. It may also have additional GPU evidence. |
| `gpu-verified` | The lesson's declared GPU contract passed on a recorded reference platform. It is not a claim about every GPU. |
| `published` | Release artifacts, public entry points, and release acceptance have passed the publication gate. `verified` is not automatically `published`. |
| diagnostic | A bounded check of configuration, logic, or inputs; it must state which core experiment did not run. |
| integration evidence | Evidence that interfaces connect and execute; it does not by itself establish policy quality. |
| task-performance evidence | Closed-loop outcomes under a declared protocol, with counts, termination reasons, and artifact checks. |

## Writing rules

- Introduce a specialized term with a short Chinese explanation and the original English
  when translation alone could be ambiguous.
- Keep recognizable technical terms such as `rollout`, `domain randomization`, `dry-run`,
  and `checkpoint` in English when that is clearer for learners.
- Do not alternate casually between dataset path, repository ID, and artifact version.
- Use `success` only for the declared success predicate; use `completed`, `passed`, or
  `executed` for pipeline stages.
- State whether evidence is diagnostic, open-loop, closed-loop, or aggregate before drawing
  a conclusion.
- Preserve upstream spellings for Genesis, LeRobot, ACT, SmolVLA, RoboTwin, LingBot-VLA-v2,
  Franka, and YCB.
