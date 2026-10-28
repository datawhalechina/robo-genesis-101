# RoboGenesis 101 当前工作交接

最后核对日期：2026-10-28（Asia/Shanghai）。

本文件只记录新 thread 最容易丢失的当前状态、验收边界、项目负责人偏好、未决项与
恢复顺序。通用规则以根目录 `AGENTS.md` 为准；课程总计划与门禁以本地
`robo_genesis_101_course_development.plan.md` 为准；L14 详细历史位于
`course_development/lessons/l14.md`；实测兼容性公开摘要以 `COMPATIBILITY.md` 第 25 节为准。

## 1. 一句话恢复状态

- L01–L13 核心课程已全部完成并通过项目负责人验收。
- L14 是不影响核心 13 讲完成路径的可选进阶实践。`M3.R14.1`–`.R14.2` 与
  `M3.L14.1`–`.L14.6` 已全部验收并冻结；L14 公开状态为 `gpu-verified`。
- 项目负责人于 2026-10-28 明确确认 `M3.L14.6` 验收通过。L14 开发轮次至此完成。
- M4 未启动。只有项目负责人另行明确说“开始 `M4.1`”后，才能开始跨讲整合。
- `docs/handoffs/current.md` 只在项目负责人准备切换 thread 时更新；不要在每个小步骤
  例行修改。

## 2. Git 快照、CI 与工作树保护

更新本文件前的快照：

- 当前分支：`main`；
- 本地 HEAD：`d22912fd0979a251c663a47044aab24e671ec961`；
- HEAD 标题：`update COMPATIBILITY doc after l14`；
- `origin/main` / `origin/HEAD`：
  `1f3fa95eec9d34f2a90556d4276daf3d601a2d20`；本地 `main` 当前领先 1 个提交；
