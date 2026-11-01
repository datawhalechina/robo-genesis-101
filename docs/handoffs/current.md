# RoboGenesis 101 当前工作交接

最后核对日期：2026-11-01（Asia/Shanghai）。

本文件只记录新 thread 最容易丢失的当前状态、项目负责人偏好、操作陷阱、未决项与恢复顺序。
通用规则以根目录 `AGENTS.md` 为准；课程总计划与门禁以本地
`robo_genesis_101_course_development.plan.md` 为准；M4/M5 逐步验收记录位于
`course_development/m4.md` 与 `course_development/m5.md`；公开运行与平台证据以
`COMPATIBILITY.md` 为准。

## 1. 一句话恢复状态

- M0–M4 已全部完成并通过项目负责人验收。
- M5.1–M5.8 已全部完成并通过项目负责人验收；M5 阶段已经完成。
- 项目负责人已明确授权把 `rg101-fruit-pick@1.0.0` 与
  `rg101-fruit-pick-smolvla@1.0.0` 从 `candidate` 提升为 `release`，仓库 manifest、双语
  教学材料和测试已同步；ACT 仍为 `unavailable`。
- 当前 canonical 状态为 8 个 `cpu-verified`、6 个 `gpu-verified`、0 个 `planned`、
  0 个 `published`。本次授权不修改 lesson 状态；`verified` 不等于 `published`。
- `docs/handoffs/current.md` 在重大阶段边界或准备切换 thread 时更新，不要在每个小步骤例行修改。

## 2. Git 快照与工作树保护

当前快照：

- 当前分支：`M5`；
- 本地 HEAD：`c87d4f1`，标题 `verification of cpu gpu smoke`；
- `origin/main` / `origin/HEAD`：`29cdd70`，标题 `update current doc after M4`；
- M5 tracked 提交依次包括：
  - `0464bc3`：dataset schema、许可与版本规则；
  - `74c8902`：ACT/SmolVLA checkpoint 记录；
  - `d236131`：artifact manifest 与 downloader；
  - `b383adc`：双语 fallback；
  - `947c9ee`：README、首页、sidebar、讲义与 notebook 状态核对；
  - `c87d4f1`：CPU/GPU smoke 与 release acceptance 记录。

当前 tracked 工作树包含 M5.8 release promotion 的 manifest、双语文档、L13 notebook、测试、
兼容性与 NOTICE 修改；这些是当前任务结果，不要清理。下列 untracked 内容是已有本地配置、
补丁或开发档案，必须保留，不得清理、覆盖或误当作新 thread 产生的垃圾：

- `.vscode/`；
- `0001-4-cards-failure.patch`；
- `0001-add-en-zh-lecture-of-l13-closed-loop-evaluation.patch`；
- `0001-rewrite-l09-lectures.patch`；
- `MIGRATION.md`；
- `course_development/`；
- `genesis_公开课体系规划_2ba5d82e.plan.md`；
- `robo_genesis_101_course_development.plan.md`。

其中 `MIGRATION.md`、`course_development/` 和根开发计划虽然未跟踪，仍是重要开发真相源。
普通 `git diff` 不会显示它们的修改，不要因此忽略或删除。

本次没有重新查询 GitHub Actions 或 Pages 状态。本地 `M5` 分支领先 `origin/main`，且当前
release promotion 仍是未提交工作树修改。新 thread 如需引用最新 CI/Pages 结论，应先重新
查询，不能根据本 handoff 猜测。

## 3. M4 最终交付与公开课程状态

`course.json` 当前定义 13 讲核心课程和 1 讲可选 L14：

- L01–L07、L10：8 个 `cpu-verified`；
- L08、L09、L11–L14：6 个 `gpu-verified`；
- 0 个 `planned`；
- 0 个 `published`。

M4.5 已核对 `course.json`、双语 README、根/双语首页、动态 sidebar、28 份 canonical 双语
讲义 frontmatter 与 28 份 notebook metadata。它们保持一致，没有因“所有讲次都存在”而
人为提升到 `published`。

M4.6 新增并公开了五对非讲次辅助页面：

- `docs/{zh,en}/appendix/setup-and-fallbacks.md`；
- `docs/{zh,en}/appendix/glossary.md`；
- `docs/{zh,en}/appendix/api-cheatsheet.md`；
- `docs/{zh,en}/appendix/instructor-guide.md`；
- `docs/{zh,en}/references/index.md`。

