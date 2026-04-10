---
name: kaiwu-algo-implementation
description: Execute a concrete algorithm implementation cycle for the Gorge Chase KaiWuDRL repository. The implementation must be grounded in source-code entry points, development docs, smoke-test validation, and NOW.md-to-algorithm-doc drafting.
argument-hint: [algorithm-goal-or-change]
allowed-tools: Bash(*), Read, Grep, Glob, Edit, Write
---

# KaiWu Algo Implementation

实现目标：$ARGUMENTS

## 目标

把一轮算法设计真正落地到源码中，并在实现结束时把 `DEV_MEMORY/NOW.md` 整理成“算法文档初稿”。

这里的“算法文档初稿”应当参考当前 PPO 正式文档结构，包含除训练信息以外的全部内容，为后续训练分析和信息归档做准备。

## 强制前置步骤

开始实现前，必须先执行 `/kaiwu-dev-init`。

只有在下面几点已经清楚时，才允许进入代码修改：

- 当前是在继续上一轮，还是开启新方向
- 当前 baseline 算法和正式算法文档是什么
- 当前 `NOW.md` 有无未完成任务
- 当前分支和工作区是否适合继续开发

如果这些信息不清楚，先回到 `/kaiwu-dev-init`，不要直接改代码。

## 实现前必须具备的前置知识

### 1. 开发文档理解

至少要知道：

- 环境配置来自 `agent_ppo/conf/train_env_conf.toml`
- 训练系统配置来自 `conf/configure_app.toml`
- 环境返回结构、动作空间、字段协议来自 `开发文档/开发指南/环境详述.md` 与 `开发文档/开发指南/数据协议.md`
- Agent / 特征 / 模型 / 算法 / workflow 的框架接口来自 `开发文档/腾讯开悟强化学习框架/智能体/*.md`

### 2. 项目源码入口理解

实现前必须能复述下面这条入口链：

```text
train_test.py
-> conf/app_conf_gorge_chase.toml
-> conf/algo_conf_gorge_chase.toml
-> agent_ppo/conf/conf.py
-> agent_ppo/conf/train_env_conf.toml
-> agent_ppo/agent.py
-> agent_ppo/feature/preprocessor.py
-> agent_ppo/feature/definition.py
-> agent_ppo/model/model.py
-> agent_ppo/algorithm/algorithm.py
-> agent_ppo/workflow/train_workflow.py
```

### 3. 改动定位知识

实现前先明确“想改什么应该改哪里”：

| 改动目标 | 主要文件 |
| --- | --- |
| 观测特征、合法动作、奖励 shaping | `agent_ppo/feature/preprocessor.py` |
| 样本结构、GAE、回报计算 | `agent_ppo/feature/definition.py` |
| 网络结构 | `agent_ppo/model/model.py` |
| PPO loss、优化逻辑 | `agent_ppo/algorithm/algorithm.py` |
| Agent 推理/训练接口 | `agent_ppo/agent.py` |
| 超参数 | `agent_ppo/conf/conf.py` |
| 训练环境配置 | `agent_ppo/conf/train_env_conf.toml` |
| 训练流程、终局奖励、监控上报 | `agent_ppo/workflow/train_workflow.py` |
| 系统训练配置 | `conf/configure_app.toml` |
| 切换算法 | `conf/app_conf_gorge_chase.toml` + `conf/algo_conf_gorge_chase.toml` |

## 执行步骤

### Step 1：确认本轮实现范围

先读：

- `GLOBAL_DOCS/算法总表.md`
- 对应正式算法文档
- `DEV_MEMORY/NOW.md`
- 必要的开发文档

确认本轮只验证一个主方向，不混入多个大改动。

### Step 2：补齐开发文档约束

如果改动涉及：

- 环境参数
- 动作空间
- observation / extra_info / EnvInfo 字段
- Agent / feature / model / algorithm / workflow 接口

就必须先读对应开发文档，再写代码。

### Step 3：按源码链路落地修改

改动前先明确将修改哪些文件以及理由，再实施。

默认约束：

- 正式算法实现只改 `agent_ppo/`
- `agent_diy/` 只作参考，不做正式落地
- 若修改特征维度、动作维度、样本结构，必须联动检查 `conf.py`、`preprocessor.py`、`definition.py`、`model.py`、`algorithm.py`、`agent.py`

