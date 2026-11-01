# 环境配置与 fallback 路径

本附录区分安装、课程完成路径与诊断路径。依赖解析成功不等于 GPU 已验证，诊断分支也不会
自动替代某讲要求完成的实验。精确的已验证平台与 wheel 校验和仍以
[兼容性矩阵](https://github.com/datawhalechina/robo-genesis-101/blob/main/COMPATIBILITY.md)为准。

## 选择需要的环境

### 只阅读文档

文档 CI 使用 Node.js 24，建议使用相同主版本：

```sh
npm ci
npm run docs:dev
```

使用 `npm run docs:build` 构建静态站点。

### 轻量仓库验证

这个环境不安装 Genesis、PyTorch、LeRobot 或训练栈，只用于课程合同、纯逻辑测试和源码检查：

```sh
UV_PROJECT_ENVIRONMENT=.venv uv sync --only-group dev --locked
uv pip install --python .venv/bin/python --no-deps --editable .
.venv/bin/python -m robo_genesis.course_validation
.venv/bin/python -m pytest
```

它不能执行仿真、渲染、采数、训练或闭环评估。

### 完整核心课程环境

安装可移植依赖集合：

```sh
uv sync --locked --all-extras
uv run python -m robo_genesis.setup_assets
```

第二条命令会验证仓库内置的四个 YCB 对象并返回模型目录。第一条命令不会安装或证明单独实测
的 AMD ROCm wheel 集合；复现参考 AMD 环境时请遵循
[兼容性矩阵](https://github.com/datawhalechina/robo-genesis-101/blob/main/COMPATIBILITY.md)。

L14 不属于这个环境。它使用 [L14 讲义](../lessons/l14-robotwin-lingbot-vla-fine-tuning.md)
说明的固定外部 companion runtime。

## 工作区路径

路径模块第一次被 import 时会解析一个工作区。请在启动 Python 或 notebook kernel 前设置路径
变量。

| 变量 | 默认值 | 用途 |
|---|---|---|
| `ROBO_GENESIS_ROOT` | 当前源码 checkout；否则为工作目录 | 相对路径覆盖项的基准 |
| `ROBO_GENESIS_ASSETS_DIR` | `<root>/assets` | 内置与本地资产 |
| `ROBO_GENESIS_DATASETS_DIR` | `<root>/datasets` | 录制或准备好的 LeRobot 数据集 |
| `ROBO_GENESIS_OUTPUTS_DIR` | `<root>/outputs` | 图像、训练运行、报告与视频 |
| `ROBO_GENESIS_VIEWER` | `0` | 只有 helper 明确支持交互 viewer 时才设为 `1` |

生成的数据集、checkpoint、cache、视频和日志都不进入 Git。除非讲义明确提供 overwrite
开关，否则应使用新的输出名称。

## 运行开关

课程 notebook 会验证这些值，而不是静默切换执行路径：

| 变量 | 接受的行为 |
|---|---|
| `ROBO_GENESIS_BACKEND=auto` | 有可用参考 AMD backend 时选择它，否则选择 CPU |
| `ROBO_GENESIS_BACKEND=cpu` | 强制使用 CPU 路径 |
| `ROBO_GENESIS_RENDER=0` | 关闭本讲相机工作；是否构成完整路径取决于具体讲次 |
| `ROBO_GENESIS_RENDER=1` | 要求执行真实 Genesis 相机路径；渲染错误必须显式保留 |

修改运行开关后要重启 kernel。PyTorch 会通过 `torch.cuda` 命名空间暴露 ROCm 设备，仅凭
命名空间名称不能证明实际使用的是 CUDA 硬件。

以下讲次专用变量用于收窄输入位置，或明确允许一次破坏性替换：

- `RG101_L09_OVERWRITE=1` 允许替换经过校验的精确 L09 输出根目录。
- `RG101_L10_DATASET_ROOT` 和 `RG101_L10_REPO_ID` 为 L10 选择一份兼容本地输入。
- `RG101_L11_BASELINE_ROOT`、`RG101_L11_DATASET_ROOT`、`RG101_L11_PREVIEW_ROOT` 和
  `RG101_L11_BASELINE_REPO_ID` 指定 L11 的明确位置与 identity。
- `RG101_L11_OVERWRITE=1` 允许替换经过校验的精确 L11 数据集与 preview 根目录。
- L12 使用 `RG101_REPO_ID`、`RG101_DATASET_ROOT`、`RG101_OUTPUT_ROOT`、`RG101_SEED`
  和 `RG101_RUN_SMOKE`；SmolVLA smoke 还要求同时提供两个固定的本地 snapshot 路径。

不要仅为了绕过无法解释的目录冲突而设置 overwrite 变量，应先检查现有目录。

## 各讲 fallback 矩阵

| 讲次 | 最低可用路径 | fallback 不能证明什么 |
|---|---|---|
| L01–L07 | CPU 执行是可接受的完成路径。讲义明确说明数值路径完整时，可以关闭渲染。 | render `SKIP` 不是相机证据。 |
| L08 | scripted rollout 与数值证据可以在 CPU 上运行；CPU+EGL 和参考 AMD+EGL 视觉路径也已通过。 | `ROBO_GENESIS_RENDER=0` 不会产生阶段图像证据。 |
| L09 | CPU 诊断会检查采样与 schema。完整实验需要两路真实相机流；CPU+EGL 与参考 AMD+EGL 采数路径均已通过。 | `ROBO_GENESIS_RENDER=0` 不会录制数据集，也不算完成 L09。 |
| L10 | 使用 CPU 只读一份现有兼容 L09 数据集，是可接受路径。 | L10 不生成 fallback 数据、不训练策略，也不推断任务成功。 |
| L11 | CPU 诊断会检查配置、seed 调度、guardrail 与命令。完整 bounded DR 实验需要渲染与录制；CPU+EGL 和参考 AMD+EGL 路径均已通过。 | `ROBO_GENESIS_RENDER=0` 不会生成随机化数据集、preview 或 provenance 结果。 |
| L12 | CPU dry-run 可以验证数据与命令构造。真实 ACT/SmolVLA smoke 训练要求 GPU 和经过审计的输入。 | dry-run、一步 loss 或 open-loop reload 都不代表策略质量或闭环成功。 |
| L13 | CPU/no-checkpoint 诊断可以审计配置与本地输入。完成课程要求 GPU 闭环协议、结构化报告和真实视频。 | open-loop action 生成与诊断报告不等于闭环评估完成。 |
| L14 | 必做路径只接受固定 companion runtime 和 4× W7900D profile。 | 不存在 CPU、单卡、核心环境或无 companion 的完成 fallback。 |

## 数据与 checkpoint 交接

默认本地交接是显式的：

- L09 写入 `ROBO_GENESIS_DATASETS_DIR/l09_banana_demo`，逻辑 ID 为
  `local/l09_banana_demo`。
- L10 读取这份数据，不扫描替代项。
- L11 读取 L09 baseline，并写入 `l11_banana_dr` 与 domain provenance。
- L12 的已验证训练默认输入是单独准备的 `genesis/fruit_pick` 数据集，不是规模很小的 L09
  或 L11 教学数据。
- L13 在评估前要求 dataset/checkpoint identity 匹配。

L13 仍支持显式填写 commit 固定的 Hugging Face 来源，但课程默认交接改为下文由 manifest
管理的本地路径。显式 Hugging Face mapping 是进阶覆盖项，不是第二套课程默认值。

## 版本化 artifact fallback 教程

仓库 manifest 当前列出两个可下载的 **candidate** baseline，以及一个不可用条目。candidate
表示经过审计、身份不可变的 payload baseline，并不是课程正式发布件。下载前先查看状态与精确
默认目标：

```sh
python scripts/fetch_artifacts.py list

python scripts/fetch_artifacts.py fetch \
  rg101-fruit-pick 1.0.0 \
  --allow-candidate

python scripts/fetch_artifacts.py verify \
  rg101-fruit-pick 1.0.0

python scripts/fetch_artifacts.py fetch \
  rg101-fruit-pick-smolvla 1.0.0 \
  --allow-candidate

python scripts/fetch_artifacts.py verify \
  rg101-fruit-pick-smolvla 1.0.0
```

`--allow-candidate` 是对已审计 M5 baseline 的主动 opt-in，不是 release 标记。两个默认精确
根目录分别是 `datasets/fruit_pick` 与
`checkpoints/rg101-fruit-pick-smolvla/1.0.0/pretrained_model`。自定义 `--target` 同样表示
artifact 的精确根目录，CLI 不会再追加 artifact ID。重复执行 `fetch` 会复用有效文件；已有文件
checksum 不匹配时默认停止且不修改，只有显式添加 `--repair` 才会替换。ACT 条目状态为
`unavailable`，不能下载。

### 跳过 L09 采数后继续

下载的数据集可以交给 L10 只读审计和 L12 数据门禁。请在启动 notebook kernel 前设置变量：

```sh
export RG101_L10_DATASET_ROOT=datasets/fruit_pick
export RG101_L10_REPO_ID=genesis/fruit_pick

export RG101_DATASET_ROOT=datasets/fruit_pick
export RG101_REPO_ID=genesis/fruit_pick
export RG101_RUN_SMOKE=0
```

这条路径让无法渲染和录制 L09 的学习者继续后续课程，但**不算完成 L09**：你没有执行 scripted
采集、双相机 recorder、事务边界或吞吐量测量。L12 中的 `RG101_RUN_SMOKE=0` 会保持两项 GPU
训练关闭；数据门禁与命令 dry-run 通过，不表示已经训练 ACT 或 SmolVLA。

### 跳过 L12 训练后继续

两条 `verify` 都通过后，L13 notebook 默认使用上述本地 dataset 与 SmolVLA target，不会隐式
下载 candidate。任何一个根目录缺失或消费者审计失败时，第 1 步都会停止，并指回这套 fetch 与
verify 流程。下载 SmolVLA candidate 后，可以审计 checkpoint/dataset 匹配关系并继续 L13
声明的 GPU 协议，但不能声称模型由自己训练。

下载成功、checksum 通过、数据集可读、checkpoint 可加载、training loss 或 open-loop action
都没有达到闭环证据门槛。只有规定的实时 rollout、结构化报告与真实视频通过各自协议后，才算
完成 L13。全新 cache 下载与 CPU 消费验收已经通过；当前仍保留 `candidate` 标签，是因为参考
AMD GPU release acceptance 与最终发布清单/授权尚未完成。

## 在不隐藏错误的前提下诊断

修改环境前，先对失败分类：

1. **安装：**缺少 import、锁定依赖或原生库。
2. **Backend：**请求的 CPU 或 AMD 设备不可用，或实际设备与报告不符。
3. **渲染：**EGL、相机创建或帧验证失败。
4. **输入 identity：**dataset、checkpoint、snapshot revision、schema 或 repository ID 与命令
   不匹配。
5. **输出安全：**目标已经存在，或不在允许的根目录下。
6. **任务证据：**进程执行了，但成功谓词、视频或报告检查失败。

不要用未声明的 CPU 结果覆盖失败的 GPU 运行，不要伪造相机图像，也不要用训练 loss 替代闭环
任务证据。应记录请求与实际 backend、精确输入 identity、命令以及所有未运行检查。

## Setup 检查清单

- 仓库和所选讲次输入位于本地存储。
- Python 为 `3.12.x`，已安装包版本与兼容性记录一致。
- `robo_genesis.setup_assets` 验证通过全部四个内置 YCB 对象。
- dataset 与 output 根目录可写，且不位于 tracked 源文件内。
- 所有环境变量设置完毕后才启动 notebook kernel。
- 第一段诊断输出明确显示请求的 backend 与渲染路径。
- GPU-required 工作使用经过审计的 GPU、dataset 与 checkpoint，而不是静默诊断 fallback。
- L14 只在固定外部 companion profile 中运行。