这些页面没有 lesson frontmatter 或独立课程状态。VitePress nav/sidebar、双语 README、首页和
`AGENTS.md` 仓库结构已经同步；localized Markdown 合同计数因此从 34 变为 44。

## 4. M4 回归证据与结论边界

M4.3 按课程顺序完成 26 份适用的双语 CPU clean-kernel/diagnostic notebook；L14 外部
companion 不加入核心 CPU 回归。

M4.4 在参考 `AMD Radeon AI PRO R9700`、固定 ROCm/PyTorch、Genesis 1.3.3、LeRobot 0.6.0
与 EGL 环境完成纵向接口回归：

- L08、L09、L11 English AMD+EGL notebook；
- 同轮 L09 新数据生成后由 L10 只读回读；
- ACT/SmolVLA 1-step GPU smoke、numeric checkpoint audit 与 open-loop reload；
- 两个 checkpoint 各进入一个 L13 15 秒 reference closed-loop episode，并生成结构化报告与
  H.264 视频；
- L14 复用已经验收的固定 companion + 4× W7900D evidence，没有在 R9700 上伪造或扩大
  L14 结论。

这些运行只证明纵向接口和 integration contract。1-step loss、单样本 open-loop reload、
单 episode timeout、L14 100-step LoRA 或独立 aggregate 都不能证明收敛、策略质量提升、稳定
成功率、OOD robustness 或 sim-to-real。

M4.3/M4.4 的临时 dataset、checkpoint、视频、日志和 executed notebook 不属于 M5 release
artifact，不应在新 thread 中当成可发布资源或依赖其 `/tmp` 路径仍然存在。

## 5. 项目负责人在 M4 明确的术语与写作偏好

- `rollout`、`domain randomization` 等稳定技术词在中文工程语境中可以保留英文，不要为了
  表面中文化而强行翻译。
- `scripted rollout` 保留英文词组，不写成 `scripted rollout（回合执行）`。
- `seed demonstration` 应在中文解释后保留英文，例如“种子演示数据（seed demonstration）”。
- 仅中文容易产生歧义时，使用“中文解释（原英文词组）”；不要机械给所有技术词加括号。
- dataset path、repository ID、artifact revision 和 checkpoint identity 必须分开表达。
- 不得把 loss、open-loop playback/reload、视频主观观察或 pipeline 完成写成 closed-loop success。
- 双语 shell 命令必须逐字一致；EN/ZH notebook code cell ID/source 继续保持相同。

上述偏好已经进入公开 glossary、讲义修正和合同测试。后续修改中文材料时应继续遵守，不要
把 M4.2 已按项目负责人反馈保留的英文技术词重新机械翻译。

## 6. Setup、fallback 与 API 的冻结边界

- dependency-light validation 环境不包含 Genesis、PyTorch、LeRobot 或训练栈。
- `uv sync --locked --all-extras` 只表示完整可移植依赖解析，不构成参考 AMD ROCm 验证。
- L01–L07、L10 有已验收 CPU 完成路径。
- L08 的 scripted rollout 数值路径可在 CPU 执行，但关闭渲染不产生阶段图像证据。
- L09/L11 的 `ROBO_GENESIS_RENDER=0` 只是诊断，不能冒充 dataset、preview 或 provenance
  生成完成。
- L12 CPU dry-run 不替代 GPU smoke；L13 CPU/no-checkpoint 诊断不替代 GPU closed-loop。
- L14 只有固定 external companion + 4× W7900D 必做路径；没有 CPU、单卡、核心环境或无
  companion 的完成 fallback。
- L13 的 commit-pinned、opt-in Hugging Face source declaration 不是 M5 通用 artifact downloader。
- API cheatsheet 只列当前 `src/robo_genesis/` 真实课程接口；以下划线开头的实现细节和
  notebook-local helper 不应升级成公共 API。

## 7. 引用、许可与发布前未决项

当前许可边界：

- 原创课程代码、讲义、notebook、练习和原创媒体：除另有注明外采用 MIT；
- 四个 vendored YCB 对象：CC BY-NC 4.0，不属于 MIT；
- Franka：使用固定 Genesis 自带模型，不 vendor 旧 source-course bundle；
- Genesis、LeRobot、论文、外部 dataset/model：继续作为引用、链接或安装依赖；
- LingBot-VLA-v2 base、RoboTwin dataset 与 L14 companion image：不 rehost；
- 生成 dataset/checkpoint/log/frame/video：默认不进入 Git，也没有默认再分发授权；本次明确
  例外是已固定托管 revision、许可和 checksum 的 `rg101-fruit-pick@1.0.0` 与
  `rg101-fruit-pick-smolvla@1.0.0` release。