### Step 4：做最小验证

实现完成后，至少执行一次 smoke test：

```bash
# 进入 Docker 容器执行烟测
docker exec -it kaiwu-dev-kaiwudrl-1 bash
python3 train_test.py
```

### Step 5：更新 NOW.md

实现阶段维护 `DEV_MEMORY/NOW.md`，记录：

- 本轮目标
- 已改动文件
- 已完成内容
- smoke test 结果
- 尚未做的训练事项

### Step 6：把 NOW.md 整理成算法文档初稿

这是算法实现的最后一步，必须执行。

要求：

- 把 `DEV_MEMORY/NOW.md` 从过程性记录，整理成“算法文档初稿”结构
- 内容参考 `GLOBAL_DOCS/算法文档/agent_ppo_20260409_1733.md`
- 只保留实现层面的稳定信息
- 先不要写真实训练结果、训练得分、训练结论
- 训练相关内容留给后续“训练分析”和“信息归档”阶段

可以选择两种做法：

1. 直接把 `NOW.md` 改写成算法文档初稿格式
2. 在 `GLOBAL_DOCS/算法文档/` 先生成初稿，同时在 `NOW.md` 保留简版指针和本轮状态

若未明确要求，优先采用第 1 种，即先把 `NOW.md` 整理成算法文档初稿。

## 算法文档初稿模板

```markdown
# <算法完整名> 算法文档初稿

**文档版本**：<算法完整名>
**记录日期**：<YYYY-MM-DD>
**当前状态**：已实现 / smoke test 已通过 / 暂无正式训练结果

---

## 1. 算法概述

- 任务目标：
- 算法框架：
- 本轮核心改动：
- 当前实现特点：

---

## 2. 代码入口链路

```text
train_test.py
-> conf/app_conf_gorge_chase.toml
-> conf/algo_conf_gorge_chase.toml
-> conf/configure_app.toml
-> agent_ppo/conf/conf.py
-> agent_ppo/conf/train_env_conf.toml
-> agent_ppo/agent.py
-> agent_ppo/feature/preprocessor.py
-> agent_ppo/feature/definition.py
-> agent_ppo/model/model.py
-> agent_ppo/algorithm/algorithm.py
-> agent_ppo/workflow/train_workflow.py
```

最小验证命令：

```bash
python3 train_test.py
```

---

## 3. Agent 接口

| 方法 | 说明 |
| --- | --- |
| `reset` | |
| `observation_process` | |
| `predict` | |
| `exploit` | |
| `learn` | |
| `save_model` | |
| `load_model` | |
| `action_process` | |

---

## 4. 特征处理

### 4.1 特征向量

| 分组 | 维度 | 内容 |
| --- | --- | --- |

### 4.2 合法动作处理

- 动作空间是否为 8 维或 16 维：
- legal action mask 如何处理：

### 4.3 奖励设计

| 分量 | 位置 | 说明 | 参数 |
| --- | --- | --- | --- |

### 4.4 终局奖励

- 位置：
- 逻辑：

---

## 5. 样本结构与 GAE

- `ObsData`：
- `ActData`：
- `SampleData`：
- GAE 公式：
- 关键参数：

---

## 6. 模型结构

- 编码器结构：
- backbone：
- actor head：
- critic head：
- 关键维度：

---

## 7. 算法训练逻辑

- loss 组成：
- PPO clip：
- value loss：
- entropy：
- 优化流程：
- early stop / KL 控制：

---

## 8. 超参数汇总

### 8.1 算法超参数

| 参数 | 值 | 说明 |
| --- | --- | --- |

### 8.2 环境配置

| 参数 | 值 | 说明 |
| --- | --- | --- |

### 8.3 系统训练配置

| 参数 | 值 | 说明 |
| --- | --- | --- |

---

## 9. 训练 Workflow

- `workflow` 主循环：
- episode 流程：
- 模型保存：
- 监控上报：

---

## 10. 已知限制

1. 
2. 
3. 

---

## 11. 待训练补充项

- 正式训练任务 ID：
- 正式训练得分：
- 关键监控结论：
- 是否进入归档：
```

## 规则

- 不在不理解源码入口的情况下直接改代码
- 不跳过开发文档约束
- 不把正式改动做进 `agent_diy/`
- 不编造训练结果
- 算法实现结束时必须完成“NOW -> 算法文档初稿”
