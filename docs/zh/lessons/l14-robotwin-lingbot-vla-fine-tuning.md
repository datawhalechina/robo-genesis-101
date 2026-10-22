---
lesson: L14
slug: robotwin-lingbot-vla-fine-tuning
locale: zh
title: "可选进阶实践：使用 RoboTwin 数据微调 LingBot-VLA-v2"
duration_minutes: 180
hardware: gpu-required
status: planned
---

# L14 · 可选进阶实践：使用 RoboTwin 数据微调 LingBot-VLA-v2

> **课程状态：** `planned`。本讲解释已经完成 review 的 L14 工作流，但双语 notebook、
> 课程侧辅助代码和必做四卡执行证据尚未交付。不要把下面的命令当作 RoboGenesis 已验证
> 的运行，也不要把引用的比赛测量写成课程实验结果。

## 本实践在课程中的位置

[L10](/zh/lessons/l10-dataset-anatomy-and-imitation-learning) 已经让 LeRobot feature、episode
metadata、归一化统计和动作块变得可检查。[L12](/zh/lessons/l12-act-and-smolvla-policy-training)
把动作专家和流匹配目标连接到训练与 checkpoint 证据。[L13](/zh/lessons/l13-closed-loop-evaluation-and-capstone)
则要求先冻结评估协议，再比较任务结果。