Datawhale 品牌和模板媒体仍是明确未决项：

- `docs/public/datawhale-logo.png` 与 `docs/public/learning.GIF` 不属于项目 MIT 授权；
- 本地没有记录 Datawhale 品牌/商标使用授权；
- V1 release 前必须由项目负责人确认授权并补充记录，或替换/移除相应媒体；
- 未确认前不要修改、重新设计或对外发布这些品牌素材。

## 8. 构建与验证时容易遗漏的操作细节

### VitePress 构建必须顺序执行

不要并行运行：

```sh
npm run docs:build
EDGEONE=1 npm run docs:build
```

两次构建共享 `docs/.vitepress/.temp`。M4.6 中并行执行曾产生大量虚假的
`ERR_MODULE_NOT_FOUND` 和 `Unexpected identifier`；改为顺序执行后两种 build 都通过。

### 站点页面不能相对链接到 `docs/` 之外

Python course validator 能解析指向仓库根文件或 `src/` 的相对路径，但 VitePress 会把站点
源码目录之外的这些链接判为 dead link。公开 appendix/references 中链接
`COMPATIBILITY.md`、`NOTICE.md`、`LICENSE_POLICY.md` 或 `src/robo_genesis/*.py` 时，应使用
canonical GitHub URL，不要恢复成 `../../../...`。

### 已知非阻塞 warning

- `npm ci` 报告 15 项既有 advisory（4 low、1 moderate、10 high）；M4 没有运行
  `npm audit fix` 或自动升级依赖。
- VitePress build 保留既有 large-chunk warning，但构建成功。

当前 M5.8 门禁：14 lessons、44 localized Markdown files、28 notebooks、49 Python files；
126 项 pytest；compileall、238-package `uv lock --check`、`npm ci`、普通与 EdgeOne build、
`git diff --check` 全部通过。

## 9. M5 当前状态与 release 边界

M5.1–M5.8 已逐步完成并验收。M5.8 已完成 artifact release promotion 与完整本地回归：

- dataset：`rg101-fruit-pick@1.0.0`，状态 `release`，固定 revision
  `eab67399248de625506d43fdeb994788874a8492`，9 个文件；
- SmolVLA：`rg101-fruit-pick-smolvla@1.0.0`，状态 `release`，固定 revision
  `6649cc34576b1bf6a7ed1310251ece8c969dfafe`，7 个文件；
- ACT：`rg101-fruit-pick-act@1.0.0`，状态 `unavailable`；20,000-step payload 在冻结的
  reference 与 shifted-friction 协议中均为 0/5 timeout，因此没有被选为 learner fallback；
- 两项 release 使用普通 `fetch` 命令，不需要 `--allow-candidate`；下载器仍保留对其他
  candidate 条目的通用显式 opt-in 保护；
- L13 notebook 不隐式下载课程 artifact，只审计本地默认目标或学习者显式填写的固定来源；
- lesson 状态继续为 8/6/0/0，不因 artifact release 自动提升为 `published`。

本次授权只覆盖仓库内两项 artifact 的 `candidate → release` 状态提升。它不授权创建 GitHub
Release、push、部署 Pages、重新上传 Hugging Face 内容或修改 lesson `published` 状态。

## 10. 新 thread 恢复顺序

1. 读取根 `AGENTS.md`、本文件、根开发计划的 M5 部分、`course_development/m5.md` 尾部、
   `course_development/m5_release_checklist.md`，以及 `COMPATIBILITY.md` 第 32 节。
2. 运行：

   ```sh
   git status --short --branch
   git log -8 --oneline --decorate
   ```

3. 保留第 2 节列出的所有 untracked 文件和目录。
4. 确认 M5.1–M5.8 已全部验收；artifact 状态为 release/unavailable/release，
   lesson canonical 状态仍为 8/6/0/0。
5. 如需引用 CI 状态，重新查询 GitHub Actions；不要沿用本文件未能联网确认的结果。
6. 不要重做已完成的 M5 步骤；等待项目负责人明确启动后续阶段。
7. 除非项目负责人明确恢复延期项，不修改 `Robotwin-radeon-cloud` 或应用旧 companion JSONL
   patch。
