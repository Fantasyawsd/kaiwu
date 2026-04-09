---
name: kaiwu-rl-run-experiment
description: Run smoke or full experiments for KaiWu / KaiWuDRL repositories using the project-specific entrypoints and configuration files, while reusing the general run-experiment workflow for long or remote jobs. Also link experiment execution back to the workflow's work progress document. Use when user says "跑开悟实验", "跑 train_test", "验证这个 KaiWu 改动", or after selecting an algorithm candidate.
argument-hint: [experiment-plan-or-command]
allowed-tools: Bash(*), Read, Grep, Glob, Skill, AskUserQuestion
---

# KaiWu RL Run Experiment

实验：$ARGUMENTS

## 目标

把一个已选定的 KaiWu / KaiWuDRL 算法改动或配置方案，转换成当前仓库可执行的实验步骤。这个 skill 专注“怎么跑”，不负责调研新算法，也不负责多轮停止决策。

本 skill 负责把实验执行阶段的状态回填到 workflow 使用的 `工作进度.md`。默认双文档联动：

- `工作进度.md`：记录状态、计划、阻塞、执行进度和下一步
- `实验记录.md`：记录实验细节、指标结果、日志位置和结论

## 何时使用

在以下场景触发本 skill：

- 用户说“跑一下开悟实验”
- 已经选定一个候选方案，需要做烟测或正式实验
- 需要确认当前仓库的实验入口、容器命令和配置文件
- `kaiwu-rl-iteration` 工作流进入实验阶段

## 决策树

### A. 最小烟测

如果目标是验证代码是否能跑通，优先执行当前仓库最小闭环：

```bash
python3 train_test.py
```

在 Gorge Chase 仓库中，先进入 Docker 容器：

```bash
docker exec -it kaiwu-dev-kaiwudrl-1 bash
```

然后在容器内进入代码目录，执行：

```bash
python3 train_test.py
```

## 前 Gorge Chase 仓库运行方法

如果当前仓库包含 `train_test.py`、`agent_ppo/`、`agent_diy/`、`conf/app_conf_gorge_chase.toml`，按以下规则处理。

### 1. 容器入口

```bash
docker exec -it kaiwu-dev-kaiwudrl-1 bash
```

### 2. 最小验证命令

```bash
python3 train_test.py
```

当前仓库没有独立的 `pytest` / `unittest` / `lint` 主流程；最可靠的最小验证入口是 `python3 train_test.py`。

### 3. 切换 smoke test 算法

修改 `train_test.py`：

```python
algorithm_name = "ppo"   # 或 "diy"
```

可选值来自：

```python
algorithm_name_list = ["ppo", "diy"]
```

### 4. 检查平台算法入口

如果本轮改动不仅是 smoke test，还会影响平台实际加载的算法，检查：

- `conf/app_conf_gorge_chase.toml`
- `conf/algo_conf_gorge_chase.toml`

### 5. 检查训练配置

如果本轮改动涉及 batch、replay buffer、模型保存、preload，检查：

- `conf/configure_app.toml`

如果本轮改动涉及地图、最大步数、怪物、buff 等环境配置，检查：

- `agent_ppo/conf/train_env_conf.toml`
- `agent_diy/conf/train_env_conf.toml`

### 6. 记录输出指标

实验结束后至少记录：

- `reward`
- `total_loss`
- `policy_loss`
- `value_loss`
- `entropy_loss`
- `sim_score` / `total_score`
- `total_reward`
- `episode_steps`
- `result`

必要时加载 `references/gorge-chase-runbook.md`。

## 运行前检查

跑实验前必须确认：

1. 当前 Git 状态是否已记录
2. 当前算法与本轮候选是否一致
3. 是否先跑 smoke test，再跑长实验
4. 是否有 baseline 对照
5. 是否有日志/结果保存位置
6. 是否已有 work item / 轮次 ID
7. `工作进度.md` 的位置是否明确

若缺少 baseline、日志保存方式或进度文档入口，先提示并补齐，不要盲目启动长实验。

## 执行阶段与进度文档联动

本 skill 不负责整个工作流，但要负责实验阶段的状态回填。默认要求：

- 开始 smoke test 前，把当前状态更新为 `RUNNING_SMOKE`
- 开始长实验前，把当前状态更新为 `RUNNING_FORMAL`
- 若被环境或命令阻塞，更新为 `BLOCKED`
- 实验结束等待结论时，更新为 `REVIEW`

回填到 `工作进度.md` 的信息至少包括：
- work item / 轮次 ID
- 当前状态
- 本阶段命令
- 日志位置
- 结果文件位置
- 是否通过
- 下一步交给谁（如 `/monitor-experiment` 或 `/analyze-results`）

`实验记录.md` 则继续记录实验细节与指标结果。

## 输出格式

### 1. 实验类型
- smoke test / long run / remote run：

### 2. 运行命令
- 容器命令：
- 实际命令：

### 3. 配置与版本
- Git 分支 / commit：
- 算法：
- 关键配置：

### 4. 进度与记录位置
- 工作进度文档：
- work item / 轮次 ID：
- 本阶段状态更新：
- 日志：
- 实验记录：
- 结果文件：

### 5. 下一步
- 若已启动：调用 `/monitor-experiment`
- 若已完成：调用 `/analyze-results`

## 规则

- 不做算法调研
- 不做多轮迭代停止判断
- 先烟测，再长实验
- 长实验优先复用 `/run-experiment`
- 结果分析优先交给 `/analyze-results`
- 监控运行中任务优先交给 `/monitor-experiment`
- 只要进入实验阶段，就必须同步更新 `工作进度.md`
