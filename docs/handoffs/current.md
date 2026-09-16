# RoboGenesis 101 当前工作交接

最后核对日期：2026-09-16（Asia/Shanghai）。

本文件只记录新 thread 最容易遗漏的当前状态、近期验收结论、项目负责人偏好、未决事项和
恢复顺序。通用协作规则以根目录 `AGENTS.md` 为准；课程总状态与步骤门禁以本地
`robo_genesis_101_course_development.plan.md` 为准；逐讲历史位于
`course_development/lessons/`；运行环境和实测证据以 `COMPATIBILITY.md` 为准。

## 1. 一句话恢复状态

- L03–L11 的逐讲开发步骤均已完成并通过项目负责人验收；L01、L02 与 L12 也已有各自
  已验收实现和状态。
- L11 已于 2026-09-15 完成 `M3.L11.1`–`M3.L11.6` 全部验收，公开状态为
  `gpu-verified`。
- L13 尚未开始；当前唯一课程开发下一步是等待项目负责人明确说“开始 `M3.L13.1`”。
  不要因为骨架已存在、L11 已验收或新 thread 已建立而自动开始。
- L13 启动后先完成 `.1`：来源与现有实现审计、教学边界、学习目标、讲义/视觉结构、
  notebook 合同和 `.2`–`.6` 验收门禁。不要直接扩写讲义/notebook，也不要提前改变
  L13 的 `planned` 状态。

## 2. Git 快照与工作树保护

更新本文件前的快照：

- 当前分支：`main`；
- HEAD、本地 `main`、`origin/main` 与 `origin/HEAD`：
  `84adc29 new course logo`；
- 近期课程提交：`0f182e8 verified en/zh notebooks of l11 domain randomization`、
  `3b931ec update l11 lectures and src tests per notebooks' requirement`、
  `106aa86 add en/zh notebooks of l11 domain randomization`。

分支和 HEAD 可能在新 thread 启动前继续变化，因此首先重新运行：

```sh
git status --short --branch
git log -5 --oneline --decorate
```

本次 handoff 更新前，tracked 工作树是 clean；更新后预期只有
`docs/handoffs/current.md` 是 tracked 修改。下列 untracked 内容在本轮之前已经存在，属于
本地配置、补丁或开发记录，必须保留，不得清理、覆盖或误当成新 thread 生成的垃圾文件：

- `.vscode/`；
- `0001-4-cards-failure.patch`；
- `0001-rewrite-l09-lectures.patch`；
- `MIGRATION.md`；
- `course_development/`；
- `genesis_公开课体系规划_2ba5d82e.plan.md`；
- `robo_genesis_101_course_development.plan.md`。

根开发计划和逐课档案位于 untracked 路径，但它们是当前开发状态的重要真相源；不要因为
`git diff` 不显示其内容变化而忽略或删除。当前 thread 没有执行新的 commit、push 或发布；
HEAD 的 logo commit 已在本 thread 开始 handoff 前存在并与 `origin/main` 对齐。

## 3. 当前公开课程状态

`course.json` 是课程元数据的唯一结构化来源。当前共 13 讲：

- L01–L07、L10：8 个 `cpu-verified`；
- L08、L09、L11、L12：4 个 `gpu-verified`；
- L13：1 个 `planned`；
- 0 个 `published`。

L11 的 90 分钟时长、`domain-randomization` slug、双语路径和 `gpu-recommended` hardware
字段没有因状态晋级而改变。以下来源已一致同步为 `gpu-verified`：

- `course.json`；
- 双语 L11 讲义 frontmatter 与顶部课程状态说明；
- 双语 L11 notebook metadata、setup assert 和两处分支 final-check contract；
- 双语 README 与首页；
- manifest 和 L11 notebook 合同测试。

完整逐步记录见 `course_development/lessons/l11.md`；兼容性与运行证据见
`COMPATIBILITY.md` 第 22 节，尤其是状态同步后的 22.7 节。

## 4. L11 最终实现与证据摘要

