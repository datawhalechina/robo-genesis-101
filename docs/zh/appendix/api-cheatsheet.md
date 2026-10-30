# API 与命令速查表

可复用行为位于 `src/robo_genesis/`；notebook 是教学入口，不是另一套独立实现。本页列出当前
讲义实际使用、面向课程的稳定接口。修改协议前，应阅读链接的源码和对应讲义。

package 根目录只导出 `__version__`，helper 应从定义它的 module import。以下不列出以下划线
开头的实现细节。

## 路径与诊断

| 接口 | 用途 |
|---|---|
| [`ProjectPaths`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/paths.py)、`resolve_project_paths()` | 根据可移植默认值与 `ROBO_GENESIS_*` 覆盖项解析 project、asset、dataset 和 output 根目录。 |
| `resolve_cli_path()` | 根据当前工作目录或绝对默认值解析 CLI 路径。 |
| [`environment_report()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/course_utils.py) | 输出 Python、平台、Genesis、PyTorch/HIP 和加速器 identity。 |
| `select_backend()` | 有可用参考 AMD ROCm 时优先选择，否则返回 Genesis CPU backend。 |
| `to_numpy()` | 把 Genesis、Torch 或 NumPy 值转换成 detached CPU NumPy array。 |
| `assert_pose_close()` | 校验测量向量与目标值，并返回欧氏误差。 |
| `notebook_mode()` | 创建一个 output 目录，并解析可选 viewer 开关。 |

请在 import `robo_genesis.paths` 前设置路径变量，因为 module-level 常量会在 import 时解析。

## 资产与场景

| 接口 | 用途 |
|---|---|
| [`setup_assets()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/setup_assets.py) | 校验内置 YCB 的许可/provenance 文件和 SHA-256 manifest，然后返回 models 目录。 |
| [`build_scene()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/build_scene.py) | 按声明的相机、环境数量和可选 build-time DR 构建课程 Franka/table/YCB 场景。 |
| `SceneBundle` | 保存 scene、Franka entity、YCB entity、camera 与 table entity；wrist 渲染前调用 `update_wrist_cam()`。 |
| `SceneDomainRandomizationConfig` | 配置 build-time 外观与相机内参随机化；新的外观 domain 需要重新 build scene。 |
| [`get_ycb_assets()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/scene_config.py) | 返回从已配置 models 目录解析出的经审计 YCB metadata。 |

每个进程只能按课程路径初始化一次 Genesis，调用 `build_scene()` 前先完成初始化。camera 必须在
`scene.build()` 前加入；关闭渲染的分支不能伪造替代帧。

## 脚本化任务执行

| 接口 | 用途 |
|---|---|
| [`TaskSpec`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/grasp_demo.py) | 声明 `pick_object`、`place_target` 与 `success_tol`。 |
| `GraspProfile` | 保存每类对象的 top-down grasp 参数。 |
| `run_pick_place()` | 执行显式 scripted expert 阶段，并可向 episode recorder 送入采样。 |
| `check_success()` | 计算共享的水平放置与低于碗沿包含关系成功判据。 |
| [`EpisodeRecorder`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/record_dataset.py) | 在 scripted rollout 中采样同步 state、action 与 camera observation。 |
| `build_features()` | 为声明的图像尺寸构造课程 LeRobot feature schema。 |

正常创建数据集时应使用 recorder CLI。直接使用 `EpisodeRecorder` 只适用于讲义级检查，或有意
保持相同时间合同的扩展。

## Domain randomization 与 provenance

| 接口 | 用途 |
|---|---|
| [`DomainRandomizationConfig`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/randomize.py) | 配置 per-episode runtime friction、mass 与 world-camera extrinsic 范围。 |
| `RandomizationConfig` | 配置 pose/task 随机化、settle steps、容差、seed 与嵌套 runtime DR。 |
| `EnvRandomizer` | reset 已 build 场景，并使用显式 seed 采样一个 task/domain。 |
| [`validate_dr_collection_config()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/domain_provenance.py) | 录制前校验 bounded collection 合同。 |
| `plan_seed_schedule()` | 构造确定性的 attempt 与 appearance-domain 调度。 |
| `write_domain_provenance()` / `load_domain_provenance()` | 持久化并验证机器可读 collection provenance。 |
| `plan_domain_split()` / `validate_domain_split()` | 创建或检查 domain-aware dataset split。 |

Build-time appearance DR 与 runtime DR 是不同层。不能用其中一层的变化声称另一层也已覆盖。

## 训练、checkpoint 与评估

| 接口 | 用途 |
|---|---|
| [`robo_genesis.train_policy`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/train_policy.py) | 构造经审计 ACT 或 SmolVLA `lerobot_train` 命令的轻量 CLI wrapper。 |
| [`audit_dataset_contract()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/evaluation_contract.py) | 评估前检查 LeRobot identity、metadata、camera key、state/action 维度与 FPS。 |
| `validate_evaluation_protocol()` | 校验 episode 数、时间、对象、seed、容差和 condition 声明。 |
| `validate_action_vector()` / `normalize_policy_action()` | 拒绝 shape 错误或非有限 policy action，并规范化接受的输出。 |
| `build_evaluation_report()` / `validate_evaluation_report()` | 创建并审计结构化闭环 evidence report。 |
| [`robo_genesis.eval_policy`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/eval_policy.py) | 加载支持的策略并执行声明的闭环协议。 |
| [`robo_genesis.eval_sweep`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/eval_sweep.py) | 在同一固定协议下评估带数字编号的 checkpoint，并写入 JSON、CSV 与曲线。 |
| [`wilson()` 与 `newcombe_diff()`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/stats.py) | 计算课程使用的二项比例区间与独立比例差区间。 |