L14 把这些知识应用到固定版本
[`Robotwin-radeon-cloud`](https://github.com/ZiguanWang/Robotwin-radeon-cloud/tree/27b2f6fcb6c715e2cbb6db4431381f87c94b86ed)
companion 中已经走通的比赛参考路径：

```text
RoboTwin demo_clean 数据
        ↓
50 个 LeRobot v3 任务数据集 + LingBot 训练合同
        ↓
base model 闭环评估
        ↓
4-GPU 动作专家 LoRA → 分布式检查点（DCP）
        ↓
合并为可部署的 Hugging Face checkpoint
        ↓
合并后模型的配对评估 → 有边界的证据卡
```

同一本源 notebook 还覆盖 official RoboTwin post-training checkpoint、4/8-GPU 的 1000 回合
benchmark、合并后 LoRA benchmark，以及带 depth/video teacher 的全参数 SFT。这些章节都会
保留在本讲中，但它们是显式开启、成本较高的比赛扩展，不属于 180 分钟路线的必做要求。

![完整的 L14 比赛工作流在一张技术图中保留 base 与 official checkpoint、必做 LoRA 路径、可选 4/8-GPU benchmark 和全参数 SFT。蓝色通道是 180 分钟必做路线，紫色分支是保留的比赛扩展。](/diagrams/l14-competition-training-paths-zh.svg)

*课程原创示意图。源 notebook 的每条分支都保持可见；可选分支的存在不代表 RoboGenesis
已经执行过它。*

### 硬件与运行时边界

完整必做运行有严格的最低条件：

- 四张 AMD Radeon Pro W7900 48 GiB GPU；
- 固定版本的 companion container/runtime，以及已挂载的模型和数据；
- companion 定义的 Python 3.12、PyTorch 2.9.1 和 ROCm 7.2.1；
- EGL 渲染、MPLib 末端执行器规划，并关闭 CuRobo；
- `/workspace/runtime` 下可持久写入的存储；
- 不提供 CPU、单 GPU 或无云环境的完整完成 fallback。

在 ROCm build 中，PyTorch 仍使用设备字符串 `cuda`。这是 API 兼容名称；环境证据必须展示
HIP 和实际 AMD 设备。

八卡 profile 会保留，因为它属于比赛参考，但它不是课程最低合同。八卡结果不能替代必做四卡
路径的验证。

### 聚焦的 180 分钟路线

下面的时间只计算教学和审计，不包含 image 构建、第一次准备模型/数据、等待 server 启动以及
训练 wall time。

| 时间 | 主题 | 学习者产出 |
|---:|---|---|
| 0–10 分钟 | 课程定位、硬件门禁和证据边界 | 区分管线贯通与策略质量结论 |
| 10–30 分钟 | source、model、data、GPU、backend、port、storage 和 output preflight | 生成结构化 PASS/FAIL 身份报告 |
| 30–50 分钟 | RoboTwin → LeRobot v3 → LingBot 数据合同 | 审计一个任务数据集和 50 行 training manifest |
| 50–75 分钟 | Base server 与 10 回合评估协议 | 冻结 checkpoint、expert、seed、video 和分母语义 |
| 75–105 分钟 | 动作专家 LoRA、batch arithmetic 与 FSDP2 | 解释更新范围并审计四卡命令 |
| 105–130 分钟 | DCP 身份与 Hugging Face merge | 区分训练 checkpoint 与 serving artifact |
| 130–155 分钟 | 合并后模型评估与 resolved-seed 配对 | 构造 matched、base-only 和 merged-only seed 集合 |
| 155–175 分钟 | Wilson 区间、JSONL/video 对账和 evidence card | 写出范围恰当的 10+10 回合结论 |
| 175–180 分钟 | 总结与单变量扩展设计 | 注册一个不混入核心分母的后续实验 |

official checkpoint、完整 1000 回合 benchmark、八卡 profile、更长 LoRA 运行和 full SFT 仍会
在必做路线之后说明。它们可能需要数小时和大量持久存储。

## 学习目标

完成 L14 后，你应当能够：

1. 解释 RoboTwin demonstrations 如何成为 LingBot-VLA-v2 的训练输入；
2. 为 VLA 微调配置并比较动作专家 LoRA 与全参数 SFT；
3. 将分布式训练检查点转换为可部署的 Hugging Face 模型，并通过推理服务加载模型；
4. 在受控闭环评估下比较 base 与 fine-tuned policy，并报告范围恰当的结论。

## 证据层级与实验身份

L14 会跨越多个证据层级。不要把它们压缩成一句“训练成功了”。

| 证据 | 能证明什么 | 不能证明什么 |
|---|---|---|
| Source/data preflight | 声明的 revision 和必需输入存在 | policy 能完成任务 |
| 一次 optimizer update 或 100-step 运行 | data loading、forward/backward、更新和 DCP 保存可以执行 | 收敛或有用的微调质量 |
| DCP 审计与 merge | 训练 artifact 可使用声明的 base/config 完成转换 | 合并后 policy 表现更好 |
| Server health | 所选 checkpoint 能加载并响应 health endpoint | 动作语义正确或任务成功 |
| 闭环 `k/n` 与 episode rows | 一个冻结协议下观察到的结果 | 稳定 benchmark、未测任务或 sim-to-real 表现 |
| 1000 回合 benchmark | 一个声明 checkpoint/protocol 的广任务覆盖 | revision 改变或隐藏 retry policy 后仍然公平 |

因此，每次 run 都需要完整身份，而不是只有一个目录名。至少记录 companion 和 upstream
revisions、checkpoint path/revision、training config、task/config、CLI seed 与实际 resolved
seeds、GPU profile、backend flags、video 选择、output root，以及本次运行是 fresh start 还是
resume。

## Preflight：在消耗 GPU 之前失败

在 model serving、evaluation 或 training 之前只运行一次结构化 preflight。基础设施检查失败应
中止本次运行，而不是记成 policy episode failure。

### Source 与软件身份

本讲 review 的输入是 companion commit
`27b2f6fcb6c715e2cbb6db4431381f87c94b86ed`，其中固定了：

| 组件 | 已 review 的身份 |
|---|---|
| RoboTwin | `266f3aadf505a4f7fe9af0faa41a20f5f47cd123` |
| XPolicyLab | `c37109c500be67d0dea6b36bf7337bbd26e763cd` |
| LingBot-VLA-v2 source | `951475ae1b1d87553e7dc47c97b53a3d695c0d13` |
| LingBot-VLA-v2 6B base model | `11c703bf6a5c1f45b3b69168482da11fdbba53d7` |
| RoboTwin2.0 data | `a967b852afa21a9cbf19a198f7e653109042e87c` |
| LeRobot | `0.6.0` |

依赖能够解析并不等于 runtime 已验证。preflight 还必须展示 Python、PyTorch、
`torch.version.hip`、LeRobot、可见设备数量和名称、每张卡的显存身份、`/dev/kfd`、
`/dev/dri`、EGL，以及一个小型 ROCm tensor operation。

### 路径、存储、端口与 fresh outputs

companion 有意使用以下 container paths：

```text
/RoboTwin                  source, assets, converted data, experiment scripts
/models/robotwin-persistent mounted model and persistent input content
/workspace/runtime         logs, checkpoints, evaluations, videos, evidence
```

确认 port `13400` 空闲、`/workspace/runtime` 可写，并且新的 run names 不会与旧 artifact 冲突。
记录 `/`、`/workspace` 和 runtime output root 的剩余空间。L14 在四卡验证实际测量之前，不发布
RoboGenesis 最低存储数字。

教学 notebook 绝不能静默删除先前输出。保留的 full-SFT storage cell 只列出精确 cleanup
candidates 并执行 dry run；只有在最终 artifact 已复制到持久存储后，学习者才能显式决定是否
删除。

## RoboTwin 数据如何成为 LingBot 训练合同

companion image 下载固定版本、覆盖 50 个任务的 `demo_clean` 数据，再使用 XPolicyLab 的
LeRobot v3 converter 独立转换每个任务：

```text
data/demo_clean/<task>
        ↓ transform_lerobot_v30_format.py
data/lerobot/<task>_joint_v30
        ↓ one manifest entry per dataset
data/robotwin_demo_clean_joint_v30.txt
```

manifest 是一个包含 50 个数据集位置的列表，不是一个单独的数据集目录。
`adjust_bottle_joint_v30` 只是其中一项。在已 review 的 build 中，converter 将每个源任务限制
为最多 50 个 episodes，并写出 H.264 media，供 LeRobot-compatible reader backend 读取。

![50 个 RoboTwin demo_clean 任务目录被独立转换为 LeRobot v3 数据集。metadata、三路 camera stream、semantic joint groups、归一化统计和 50 行 manifest 共同定义 LingBot 训练输入，而不是某一个文件名或最大维度。](/diagrams/l14-robotwin-data-contract-zh.svg)

*课程原创示意图。审计跟随实际 metadata 和 config，不从数据集名称猜测 tensor shape。*

### 三路相机，两层命名接口

training YAML 声明三路逻辑 stream：

- `camera_top`；
- `camera_wrist_left`；
- `camera_wrist_right`。

RoboTwin evaluation patch 构造的直接 policy request 则使用：

- `head_camera` 对应 `observation.images.cam_high`；
- `left_camera` 对应 `observation.images.cam_left_wrist`；
- `right_camera` 对应 `observation.images.cam_right_wrist`。

这些名称属于不同接口。应审计 converter metadata 和 serving adapter，不能因为 camera label
相似就假定它们能够互换。

### Semantic groups 不是 storage shape 猜测

LingBot training YAML 声明：

```text
arm.position      14
end.position      14
effector.position  2
max_state_dim     55
max_action_dim    55
```

companion 中的一个 inference probe 使用 14-D state，而 converter 的 joint padding 取决于转换
配置。这些事实并不矛盾：semantic groups、stored feature shape 和 model capacity 属于不同层次。

notebook audit 必须分别报告：

1. `meta/info.json` 中实际 LeRobot feature shapes 与 dtypes；
2. `lingbotvla_cli.yaml` 中的 semantic group sizes；
3. converter 的 joint layout 与 padding target；
4. 作为 model capacity 的 `max_state_dim` 和 `max_action_dim`；
5. `robotwin.json` 是否为每个必需 group 提供了匹配的 normalization statistics。

## Base model 与 official RoboTwin checkpoint 的角色不同

companion 中有两个重要的 checkpoint 角色：

| Checkpoint | 在本讲中的角色 | 训练用途 |
|---|---|---|
| `robbyant/lingbot-vla-v2-6b` base | 部署与管线参考；LoRA/full SFT 的初始化 | 必需起点 |
| official RoboTwin post-training checkpoint | 可选的效果验证与 benchmark 参考 | 只用于 evaluation；比赛复现不能从它初始化 |

official RoboTwin checkpoint path 会继续保留在源 notebook 中，但公开课程必须在 notebook
实现前固定它的精确 artifact revision。这是 provenance 要求，不是删除已验证路径的理由。

### 一次只启动一个 server，并等待 health

companion 在 GPU 0 和 port 13400 启动所选模型：

```bash
bash /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/scripts/launch_official_server.sh \
  0 13400 /workspace/runtime/outputs/logs/base_server.log False \
  /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/models/robbyant_lingbot-vla-v2-6b
```

不能因为 process 已存在就开始 evaluation。轮询 `http://127.0.0.1:13400/healthz`；如果 process
退出则判定失败，并保留 server log。更换 checkpoint 或开始训练之前，停止 server process
group，并确认 GPU memory 和 port 已释放。

## 在运行前冻结闭环协议

必做的 base 与 merged evaluation 使用完全相同的协议：

| 字段 | 必需值或规则 |
|---|---|
| Task/config | `adjust_bottle` / `demo_clean` |
| Policy/protocol | `LingBot-VLA-v2` / `lingbot_vla_v2` |
| Episodes | base 10 回合 + merged 10 回合 |
| CLI seed | `0`，同时记录每个 episode 的实际 resolved seed |
| Expert | `expert_check=true`、`accept_expert_info_on_failure=true` |
| Backend | EGL、MPLib、`ROBOTWIN_DISABLE_CUROBO=1` |
| Evaluation | `eval_batch=false`，使用相同 timeout/control/success implementation |
| Video | 必做 10+10 evidence path 显式启用 |
| Outputs | base 与 merged 使用独立 fresh directory，不用成功 retry 替换失败记录 |

companion reference 默认关闭 video，以减少编码和磁盘 I/O。这个开关必须保持显式。单任务
evaluation 使用 `eval_video_log=true|false`；benchmark script 使用 `--video|--no-video`。
删除参数不等价，因为不同 entry point 的默认值不同。

一个有代表性的命令形状是：

```bash
ROBOTWIN_DISABLE_CUROBO=1 \
ROBOTWIN_EE_PLANNER=mplib \
PYOPENGL_PLATFORM=egl \
/opt/robotwin-env/bin/python /RoboTwin/scripts/eval_policy_xpolicylab.py \
  --task_name adjust_bottle \
  --task_config demo_clean \
  --policy_name LingBot-VLA-v2 \
  --protocol lingbot_vla_v2 \
  --host 127.0.0.1 \
  --port 13400 \
  --device_id 0 \
  --seed 0 \
  --test_num 10 \
  --expert_check true \
  --accept_expert_info_on_failure true \
  --eval_batch false \
  --additional_info eval_video_log=true
```

### Expert information 与分母

`expert_check=true` 要求环境在 policy rollout 之前准备 expert information。
`accept_expert_info_on_failure=true` 表示即使 expert plan/task check 失败也保留这些信息，而不是
静默过滤相应 seed。

episode 开始前发生基础设施失败应中止该 run。一次不稳定的 setup attempt 可能推进内部 seed，
必须记录为不计入分母的 attempt。一旦 policy episode 已开始，任务失败、timeout 或 evaluator/
policy exception 都按 evaluator 的 outcome semantics 处理，保留 termination reason，并继续
进入分母。

当前固定 companion 能可靠报告 aggregate `Final success rate: k/n`，但它的 single-task JSONL
在 policy rollout 之前写入，尚不包含每个 resolved seed 的 policy outcome。在 `M3.L14.4`
之前，companion 必须增加通过 review 的 per-attempt/episode JSONL。这个课程证据增强不否定
比赛 notebook 已经走通的路径。

## 可选的 100 tasks × 10 episodes benchmark

benchmark script 覆盖 50 个 clean tasks 和 50 个 randomized tasks，每个任务运行 10 回合。
选择四张或八张 GPU 后，它会在每张 GPU 上启动一个 model server 和一个 evaluation worker，
再从共享 queue 中领取下一个未完成任务。`--resume` 会跳过同一 run directory 中已有的 task
completion markers；独立 rerun 必须更换 `--run-name`。

固定 companion notebook 报告了以下 wall-clock 观测。这些数字是**上游比赛参考测量**，不是
RoboGenesis compatibility evidence；这里有意不列 success-rate 细节：

| 机器 | 配置 | 完成量 | 报告 wall time |
|---|---|---:|---:|
| 4 × W7900 | clean | 50 tasks / 500 episodes | 8 h 26 min 41 s |
| 4 × W7900 | randomized | 50 tasks / 500 episodes | 10 h 29 min 07 s |
| 4 × W7900 | total | 100 tasks / 1,000 episodes | 18 h 55 min 48 s |
| 8 × W7900 | clean | 50 tasks / 500 episodes | 6 h 34 min 23 s |
| 8 × W7900 | randomized | 50 tasks / 500 episodes | 8 h 37 min 58 s |
| 8 × W7900 | total | 100 tasks / 1,000 episodes | 15 h 12 min 21 s |

这些是端到端 task timing，不是线性 model-throughput benchmark。各任务时长不同，因此 queue
末尾由最慢的剩余任务决定。base model、official RoboTwin checkpoint、merged LoRA 和 full-SFT
model 必须使用不同 run identity。

## 在四张 GPU 上训练动作专家 LoRA

LoRA 把 frozen weight matrix 的可训练更新表示为低秩乘积：

```text
W' = W + (α / r) B A

A ∈ R^(r × d_in), B ∈ R^(d_out × r), r ≪ min(d_in, d_out)
```

必做配置使用 rank `r=8`、alpha `16`、scope `action_expert`，target modules 为
`q_proj,k_proj,v_proj,o_proj`。因此，训练更新的是动作专家中 attention projection 的低秩增量，
而不是把“LoRA”理解成更新模型的全部权重。

![Base vision-language model 保持为参考，rank-8 LoRA matrix 更新动作专家的 q、k、v、o projection。四个 W7900 worker 各处理 micro batch 1；FSDP2 shard size 4、accumulation 1 得到 global batch 4。可选八卡 profile 将 global batch 提升为 8。](/diagrams/l14-action-expert-lora-zh.svg)

*课程原创示意图。rank 和 batch 数字是配置，不是学习质量结论。*

### Batch arithmetic 必须闭合

```text
global batch
  = micro batch per GPU
  × data-parallel process count
  × gradient accumulation
```

| Profile | Micro batch | Processes/shard size | Accumulation | Global batch |
|---|---:|---:|---:|---:|
| 必做课程路径 | 1 | 4 | 1 | 4 |
| 可选比赛 profile | 1 | 8 | 1 | 8 |

YAML 中包含通用默认值，但 launcher 会覆盖 shard size、accumulation、global batch、steps、save
interval 和 output directory。应审计最终解析后的命令，而不只是 YAML 文件。

### 三种 attention setting 有不同 owner

| Setting | Owner 与作用 |
|---|---|
| `model.attn_implementation=flash_attention_2` | Hugging Face/Qwen model attention |
| `model.vit_attn_implementation=flash_attention_2` | vision encoder attention |
| `train.attention_implementation=flex_cached` | 使用自定义 2-D block mask 的 VLM/action-expert 联合 attention |

把第三项换成 `flash_attention_2` 不是优化；已 review 的路径会拒绝它，因为它不适用于该
custom mask。

### 必做四卡 smoke command

教学路径使用 companion 中固定的 Python interpreter，避免依赖 `PATH` 中身份不明确的
`torchrun`：

```bash
cd /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/source/lingbot-vla-v2

export HIP_VISIBLE_DEVICES=0,1,2,3
unset ROCR_VISIBLE_DEVICES CUDA_VISIBLE_DEVICES

/opt/robotwin-env/bin/python -m torch.distributed.run \
  --standalone \
  --nproc-per-node=4 \
  -m tasks.vla.train_lingbotvla \
  /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/training/lingbotvla_cli.yaml \
  --train.data_parallel_shard_size 4 \
  --train.gradient_accumulation_steps 1 \
  --train.global_batch_size 4 \
  --train.max_steps 100 \
  --train.save_steps 100 \
  --train.output_dir /workspace/runtime/outputs/lora_100steps_4gpu
```

课程运行还会在 resolved configuration 中冻结 training seed `42`。提交后的 notebook 会在执行
前展示这个身份。

100 steps 用来检验 data loading、distributed forward/backward、optimizer update、DCP 保存、
merge、load 和 evaluation plumbing。它不能证明 loss 收敛或 policy 改善。companion 建议把
1000–5000 steps 作为实验规模，但 checkpoint 选择仍需要 held-out closed-loop evidence，不能
自动选择训练时间最长的一次。

## DCP 是训练 artifact，Hugging Face 是 serving artifact

FSDP2 写出的 distributed checkpoint 会把 state 分片到不同 rank。它可能包含 sharded model
state、optimizer state、scheduler/RNG state、dataloader state 和 resolved training
configuration。不能像使用普通 Hugging Face model 一样，让 server 直接指向这个目录。

![四个训练 rank 写出 DCP shards 和 resolved training identity。LoRA 路径先验证 base model、rank、alpha 与 adapter state，再将其合并到新的 Hugging Face directory。config、processor、safetensor index、weight references 和 health check 共同构成 serving 门禁。](/diagrams/l14-dcp-to-hf-merge-zh.svg)

*课程原创示意图。Full SFT 使用 gather/convert，而不是图中的 LoRA adapter merge。*

对 LoRA 来说，转换身份是：

```text
global_step_100 DCP
  + exact base model
  + action-expert LoRA rank 8 / alpha 16
  + saved training config
  → fresh merged Hugging Face checkpoint
```

固定的 merge entry point 是：

```bash
/opt/robotwin-env/bin/python \
  /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/scripts/merge_lora_dcp.py \
  --checkpoint /workspace/runtime/outputs/lora_100steps_4gpu/checkpoints/global_step_100 \
  --training-output /workspace/runtime/outputs/lora_100steps_4gpu \
  --base-model /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/models/robbyant_lingbot-vla-v2-6b \
  --output /workspace/runtime/outputs/lora_100steps_4gpu/merged_checkpoint/global_step_100/hf_ckpt \
  --rank 8 \
  --alpha 16
```

serving 之前至少审计：

- DCP 与 saved training config 是否存在；
- 初始化时使用的精确 base checkpoint；
- LoRA scope、target modules、rank 和 alpha；
- fresh output directory；
- model config 与 processor assets；
- `model.safetensors.index.json` 及其引用的每个 shard；
- 启动 merged checkpoint 后的 health check。

## 按 resolved seed 比较 base 与 merged checkpoint

停止 training processes，在与 base checkpoint 相同的 GPU、port 和 flags 上启动 merged
checkpoint，然后再次运行 10 回合。checkpoint identity 是有意改变的变量；task、config、
evaluator、expert semantics、backend、video setting 和 output schema 保持不变。

evaluator 从 CLI `--seed 0` 派生的 seed 开始，但不稳定 setup 可能推进 seed。应使用实际 key
匹配 rows：

```text
(task_name, task_config, resolved_seed)
```

不能按 episode index 配对。

![Base 与 merged checkpoint 经过同一个冻结的 server/evaluation protocol。按 task、config 和实际 resolved seed join counted episode rows，得到 unchanged success、unchanged failure、failure-to-success、success-to-failure，以及 unmatched seed sets。](/diagrams/l14-matched-checkpoint-evaluation-zh.svg)

*课程原创示意图。缺失 seed 必须保持可见，不能拿无关 episode index 强行补齐。*

对于在 `n=10` 个 counted episodes 中观察到 `k` 次成功的 checkpoint，应报告 raw count 和
95% Wilson interval。再把 matched rows 分类为：

- `unchanged-success`；
- `unchanged-failure`；
- `failure-to-success`；
- `success-to-failure`。

如果 seed sets 不同，只比较 intersection，并分别报告 base-only 和 merged-only seeds；同时把
“完整 matched comparison”标记为不满足。不能用成功 retry 替换失败 row，也不能把一次新 run
混进旧分母。

evidence card 必须对账：

- base 与 merged 的 `k/n`；
- 两个 Wilson intervals；
- 所有 counted episode rows 和不计数的 setup attempts；
- matched outcome changes 与 unmatched seed sets；
- checkpoint 和 run identities；
- JSONL rows 与实际 video paths；
- limitations，包括 100-step training 与 10+10 小样本。

即使 merged count 更高，正确结论也只是对本次 run 的观察，而不是 100-step LoRA 已证明
RoboTwin policy 普遍更好。

## 全参数 SFT 是另一条训练路径

Full SFT 不从 LoRA adapter 继续训练。它设置 `use_lora=false`，更新所有 trainable model
parameters。保留的默认比赛路径还会启用 current/future depth 与 video-teacher supervision。

| 维度 | 动作专家 LoRA | 全参数 SFT |
|---|---|---|
| 更新权重 | 动作专家 `q/k/v/o` projection 上的 rank-8 update | 所有 trainable model parameters |
| 核心课程预算 | 4 GPU、global batch 4、100-step pipeline smoke | 可选；不是 180 分钟路线必做项 |
| 默认 teacher | 无 | 完整 depth/video teacher |
| Training checkpoint | DCP 加 LoRA adapter state/config | full-model 与 optimizer DCP |
| 部署转换 | 把 adapter merge 到精确 base | gather/convert 完整训练模型；没有 adapter merge |
| 存储/计算 | 较低 | 显著更高 |

完整 teacher 需要 LingBot depth asset、MoGe teacher asset，以及 DINO video checkpoint/config。
它会增加仅在训练中使用的 alignment heads。deployment patch 会过滤这些 training-only heads，
同时继续严格检查 inference weights。

### 四卡或八卡上的 global batch 256

保留的已验证 profile 使用 micro batch 16：

```text
4 GPU: 16 × 4 × 4 accumulation = 256
8 GPU: 16 × 8 × 2 accumulation = 256
```

`enable_full_shard=true` 映射到 FSDP2 `reshard_after_forward=true`。每个 wrapped module 会在
forward 后再次分片，从而降低 peak memory，但 backward 前需要再次 all-gather。`false` 会把
完整参数保留到 backward；这可能减少 communication，但通常需要更多 peak memory。它并不表示
关闭 FSDP2。

### Companion capacity measurement，不是课程验证

下表保留自固定比赛 notebook，因为它记录了已经测试的 capacity envelope。测量启用了完整
depth/video teachers、gradient checkpointing 和 FSDP2 full-shard。`steady` 是 optimizer steps
2 和 3 的平均值；VRAM 每秒采样一次。以下数字是**明确归属 companion 的测量**，不是
RoboGenesis run 的结果：

| 平台 | Micro batch/GPU | Accumulation | 报告 steady step | 报告 peak VRAM/GPU | 来源结果 |
|---|---:|---:|---:|---:|---|
| 4 × W7900 48 GiB | 1 | 64 | 245.580 s | 40.329–40.375 GiB | passed |
| 4 × W7900 48 GiB | 2 | 32 | 136.748 s | 41.337–41.349 GiB | passed |
| 4 × W7900 48 GiB | 4 | 16 | 76.010 s | 43.509–43.521 GiB | passed |
| 4 × W7900 48 GiB | 8 | 8 | 54.031 s | 47.729–47.761 GiB | passed; limited headroom |
| 4 × W7900 48 GiB | 16 | 4 | 41.392 s | 47.890–47.975 GiB | passed; nearly full |
| 4 × W7900 48 GiB | 32 | 2 | — | 47.648–47.956 GiB | HIP OOM |
| 8 × W7900 48 GiB | 1 | 32 | 143.665 s | 27.520–27.558 GiB | computed |
| 8 × W7900 48 GiB | 2 | 16 | 80.319 s | 27.818–27.832 GiB | passed |
| 8 × W7900 48 GiB | 4 | 8 | 47.055 s | 29.498–29.523 GiB | passed |
| 8 × W7900 48 GiB | 8 | 4 | 27.108 s | 33.004–33.386 GiB | passed |
| 8 × W7900 48 GiB | 16 | 2 | 24.682 s | 41.344–41.356 GiB | passed |
| 8 × W7900 48 GiB | 32 | 1 | — | 47.878–47.947 GiB | HIP OOM |

源 guide 还报告完整 AdamW DCP directory 约为 70-GB 级别。这是上游 storage observation，不是
课程最低值。model shards、一阶/二阶 optimizer moments、scheduler、RNG 和 dataloader state
都会占用空间。训练前检查实际剩余空间；删除任何 DCP 之前，先保留 final checkpoint、logs、
conversion 与 evaluation evidence。

### Convert，不要 merge adapter

Full SFT 没有 LoRA adapter。正确转换命令是：

```bash
/opt/robotwin-env/bin/python \
  /RoboTwin/experiments/lingbot_vla_v2_6b_robotwin/scripts/convert_full_sft_dcp.py \
  --checkpoint /workspace/runtime/outputs/full_sft_full_4gpu_10steps/checkpoints/global_step_10 \
  --training-output /workspace/runtime/outputs/full_sft_full_4gpu_10steps \
  --output /workspace/runtime/outputs/full_sft_full_4gpu_10steps/merged_checkpoint/global_step_10/hf_ckpt
```

转换后继续遵循源工作流：验证 weight index，在 port 13400 启动 converted model，运行一组独立
10 回合评估，并可选择在新的 run identity 下执行 4/8-GPU 1000 回合 benchmark。不能把这些
结果混入必做的 base-versus-LoRA 10+10 evidence。

## 按层诊断失败

| 症状 | 首先检查 | 暂时不要得出的结论 |
|---|---|---|
| Preflight 看到少于四张 GPU | visibility variables、device nodes、PyTorch/HIP identity | training code 已损坏 |
| EGL 或 MPLib setup 失败 | `/dev/dri`、EGL packages、planner flags、assets | policy 已经失败一个 episode |
| Data loader shape/stat error | actual metadata、joint groups、padding config、norm-stat keys | `max_action_dim=55` 就是 stored action shape |
| Server 一直不能 healthy | checkpoint index/shards、config/processor、log、port ownership、GPU memory | task behavior 很差 |
| DCP 存在但 merge 失败 | saved config、exact base identity、rank/alpha、fresh output | LoRA training 没有产生 update |
| Base `k/n` 较低 | video、action flow、expert/setup rows、task semantics | deployment 已损坏；base 只是 pipeline reference |
| Base/merged seeds 不同 | actual resolved seeds 与 setup skips | episode indices 可以直接配对 |
| Full SFT OOM | micro batch、accumulation、resharding、teacher mode、actual free VRAM | FSDP2 已关闭 |
| Disk pressure | exact output sizes 和 persistent/ephemeral mounts | 自动大范围删除是安全的 |

## 练习与检查

1. **数据合同审计。** 对 `adjust_bottle_joint_v30`，从 metadata 列出实际 image、state 与 action
   shapes。把它们放在 YAML joint groups 旁边，解释所有差异，不得用 `55` 猜测。
2. **Batch arithmetic。** 重新计算四卡和八卡 LoRA 的 accumulation，再计算 global batch 256、
   micro batch 16 时 full-SFT 的 accumulation。
3. **Checkpoint 身份。** 给定一个 DCP directory 和一个 Hugging Face directory，写出区分
   LoRA merge 与 full-SFT conversion 的最小检查集合。
4. **Matched outcomes。** 给定两个各含 10 rows、但有一个 setup seed 发生偏移的 episode files，
   计算 intersection、base-only/merged-only sets 和四类 matched outcome counts，并说明完整比较
   为什么不满足。
5. **单变量扩展。** 从 training length、GPU profile、checkpoint type 或 video setting 中选择一项，
   给它新的 run identity，并说明哪些核心字段必须保持不变。不要把它的 episodes 混入必做分母。

## 总结

L14 在完整保留比赛参考工作流的同时，为它增加了课程证据结构：

- 消耗 GPU 前审计 source、runtime、data、hardware 和 outputs；
- 联合检查实际 LeRobot metadata、LingBot semantic groups 和 normalization statistics；
- 把 base checkpoint 用作 deployment reference，把 official RoboTwin checkpoint 用作身份隔离的
  可选参考；
- 在必做四卡 profile 上训练 rank-8/alpha-16 动作专家 LoRA；
- 把 DCP 视为 distributed training state，并通过正确的 LoRA merge 生成 fresh、可部署的
  Hugging Face checkpoint；
- 在同一个、能够感知 resolved seed 的冻结闭环协议下比较 base 与 merged policy；
- 保留 4/8-GPU 完整 benchmark 和全参数 SFT，但不把未运行的可选章节冒充课程验证；
- 把 100 steps 与 10+10 回合的结论限制在这些观测真正能够支持的范围内。

## 来源与 provenance

本讲是对以下固定版本外部材料的课程原创改写。RoboGenesis 不复制或 rehost 它们的 container、
models、datasets、checkpoints、生成视频或完整 runtime tree。

- [`27b2f6f` 的 Robotwin-radeon-cloud companion](https://github.com/ZiguanWang/Robotwin-radeon-cloud/tree/27b2f6fcb6c715e2cbb6db4431381f87c94b86ed)，尤其是
  [`RoboTwin_ROCm_Reproduction.ipynb`](https://github.com/ZiguanWang/Robotwin-radeon-cloud/blob/27b2f6fcb6c715e2cbb6db4431381f87c94b86ed/RoboTwin_ROCm_Reproduction.ipynb)
  和
  [`Reproduce_Guide.md`](https://github.com/ZiguanWang/Robotwin-radeon-cloud/blob/27b2f6fcb6c715e2cbb6db4431381f87c94b86ed/Reproduce_Guide.md)。
- [`266f3aa` 的 RoboTwin](https://github.com/RoboTwin-Platform/RoboTwin/tree/266f3aadf505a4f7fe9af0faa41a20f5f47cd123)，MIT license。
- [`c37109c` 的 XPolicyLab](https://github.com/XPolicyLab/XPolicyLab/tree/c37109c500be67d0dea6b36bf7337bbd26e763cd)，Apache-2.0 license。
- [`951475a` 的 LingBot-VLA-v2](https://github.com/robbyant/lingbot-vla-v2/tree/951475ae1b1d87553e7dc47c97b53a3d695c0d13)，Apache-2.0 license。
- [`11c703b` 的 LingBot-VLA-v2 6B base model](https://huggingface.co/robbyant/lingbot-vla-v2-6b/tree/11c703bf6a5c1f45b3b69168482da11fdbba53d7)，其 model card 声明 Apache-2.0。
- [`a967b85` 的 RoboTwin2.0 data](https://huggingface.co/datasets/TianxingChen/RoboTwin2.0/tree/a967b852afa21a9cbf19a198f7e653109042e87c)，其 dataset card 声明 MIT。

本讲五张图均为课程原创 SVG。benchmark 与 full-SFT capacity 表是明确归属固定 companion
notebook 的参考观测，不是当前 RoboGenesis repository 产生的结果。