- 双语 notebook 为 20 cells / 9 code cells，cell type、code-cell ID/source 完全一致，
  提交版保持 clean output；最终规范化 code SHA-256 为
  `e361fbc0c22b44b15a8155d3733ca99defefe4eee8b9af9e0cd4427ae5850e9b`。
- 实验把完整 domain-randomization 范畴作为理论背景，但只实践 bounded 子集：构建期
  table/object flat color 与 FOV，运行期 shared friction、positive mass ratio 和静态
  world-camera extrinsics；不把 flat recoloring 称为 texture randomization。
- `.5` 已通过 EN/ZH CPU `render=0`、English CPU+EGL 与参考 R9700 AMD+EGL；两条完整路径
  均得到 4 attempts / 4 successes、173 frames、appearance domains `[0,0,1,1]`、双相机
  H.264 5 FPS `640×360` readback、provenance sidecar 和两种 domain-aware split。
- `.6` 只更新状态 literal 与公开摘要，没有改变 scene、DR、recorder、schema、视频、
  readback 或 split 行为。更新后 English CPU 无渲染 clean-kernel 9/9 cells 通过并读取
  `status=gpu-verified`，未创建 dataset/preview。
- 证据边界必须保留：没有训练 policy、没有闭环评价或真实机器人实验，也没有证明 DR
  提升性能、统计显著性或 sim-to-real。正式运行恰好 4/4 成功，因此 selection effect 是
  已解释并有失败路径合同的风险，不是本轮实测发生的现象。
- L09 baseline 仍是旧的 `160×120` 输入，L11 DR 数据是 `640×360`。项目负责人决定此前
  课程的分辨率以后统一处理；不要在启动 L13 时顺带返工 L09。

## 5. 项目负责人已明确的教学偏好

后续 L13 应继续遵循：

- 面向有基础 Python/机器学习知识、但刚接触机器人技术与仿真的学习者；先把机制讲清楚，
  再进入实现细节。
- 理论概念可以比 notebook 实践范围更完整；实践只取可控子集没有问题，但必须明确
  “完整技术范畴”和“本课实际实现”之间的边界。
- 对 provenance、selection effect、domain-aware split 等抽象内容，要解释“为什么需要它、
  代码里是否真的实现、学习者如何读结果”，不能只堆术语或字段。
- 抽象关系适合用课程自制示意图帮助理解；保持图形直观、无歧义，并实际检查细节。
- notebook 中不易读的 check 应配简明注释；练习必须明确告诉学习者修改哪个 code cell，
  不能只在结尾留下无落点的题目。
- 复习问题应挑核心，不要把前文每个细节全部再问一遍；问题必须与学习者当前已完成的
  实验相匹配。尚未训练 policy 时，不应要求学习者论证“policy 表现提升”。
- 如果少量 episode/domain 使教学输出难以解读，应适当增加最小 smoke 数量来真正展示
  差异，同时继续控制运行成本。
- 讲义示例和 notebook 必须忠实解释当前源码。发现课程说法与实现不一致时，先确认代码
  是否已有支持；不要把计划中的功能写成已经实现。
- EN/ZH notebook code cells 必须逐字一致；Markdown 应自然本地化，不做生硬逐句翻译。
- 相机图像是实验核心数据时，`render=0` 只能作为受限诊断，不能冒充完整视觉实验。
- 训练 loss、开环动作预测或视频回放不能替代闭环 rollout 与明确的任务成功判据。

## 6. 新课程 logo 的当前状态

HEAD `84adc29` 已将站点 logo 从 `/datawhale-logo.png` 切换为原创的
`/robogenesis-logo.svg`：机器人夹爪托举橙色仿真立方体，外部双向轨迹与节点代表
数据—训练—评估闭环。

- 矢量源：`docs/public/robogenesis-logo.svg`；
- 400×400 RGBA 导出：`docs/public/robogenesis-logo.png`；
- VitePress 引用：`docs/.vitepress/config.mts` 的 `themeConfig.logo`；
- 原 `docs/public/datawhale-logo.png` 仍保留，但不再被站点引用；不要无指令删除；
- logo 接入后的 `npm run docs:build` 已通过，页面与 SVG 在本地预览中均返回 HTTP 200；
- 本轮曾启动 VitePress 预览服务供项目负责人查看，handoff 前已停止。新 thread 不应依赖
  旧端口或后台 session，若需预览应重新运行 `npm run docs:dev -- --host 0.0.0.0`。