- 最新课程验证：[Actions run 40494363506](https://github.com/datawhalechina/robo-genesis-101/actions/runs/40494363506)，`success`；
- 最新 Pages deploy：[Actions run 40494363640](https://github.com/datawhalechina/robo-genesis-101/actions/runs/40494363640)，`success`。

前一个 Validate run
[40492717208](https://github.com/datawhalechina/robo-genesis-101/actions/runs/40492717208)
曾因 `COMPATIBILITY.md` 链接本地未跟踪的
`course_development/evidence/l14-m3-l14-5-four-w7900-execution-2026-10-27.json` 失败。
本地 validator 只检查文件是否存在，因而被未跟踪文件掩盖。已按项目负责人决定删除
公开可点击链接：机器可读 evidence 只保留在本地开发档案，`COMPATIBILITY.md` 第 25 节
保留完整公开摘要。修复后上述 Validate 和 Deploy run 均通过。

新 thread 首先重新运行：

```sh
git status --short --branch
git log -5 --oneline --decorate
```

更新本 handoff 前除本文件已有的交接更新外，没有其他未提交 tracked 修改；更新后预期只有
`docs/handoffs/current.md` 是 tracked 修改。下列 untracked 内容是已有本地配置、补丁或开发档案，
必须保留，不得清理、覆盖或误当成新 thread 产生的垃圾：

- `.vscode/`；
- `0001-4-cards-failure.patch`；
- `0001-add-en-zh-lecture-of-l13-closed-loop-evaluation.patch`；
- `0001-rewrite-l09-lectures.patch`；
- `MIGRATION.md`；
- `course_development/`；
- `genesis_公开课体系规划_2ba5d82e.plan.md`；
- `robo_genesis_101_course_development.plan.md`。

其中 `MIGRATION.md`、`course_development/` 和根开发计划虽然未跟踪，仍是当前开发状态的
重要真相源。普通 `git diff` 不会显示它们的内容，不要因此忽略或删除。

## 3. 当前公开课程状态

`course.json` 定义 14 讲，即 13 讲核心课程 + 1 讲可选进阶实践：

- L01–L07、L10：8 个 `cpu-verified`；
- L08、L09、L11、L12、L13、L14：6 个 `gpu-verified`；
- 0 个 `planned`；
- 0 个 `published`。

L14 保持 180 分钟、`gpu-required`、slug `robotwin-lingbot-vla-fine-tuning`。以下公开状态源
已一致同步为 `gpu-verified`：

- `course.json`；
- EN/ZH L14 讲义 frontmatter 与顶部状态说明；
- EN/ZH L14 notebook metadata；
- `README.md`、`README_en.md`、根/双语首页；
- `CONTRIBUTING.md`；
- manifest 与 L14 notebook 合同测试；
- `COMPATIBILITY.md` 第 25 节。

VitePress sidebar 由 `course.json` 动态读取 lesson path/title，没有独立 status literal，
因此 `.L14.6` 没有修改 `docs/.vitepress/config.mts`。

## 4. L14 课程交付物与教学合同

L14 讲义的四项高层学习目标为：

1. 解释 RoboTwin demonstrations 如何转换为 LingBot-VLA-v2 训练输入；
2. 配置并比较 action-expert LoRA 与 full-parameter SFT；
3. 把 distributed training checkpoint 转换为可部署 Hugging Face model 并进行 serving；
4. 在受控闭环协议下比较 base 与 fine-tuned policy，并报告边界清晰的结论。

EN/ZH notebook 当前均为精确 43 cells / 20 code cells / 23 Markdown cells；保持原始
`RoboTwin_ROCm_Reproduction.ipynb` 的 cell-type 序列与技术覆盖。双语 code cell IDs 和
source 逐字一致，提交版 outputs 为空、`execution_count: null`。

180 分钟必做路线：

```text
source/runtime/data preflight
  → base 10 episodes
  → 4-GPU 100-step action-expert LoRA
  → DCP audit
  → LoRA merge to fresh Hugging Face checkpoint
  → merged 10 episodes
  → aggregate evidence card
```

原 notebook 中的 official RoboTwin checkpoint、4/8-GPU 1000-episode benchmark、merged-LoRA benchmark
和 full-parameter SFT 仍保留在同一 notebook 中，但都是章节内 opt-in 扩展，不得写成
本轮 RoboGenesis 已验证结果。

## 5. M3.L14.5 已验收的四卡证据

成功 run：`l14-adjust-bottle-4gpu-20261027t0822z`。

环境与输入：

- 4× `AMD Radeon PRO W7900D`，`gfx1100`；
- Python `3.12.3`；
- PyTorch `2.9.1+rocm7.2.1.gitff65f5bc`；
- HIP `7.2.53211-e1a6bc5663`；
- companion `27b2f6fcb6c715e2cbb6db4431381f87c94b86ed`，worktree 未修改；
- 50 个 demo task、50 个 LeRobot dataset 和 50 条 training manifest entry 通过 preflight。

实际结果：

- base：`0/10`，Wilson 95% interval `[0.0, 0.2775401688]`；
- 4-GPU LoRA：100 steps，rank 8，alpha 16，global batch 4，seed 42，约 6.01 分钟；
- DCP：134 files，`24,970,824,371` bytes；
- merge：144 LoRA layers，HF 14 files / 3 weight shards / `12,467,433,466` bytes；
- merged：`0/10`，Wilson 95% interval `[0.0, 0.2775401688]`；
- observed aggregate difference：`0.0`；
- base/merged 各 10 个 H.264 视频，320×240、400 frames、40 秒，20 个全部可解码；
- 四卡峰值显存：`25,720 / 24,239 / 24,239 / 25,720 MB`；
- run root：`37,464,653,433` bytes。

100 steps 只证明 data/forward/backward/update/save/merge/serve/evaluate 管线可执行，不证明
loss 收敛或策略质量提升。base 与 merged 均为 `0/10` 也不能外推为模型没有潜力。

## 6. Evaluator 分母与 resolved-seed 边界

固定 companion 的 serial `eval_batch=false` evaluator 可能在实际只完成 5 个 policy episodes
时仍打印请求时的 `Final success rate: 0/10`。课程不修改 companion，而在 notebook 中：

- 以最后一条 incremental `Success rate: k/n` 确定实际完成分母；
- 为剩余 episodes 启动 fresh serial invocation；
- 每次 invocation 保存独立 raw log、attempt summary 和视频目录；
- base/merged 均以 `5+4+1` 补齐真实 10 episodes；
- 基础设施非零退出仍中止 run。

当前 companion 不输出逐 resolved-seed policy outcome。attempt summaries 只是 invocation-level
collection evidence，不能代替 episode rows。因此当前只能报告两个独立 aggregate，
不得声称 resolved-seed matched improvement/regression。这个缺口不阻塞 LoRA、full-SFT、merge、
serving 或 aggregate closed-loop evaluation 教学主线。

面向学习者的讲义已将工程 workaround 压缩为“分母对应实际完成 episodes、notebook
自动补齐并保存证据、基础设施错误仍中止”。requested-slot 消耗时机、basename、
attempts JSON 等细节留在 notebook/helper/开发档案，不占用讲义主线。

## 7. Companion 与本地 evidence 的保护边界

- `Robotwin-radeon-cloud` 正在竞赛期，当前不修改 companion。
- 已设计的版本化逐 attempt/episode JSONL 增强已冻结为本地 patch：
  `course_development/patches/robotwin-radeon-cloud-jsonl-evidence-v1.patch`。
- patch SHA-256：`c98cbfee0f6e69fbcf36f5e61e23ebe966d11854a77fe3ca27fff8157dc14983`；
  详细 schema、invariants、静态验收和未来恢复步骤见
  `course_development/issues/l14-robotwin-companion-jsonl-evidence-deferred.md`。
- 只有项目负责人未来明确恢复该延期项时，才能对当时 companion `main` 重新审计/移植/实跑。
- `course_development/evidence/` 下的四份 L14 JSON 为本地开发 evidence，不提交到公开仓库。
- `COMPATIBILITY.md` 不得再建立指向上述未跟踪文件的 Markdown 链接；第 25 节的
  精确 runtime、result、resource、video 和 limitation 摘要就是公开证据记录。

## 8. 项目负责人已明确的 L14 教学偏好

- 原始 `RoboTwin_ROCm_Reproduction.ipynb` 是经过路径验证的竞赛参考。原始 43 cells /
  20 code cells 的技术覆盖必须充分保留；若认为某内容不妥，必须列出并与项目负责人
  讨论，不得静默忽略或删除。
- 讲义面向学习者，不得出现 `M3.L14.5` 等内部开发里程碑编号。
- 学习目标必须是 high-level 教学目标，不能写成细碎验收项。
- L14 hardware/runtime 说明应把 AMD 环境本身说清楚，不要引入不必要的 NVIDIA 对比。
- 课程最重要的是教会学习者运行 VLA LoRA 与 full SFT 工作流；resolved-seed matched
  evidence 只会收窄最终比较结论，不得阻塞整讲主线。
- 讲义讲清原则，notebook 承载可执行步骤，helper 承载复用/安全边界；不要把工程实现流水账
  放进讲义。
- 结论不得超出证据：训练 loss、100-step pipeline、小样本 aggregate 和视频回放都不能
  代替受控闭环评估或证明策略提升。

## 9. M3.L14.6 交付门禁与已知 warning

`.L14.6` 实现交付时的本地门禁：

- `course.json` 与 EN/ZH notebook JSON 解析通过；
- L14 manifest/notebook/workflow 定向测试：21 passed；
- 全量 pytest：107 passed；
- compileall：通过；
- course validation：14 lessons、34 localized Markdown files、28 notebooks、45 Python files；
- `npm ci`：安装 190 packages，审计 191 packages；
- VitePress build：通过；
- EN/ZH L14 notebook：43 cells / 20 code cells，code IDs/source 一致，outputs 为空；
- learner-facing `planned`/scaffold 残留扫描、状态表一致性与 `git diff --check`：通过。

公开 commit `1f3fa95` 的 Validate 与 Pages deploy 也均通过。

已知但未自动修复：

- `npm ci` 报告 15 项既有 advisory（4 low、1 moderate、10 high）；没有运行 `npm audit fix`；
- VitePress build 有既有 large-chunk warning，但 build 成功；
- full GPU notebook、checkpoint、logs 和视频不进入 Git；四卡执行证据由 `.L14.5` 已验收运行
  和 `COMPATIBILITY.md` 第 25 节支持，`.L14.6` 不重复远程 GPU 训练。

## 10. 下一阶段与新 thread 恢复顺序

`M3.L14.6` 的验收接受了以下边界：L14 `gpu-verified` 严格限定为固定 companion +
4× W7900D 必做路径；base/merged `0/10` 只是独立 aggregate 小样本；resolved-seed matched
outcomes 不可用；讲义采用学习者视角压缩 evaluator workaround；`COMPATIBILITY.md` 第 25 节
记录精确证据和未运行项；sidebar 因动态读取 manifest 无需独立修改。

当前没有已启动的开发步骤。下一候选阶段是 M4 全课程集成与发布前回归，但尚未开始。

新 thread 恢复顺序：

1. 读取 `AGENTS.md`、本文件、`COMPATIBILITY.md` 第 25 节、
   `course_development/lessons/l14.md` 第六节和根开发计划的 L14 部分。
2. 运行第 2 节的 Git 快照命令，保留所有已有 untracked 内容。
3. 确认 `.L14.6` 验收结论已经同步到根计划、L14 单课档案、`MIGRATION.md` 与
   `COMPATIBILITY.md`。
4. 不要因 `.L14.6` 已验收自动开始 M4；等待项目负责人另行明确启动 `M4.1`。
5. 除非项目负责人明确恢复 companion JSONL 延期项，不要修改 `Robotwin-radeon-cloud`。

M5 仍未启动。L13/L14 已有的 checkpoint/runtime 证据不等于 M5 的版本化 artifact
发布、checksum、license/model card、下载工具和 V1 发布流程已完成。
