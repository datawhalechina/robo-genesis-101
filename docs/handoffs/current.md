# RoboGenesis 101 当前工作交接

最后核对日期：2026-10-10（Asia/Shanghai）。

本文件只记录新 thread 最容易遗漏的当前状态、近期验收结论、项目负责人偏好、未决事项和
恢复顺序。通用协作规则以根目录 `AGENTS.md` 为准；课程总状态与步骤门禁以本地
`robo_genesis_101_course_development.plan.md` 为准；逐讲历史位于
`course_development/lessons/`；运行环境和实测证据以 `COMPATIBILITY.md` 为准。

## 1. 一句话恢复状态

- M0、M1、M2、M3 已全部完成并通过项目负责人验收。
- L13 的 `M3.L13.1`–`M3.L13.6` 已全部验收；公开状态为 `gpu-verified`。
- L13 是 M3 最后一讲。当前没有进行中的课程开发子步骤。
- M4 尚未开始。只有项目负责人明确说“开始 `M4.1`”后，才进入全课程集成与发布前回归；
  不要因为 M3 已完成而自动启动 M4。
- M5 也未开始。L13 已有固定 Hugging Face fallback，不等于 M5 的版本化 artifact 发布、
  checksum、license/model card、下载工具和 V1 发布流程已经完成。

## 2. Git 快照与工作树保护

更新本文件前的快照：

- 当前分支：`main`；
- HEAD、本地 `main`、`origin/main` 与 `origin/HEAD` 均为
  `a2441789c7b2693688224cbc550787f327a8d956`；
- HEAD 标题：`a244178 update COMPATIBILITY doc after l13`；
- 近期 L13 提交：
  - `bf9f3ad verified en/zh notebooks of l13 closed loop evaluation`；
  - `b25f66c add en/zh notebooks of l13 closed loop evaluation`；
  - `d5617b2 add en/zh lecture of l13 closed loop evaluation`；
  - `21f951c transfer to datawhalechina org`。

新 thread 首先重新运行：

```sh
git status --short --branch
git log -5 --oneline --decorate
```

本次 handoff 更新前 tracked 工作树为 clean；更新后预期只有
`docs/handoffs/current.md` 是 tracked 修改。下列 untracked 内容在 handoff 前已经存在，属于
本地配置、补丁或开发记录，必须保留，不得清理、覆盖或误当成新 thread 生成的垃圾文件：

- `.vscode/`；
- `0001-4-cards-failure.patch`；
- `0001-add-en-zh-lecture-of-l13-closed-loop-evaluation.patch`；
- `0001-rewrite-l09-lectures.patch`；
- `MIGRATION.md`；
- `course_development/`；
- `genesis_公开课体系规划_2ba5d82e.plan.md`；
- `robo_genesis_101_course_development.plan.md`。

根开发计划和逐课档案位于 untracked 路径，但仍是当前开发状态的重要真相源；不要因为
`git diff` 不显示其内容变化而忽略或删除。本次 handoff 不创建 commit、不 push、不发布外部
artifact。

## 3. 当前公开课程状态

`course.json` 是课程元数据的唯一结构化来源。当前共 13 讲：

- L01–L07、L10：8 个 `cpu-verified`；
- L08、L09、L11、L12、L13：5 个 `gpu-verified`；
- 0 个 `planned`；
- 0 个 `published`。

L13 的 120 分钟时长、`closed-loop-evaluation-and-capstone` slug、双语路径和
`gpu-required` hardware 没有因状态晋级而改变。以下来源已一致同步为 `gpu-verified`：

- `course.json`；
- 双语 L13 讲义 frontmatter 与顶部状态说明；
- 双语 L13 notebook metadata 和 manifest status assert；
- `README.md`、`README_en.md` 与双语首页；
- manifest 和 L13 notebook 合同测试。

完整开发与验收历史见 `course_development/lessons/l13.md`；正式闭环运行证据见
`COMPATIBILITY.md` 第 23 节；公开状态同步和更新后诊断见第 24 节。

## 4. L13 notebook 的最终教学交互

双语 notebook 当前均为 18 cells / 8 code cells，cell type、code-cell ID 和 code source
逐字一致，提交版所有 `outputs` 为空、`execution_count` 为 null。Markdown 自然本地化。

最终主线是一个从上到下的七步流程：

1. 审计环境、dataset 与 checkpoint 来源；
2. 冻结任务和 success/dwell/timeout 协议；
3. 预声明 Reference 与单因素 held-out 条件；
4. 运行五个 Reference closed-loop episodes；
5. 审计逐 episode rows、汇总统计和代表视频；
6. 用相同 seeds 运行 matched held-out 条件；
7. 根据 evidence card 写出结论范围明确的 Capstone report。

必须保留的交互决策：

- 不使用 global run mode，不在说明中突兀提及“global run mode”，也不恢复 `mode`、
  `RUN_REFERENCE`、`RUN_HELD_OUT`、`run_eval` 或其他分支开关。
- 运行某个评估 cell 本身就是明确的执行动作。Step 4 一定执行 Reference，因此没有额外
  True/False 开关。