图标已进入 `main`/`origin/main`，不再是未决的候选文件；除非项目负责人提出新反馈，
不要在 L13 开发中顺带改动 logo。

## 7. L13 启动前已知边界

L13 当前只有 `planned` 骨架：双语讲义各为 frontmatter 加一句占位说明，双语 notebook
各为 2 cells（`l13-overview`、`l13-manifest-check`），尚无
`course_development/lessons/l13.md` 单课档案。

冻结在根计划中的 L13 主线是：

1. 区分 training loss、open-loop playback 与 closed-loop rollout；
2. 定义 success criterion、dwell、seed、in-distribution/OOD 分组和评估协议；
3. 报告 successes / total episodes 与置信区间，不编造成功率；
4. Capstone 串联环境诊断、数据检查、模型加载、闭环评估和实验报告；
5. 自训失败的学习者应能使用课程 checkpoint 完成评估。

这些只是现有课程级边界，不是已经验收的 L13 详细设计。`M3.L13.1` 启动后必须审计：

- `src/robo_genesis/` 当前 evaluation、scene、checkpoint loader 与 policy adapter 的真实能力；
- 已验收 L08 success criterion、L09/L11 dataset/provenance 和 L12 checkpoint/data contract；
- 原始课程对应模块、当前可用 checkpoint/fixture、许可和可复现实验成本；
- CPU 诊断、GPU smoke、完整闭环路径及无法运行时的诚实降级边界。

不要假设课程 checkpoint、闭环 evaluator、OOD domain 或成功率统计已经存在；先以仓库实际
实现为准。L13 是当前最后一讲，但 `.1`–`.6` 仍需逐步交付、逐步验收，不能一次性跳到
发布状态。

## 8. 最近门禁与已知 warning

L11 `.6` 状态同步后的完整门禁：

- course validation：13 lessons、32 localized Markdown files、26 notebooks、37 Python files；
- pytest：67 passed；
- compileall：通过；
- `uv lock --check`：解析 235 packages；
- `npm ci`：安装 190 个包并审计 191 个包；
- 普通与 `EDGEONE=1` 文档构建：通过；
- EN/ZH notebook parity、clean output、更新后执行副本 source identity、状态残留和
  `git diff --check`：通过。

logo commit 后又单独运行 `npm run docs:build` 并通过，只有既有的 VitePress large-chunk
warning。最近 `npm ci` 仍报告 11 项既有 advisory（4 low、1 moderate、6 high），没有运行
`npm audit fix`。Genesis/Franka、Quadrants、NumPy read-only tensor 等 warning 的精确记录
见 `COMPATIBILITY.md`；它们没有导致 L11 正式路径失败。

## 9. 新 thread 恢复顺序

1. 完整读取根目录 `AGENTS.md`。
2. 运行第 2 节的 Git 快照命令，确认是否出现本 handoff 之后的新提交或用户修改。
3. 完整读取本文件与 `robo_genesis_101_course_development.plan.md`。
4. 读取 `COMPATIBILITY.md` 第 22 节；需要追溯教学决策时读取
   `course_development/lessons/l11.md`，不要重复执行已经验收的 L11 工作。
5. 核对 `course.json` 当前仍为 8/4/1/0，L11=`gpu-verified`、L13=`planned`。
6. 若项目负责人明确启动 `M3.L13.1`，先做第 7 节所列审计并创建
   `course_development/lessons/l13.md`；否则只报告当前状态，不自动开始。

持续适用的协作边界：每个子步骤完成后单独等待项目负责人验收，不自动开始下一步；
`docs/handoffs/current.md` 只在项目负责人准备切换 thread 时更新；不创建 commit、不 push、
不发布外部 artifact，除非项目负责人明确要求。
