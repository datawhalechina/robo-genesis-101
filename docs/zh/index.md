---
layout: home
title: RoboGenesis 101

hero:
  name: RoboGenesis 101
  text: 基于 Genesis 的机器人学习实践
  tagline: 面向具备 Python 基础的学习者，贯通仿真、控制、数据、策略训练与闭环评估
  actions:
    - theme: brand
      text: 从 L01 开始
      link: /zh/lessons/l01-introduction-and-environment-diagnostics
    - theme: alt
      text: English
      link: /en/

features:
  - title: Genesis 基础
    details: 学习环境诊断、场景、刚体物理、机器人控制、逆运动学、相机与并行仿真。
  - title: 从控制到抓取
    details: 搭建抓取场景，理解脚本化专家和演示数据获取。
  - title: 从数据到策略
    details: 依次学习数据录制、模仿学习、域随机化、策略训练与闭环评估。
---

## 课程状态

> 当前 14 讲包含 8 个 `cpu-verified` 和 6 个 `gpu-verified`，0 个 `planned`、0 个
> `published`。全部讲次均已达到各自验证状态。`rg101-fruit-pick@1.0.0` 数据集和
> `rg101-fruit-pick-smolvla@1.0.0` checkpoint 已冻结正式 release 身份、版本、许可与逐文件 checksum
> manifest，并提供标准下载/校验流程及双语本地消费路径。全新环境下载、文档构建、CPU smoke
> 与消费者验证已经完成。两者现为 `release`，ACT artifact 仍为 `unavailable`。参考 AMD GPU
> release acceptance 和最终 V1 发布就绪
> 审计已经完成。数据集 `eab6739...` 和 SmolVLA `6649cc3...` 两个固定 revisions
> 均已包含 README/card、许可声明（dataset 为 CC BY-NC 4.0，checkpoint 为 Apache-2.0）、
> 上游/第三方署名和使用边界；9 个 dataset 文件和
> 7 个 checkpoint 文件与课程逐文件 checksum 一致。项目负责人已授权两项 artifact 状态
> 提升为 `release`；lesson `published` 状态仍保持不变，因为它需要单独 review。
> L01–L07 已通过各自的 CPU clean-kernel 验证，状态均为
> `cpu-verified`；这些讲次的
> 附加 AMD 路径也已在参考 R9700 环境按各自合同通过。L08 已通过双语 CPU 数值路径、
> CPU+EGL 和参考 R9700 AMD+EGL 的脚本化专家验证；L09 已通过双语 CPU 诊断、CPU+EGL
> 和参考 R9700 AMD+EGL 的双相机录制与回读验证，两讲均为 `gpu-verified`。重编号后的
> L12 训练内容也已通过 ACT、SmolVLA GPU smoke、checkpoint 审计和重载验证，状态为
> `gpu-verified`。L10 已通过双语 CPU-only 数据读取与检查路径，状态为 `cpu-verified`。
> L11 已通过双语诊断、CPU+EGL 和参考 R9700 AMD+EGL 的 bounded DR 录制、回读与
> provenance 验证，状态为 `gpu-verified`。L13 已通过双语诊断、参考 R9700 AMD+EGL 单
> checkpoint 闭环评估、matched reference/shifted rollout、H.264 视频与报告证据审计，状态为
> `gpu-verified`；这不表示已经证明稳定成功率、OOD 鲁棒性或 sim-to-real。L14 是不影响核心
> 13 讲完成路径的可选进阶实践，已在固定 companion runtime 和 4× W7900D 上完成 base
> `0/10`、100-step LoRA、DCP→HF merge、merged `0/10` 及 20 个视频的必做路径验证，状态为
> `gpu-verified`。两组结果是独立 aggregate 小样本，不能证明策略提升；resolved-seed matching、
> 8 卡、1000 回合 benchmark 和 full SFT 尚未验证。

| 讲次 | 主题 | 预计时长 | 硬件 | 状态 |
|---|---|---:|---|---|
| L01 | [导论、运行平台与环境诊断](/zh/lessons/l01-introduction-and-environment-diagnostics) | 30 分钟 | `cpu-ok` | `cpu-verified` |
| L02 | [场景、实体与仿真生命周期](/zh/lessons/l02-scenes-entities-and-simulation-lifecycle) | 90 分钟 | `cpu-ok` | `cpu-verified` |
| L03 | [刚体物理与稳定仿真](/zh/lessons/l03-rigid-body-physics-and-stable-simulation) | 90 分钟 | `cpu-ok` | `cpu-verified` |
| L04 | [机器人模型、DOF 与关节控制](/zh/lessons/l04-robot-models-dofs-and-joint-control) | 90 分钟 | `cpu-ok` | `cpu-verified` |
| L05 | [逆运动学、末端位姿与相机](/zh/lessons/l05-inverse-kinematics-end-effector-poses-and-cameras) | 120 分钟 | `cpu-ok` | `cpu-verified` |
| L06 | [并行仿真与批量 Franka 控制](/zh/lessons/l06-parallel-simulation-and-batched-franka-control) | 90 分钟 | `cpu-ok` | `cpu-verified` |
| L07 | [抓取任务场景搭建](/zh/lessons/l07-building-a-grasping-task-scene) | 90 分钟 | `cpu-ok` | `cpu-verified` |
| L08 | [演示数据获取与脚本化专家](/zh/lessons/l08-demonstration-acquisition-and-scripted-experts) | 120 分钟 | `gpu-recommended` | `gpu-verified` |
| L09 | [合成数据录制与采数吞吐](/zh/lessons/l09-synthetic-data-recording-and-throughput) | 120 分钟 | `gpu-recommended` | `gpu-verified` |
| L10 | [数据集解剖与模仿学习 101](/zh/lessons/l10-dataset-anatomy-and-imitation-learning) | 90 分钟 | `gpu-recommended` | `cpu-verified` |
| L11 | [域随机化](/zh/lessons/l11-domain-randomization) | 90 分钟 | `gpu-recommended` | `gpu-verified` |
| L12 | [ACT 与 SmolVLA 策略训练](/zh/lessons/l12-act-and-smolvla-policy-training) | 150 分钟 | `gpu-required` | `gpu-verified` |
| L13 | [闭环评估与 Capstone](/zh/lessons/l13-closed-loop-evaluation-and-capstone) | 120 分钟 | `gpu-required` | `gpu-verified` |
| L14 | [可选进阶实践：使用 RoboTwin 数据微调 LingBot-VLA-v2](/zh/lessons/l14-robotwin-lingbot-vla-fine-tuning) | 180 分钟 | `gpu-required` | `gpu-verified` |

## GPU 算力资源

本课程建议学习者全程使用合适的 GPU；策略训练和闭环评估尤其依赖 GPU。课程中记录的
GPU 验证均在 AMD Radeon 硬件上，使用已记录的 ROCm profiles 完成。

如果没有可用的本地 GPU，可以[注册成为 AMD 开发者](https://developer.amd.com.cn/login?source=eHjyREaw5)，
查看 AMD 开发者计划当前提供的免费算力资源。资源可用性、额度、开放地区和具体硬件配置由
AMD 平台管理，可能随时间调整。

## 辅助材料

- [环境配置与 fallback 路径](/zh/appendix/setup-and-fallbacks)
- [课程术语表](/zh/appendix/glossary)
- [API 与命令速查表](/zh/appendix/api-cheatsheet)
- [教师指南](/zh/appendix/instructor-guide)
- [引用与第三方许可审计](/zh/references/)