`train_policy` 默认使用 PyAV dataset decoder。命令成功构造、一步训练或 open-loop reload 只能
证明接口集成。任务性能结论来自闭环协议。

## L13 workflow helper

[`l13_workflow.py`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/l13_workflow.py) 在 evaluator 进程真正启动前保持
notebook orchestration 依赖轻量。

| 接口 | 用途 |
|---|---|
| `prepare_l13_workflow()` | 解析本地输入、output 根目录与可选 commit 固定 fallback 声明。 |
| `audit_l13_inputs()` / `require_l13_inputs()` | 报告或强制要求 dataset/checkpoint readiness。 |
| `declare_l13_conditions()` | 校验 reference 与 shifted/OOD condition 声明。 |
| `build_l13_evaluation_command()` | 在不调用 shell 的情况下构造 evaluator 命令。 |
| `run_l13_condition()` | 使用记录的环境覆盖项执行一个声明 condition。 |
| `audit_l13_evidence()` / `compare_l13_runs()` | 检查报告/视频并比较结果，不夸大因果证据。 |
| `write_l13_capstone_report()` | 根据已审计运行写入 JSON 与 Markdown Capstone evidence。 |

Hugging Face fallback 解析要求精确 repository ID、40 位十六进制 commit 和 subfolder。下载必须
显式 opt-in；无法解析的来源保持 unavailable，不能用无关本地 artifact 替代。

## L14 隔离 helper

[`l14_workflow.py`](https://github.com/datawhalechina/robo-genesis-101/blob/main/src/robo_genesis/l14_workflow.py) 校验 notebook 可见配置、路径、命令、
checkpoint 结构、日志、视频和 aggregate evidence。它有意不 import、patch 或替换外部 companion。

常用接口包括 `validate_l14_config()`、`l14_output_paths()`、`audit_required_paths()`、
`audit_hf_checkpoint()`、`build_single_task_eval_command()`、`run_command_logged()`、
`parse_final_success_rate()` 和 `build_aggregate_evidence_card()`。

这些 helper 不是可移植 L14 runtime。固定 companion commit 与必需 4-GPU profile 仍属于课程合同。

## 命令入口

调整命令前先运行 `--help`：

```sh
uv run python -m robo_genesis.setup_assets
uv run python -m robo_genesis.build_scene --help
uv run python -m robo_genesis.grasp_demo --help
uv run python -m robo_genesis.record_dataset --help
uv run python -m robo_genesis.train_policy --help
uv run python -m robo_genesis.eval_policy --help
uv run python -m robo_genesis.eval_sweep --help
.venv/bin/python -m robo_genesis.course_validation
```

| Module | 常规用途 |
|---|---|
| `build_scene` | 场景/资产/camera smoke 与 build-time DR 检查 |
| `grasp_demo` | 一次参数化 scripted pick-and-place 执行 |
| `record_dataset` | 把成功 episode 事务式录制为本地 LeRobot dataset |
| `train_policy` | ACT 或 SmolVLA 训练命令 wrapper；`--` 后的参数原样传给 LeRobot |
| `eval_policy` | 在一个声明的闭环 condition 下评估一个 checkpoint |
| `eval_sweep` | 在匹配协议下评估多个带数字编号的 checkpoint |
| `course_validation` | 双语结构、metadata、链接、notebook、源码安全与仓库合同 |

## 最小场景模式

```python
import genesis as gs

from robo_genesis.build_scene import build_scene
from robo_genesis.course_utils import select_backend
from robo_genesis.grasp_demo import TaskSpec, check_success, run_pick_place

gs.init(backend=select_backend(), seed=0, precision="32", logging_level="warning")
bundle = build_scene(show_viewer=False, add_world_cam=False, add_wrist_cam=False)
task = TaskSpec(pick_object="011_banana", place_target="024_bowl")
run_pick_place(bundle, task)
print("success:", check_success(bundle, task))
```

这个模式会执行真实任务，但不能替代讲义专用 trace、dataset 录制或评估证据。