- 所有学习者需要选择的实验参数都在顶部可见 `CONFIG` 中；子进程环境由 `render`、
  `gpu_index` 和 `policy_device` 派生，并在 Step 1 runtime summary 中打印，不能藏在模块内部
  让学习者毫无察觉。
- Step 1–3 不启动 Genesis。远端 checkpoint 在 Step 1 显示 `DEFERRED`，只有运行 Step 4
  才下载并审计，然后立即执行 Reference rollout。
- Step 5 使用 `Video(..., embed=True)`，解决浏览器无法直接播放本地路径视频的问题。
- Step 7 是局部的两次运行流程：第一次打印 actual-result evidence card 和 scenario-aware
  sentence stems；学习者在同一个 cell 的 `CAPSTONE_CONCLUSION` 中填写
  `supported_claim`、`unsupported_claim`、`next_evidence`；然后只重跑 Step 7，rollout 不重复。
- 三个 Capstone 字段不得重新移回顶部 `CONFIG`。空字段时打印针对性的 `ACTION REQUIRED`，
  不恢复含义不清的通用 `INCOMPLETE`。
- checkpoint sweep 只保留为 notebook 末尾的可选终端扩展，不增加新的 notebook 分支。

复用实现位于 `src/robo_genesis/l13_workflow.py`，但 notebook 仍直接展示 CONFIG、冻结协议、
condition declaration、evidence audit、matched comparison 和结论填写动作，不能退化成黑盒包装器。

## 5. L13 artifact fallback 与已修复问题

最终可见配置允许学习者提供自己的 artifact，也提供固定 revision 的默认输入：

- checkpoint：`wangxun1010/smolvla-fruit-pick-0821`，revision
  `cdf720f162e6ee86dbc856cdf15c5dcd4a673221`；
- dataset metadata：`wangxun1010/fruit_pick`，revision
  `475e8c6ec7079c4c52b20a0221bf959acb541abd`；
- `CONFIG['checkpoint'] = None` 时使用可见的 course-default checkpoint；
- 优先使用 `CONFIG['dataset_root']` 指向的本地 dataset；目录不存在时只下载 pinned dataset
  的 `meta/**`。评估器读取 dataset contract，不读取训练 episodes 或训练视频；
- 每次正式重跑应使用新的 `run_name`，因为 evaluator 要求 fresh result/video targets。

本轮实际遇到并修复的集成问题：

- 本地 `datasets/fruit_pick` 缺失时 notebook 原本直接失败，现改为上述 pinned dataset metadata
  fallback。
- Hugging Face snapshot 中 processor state 通过 `snapshots/... -> blobs/...` symlink 保存时，
  旧 audit 错报“escapes checkpoint directory”。`training_contract.py` 现在只接受可验证的
  Hugging Face cache blob symlink，仍拒绝任意外部 symlink；相关安全回归测试已覆盖。
- `tqdm` 曾提示 `IProgress not found`，项目现显式依赖 `ipywidgets>=8.1,<9`。
- Step 5 的非嵌入本地视频在浏览器中无法播放，现使用 `embed=True`。
- `src/robo_genesis/l13_workflow.py` 不得重新引入 `RG101_L13_*` 隐藏环境变量；现有测试明确
  禁止该模式。

## 6. L13 正式证据与结论边界

`M3.L13.5` 已验收的主要任务级证据来自参考 AMD Radeon AI PRO R9700、ROCm、
`gs.amdgpu` 与 EGL：

- 20,000-step SmolVLA checkpoint；
- matched seeds `[1000,1001,1002,1003,1004]`；
- Reference：4/5，Wilson 95% interval
  `[0.3755282641185388,0.9637768390302125]`；
- shifted friction `0.9`：5/5，Wilson 95% interval
  `[0.5655085052479191,1.0]`；
- 四个 `unchanged-success`，一个 `failure-to-success`；
- 十个 H.264/yuv420p、30 FPS、`1920×360` 视频通过解码和人工画面审计；
- Reference timeout 与 success/shifted success 的末帧和 JSON termination 一致。

公开的 `gpu-verified` 只证明核心 single-checkpoint closed-loop evaluator 和 evidence contract
在该记录环境通过，不证明：

- friction shift 因果改善性能或统计显著；
- 一般鲁棒性或 OOD robustness；
- 稳定成功率；
- sim-to-real 或真实机器人表现；
- 多 checkpoint learning curve；
- 其他 GPU、操作系统或 viewer 路径。

训练 dataset 缺少 domain-support sidecar，因此 friction `0.9` 必须继续标为 `shifted`，不能
称 OOD。checkpoint sweep 在 `.5` 中明确 `SKIP`，不属于核心 blocker，也没有升级为已验证路径。

在最后的交互 review 中，项目负责人还手动运行了最终中文 notebook 并到达 Step 7；当时填写
内容显示 Reference 5/5、shifted 5/5。为保持课程 notebook clean，这些 output、execution count
和学习者填写内容随后全部清除。该次交互结果没有完整归档到 `COMPATIBILITY.md`，因此不得替代
上述正式 4/5 + 5/5 证据；若未来需要引用 5/5 + 5/5，必须重新运行并保存完整 report、视频、
artifact identity 和环境证据。

## 7. 项目负责人已明确的教学偏好

- 面向有基础 Python/机器学习知识、但刚接触机器人技术与仿真的学习者；先讲清机制，再进入
  实现细节。
- notebook 应线性递进，让学习者一眼看出当前在做什么、为什么做、下一步是什么；避免为工程
  灵活性引入教学上无必要的 modes、flags 和分支。
- 用户需要决定的配置必须在 notebook 可见；共享模块负责复用和安全边界，但不能隐藏实验选择。
- 理论概念可以比 notebook 实践范围更完整，但必须明确“完整技术范畴”和“本课实际实现”的
  边界。
- 结论填写只能在学习者看到实际 evidence 后出现；句式提示应随结果变化，不能让学习者预先猜
  应填写什么。
- 训练 loss、开环动作预测和视频回放不能替代 closed-loop rollout 与明确 success criterion。
- 小样本结果必须报告 `k/n`、Wilson interval、matched outcomes 和限制；不能把 5 episodes
  写成稳定 benchmark。
- EN/ZH notebook code cells 必须逐字一致；Markdown 应自然本地化。
- 相机图像是核心数据时，`render=0` 只能作为受限诊断，不能冒充完整视觉实验。
- 发现课程说法与实现不一致时，先核对实际代码和证据；不得把计划功能或未归档结果写成已验证。

## 8. 最近完整门禁与已知 warning

L13 `.6` 状态同步后的门禁：

- clean-kernel diagnostic：English notebook Step 1–3 在独立 Jupyter kernel 完成 4/4 code
  cells，输出 `status=gpu-verified`、dataset `PASS`、checkpoint `DEFERRED`、
  `Ready to run Step 4: True`，未启动 Genesis；
- course validation：13 lessons、32 localized Markdown files、26 notebooks、42 Python files；
- pytest：95 passed；
- compileall：通过；
- `uv lock --check`：解析 238 packages；
- `npm ci`：安装 190 个包并审计 191 个包；
- 普通与 `EDGEONE=1` 文档构建：通过；
- EN/ZH L13 notebook parity、clean outputs、状态残留扫描和 `git diff --check`：通过。

已知但未自动修复的 warning：

- `npm ci` 报告 14 项既有 advisory（4 low、1 moderate、9 high）；没有运行 `npm audit fix`，
  因为那会改变依赖和锁文件。
- VitePress build 有既有 large-chunk warning，但两种构建都成功。
- managed sandbox 内直接启动 Jupyter kernel 可能因 socket 权限报 `Operation not permitted`；
  `.6` clean-kernel diagnostic 经明确授权在沙箱外启动，只写隔离 `/tmp`。
- managed sandbox 中默认 uv cache 可能不可写；使用任务专用
  `UV_CACHE_DIR=/tmp/<task-cache>` 运行 `uv lock --check`。

## 9. 下一步 M4 的边界

M4 是全课程集成与发布前回归，不是继续扩写或重做某一讲。根计划冻结的步骤为：

1. `M4.1`：按 L01→L13 审计先修关系、跨讲链接、练习输入输出和术语首次解释位置；
2. `M4.2`：核对 EN/ZH 讲义结构、命令、结论、notebook Markdown 与 glossary 一致性；
3. `M4.3`：按课程顺序执行适用的 CPU clean-kernel notebook、Python 门禁和文档构建；
4. `M4.4`：在参考 AMD 环境验证指定 GPU notebook，以及数据→训练→checkpoint→闭环评估的
   纵向接口；
5. `M4.5`：同步 manifest、README、首页、sidebar、frontmatter、notebook metadata、兼容性
   记录和真实状态；
6. `M4.6`：完成 setup、fallback paths、API cheatsheet、instructor guide、引用和第三方许可
   总审计，形成进入 M5 前的验收材料。

只有项目负责人明确启动后才执行 `M4.1`。M4 发现单讲问题时，应回到对应讲次做范围明确的修复
和回归，不进行无关重写；每个 M4 子步骤仍需单独交付和验收，不自动前进。

## 10. 新 thread 恢复顺序

1. 完整读取根目录 `AGENTS.md`。
2. 运行第 2 节 Git 快照命令，确认 handoff 后是否出现新提交或用户修改。
3. 完整读取本文件与 `robo_genesis_101_course_development.plan.md`。
4. 核对 `course.json` 当前状态统计为 8 个 `cpu-verified`、5 个 `gpu-verified`、0 个
   `planned`、0 个 `published`。
5. 若任务涉及 L13，读取 `course_development/lessons/l13.md` 和 `COMPATIBILITY.md`
   第 23–24 节；不要重复已经验收的 GPU rollout 或把已清理的手动 5/5 output 当成正式证据。
6. 若项目负责人明确说“开始 `M4.1`”，先按第 9 节和根计划建立 M4 审计范围；否则只报告当前
   状态，不自动开始 M4。

持续适用的协作边界：每个子步骤完成后单独等待项目负责人验收，不自动开始下一步；不创建
commit、不 push、不发布外部 artifact，除非项目负责人明确要求。
