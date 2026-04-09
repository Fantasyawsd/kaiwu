---
name: kaiwu-current-algo-analysis
description: Analyze the current algorithm implementation in the Gorge Chase KaiWuDRL repository. Read the algorithm table, trace the code entry chain, and output a structured snapshot of the active algorithm.
argument-hint: [algorithm-name-or-scope]
allowed-tools: Read, Grep, Glob
---

# KaiWu Current Algo Analysis

分析目标：$ARGUMENTS

## 目标

只读分析当前 KaiWu 仓库中的算法实现，输出可复用的算法快照，不改代码。

## 推荐读取顺序

1. `GLOBAL_DOCS/算法总表.md`
2. 对应正式算法文档
3. `train_test.py`
4. `conf/app_conf_gorge_chase.toml`
5. `conf/algo_conf_gorge_chase.toml`
6. `agent_ppo/conf/conf.py`
7. `agent_ppo/conf/train_env_conf.toml`
8. `agent_ppo/agent.py`
9. `agent_ppo/feature/preprocessor.py`
10. `agent_ppo/feature/definition.py`
11. `agent_ppo/model/model.py`
12. `agent_ppo/algorithm/algorithm.py`
13. `agent_ppo/workflow/train_workflow.py`

## 必须输出的信息

- 算法名与当前实现状态
- 代码入口链路
- Agent 核心接口
- 特征维度与结构
- 奖励设计
- 模型结构
- PPO loss 组成
- 关键超参数
- workflow 主循环
- 已知限制
- 修改定位指南

## 规则

- 只做只读分析。
- 若算法总表与代码不一致，必须指出。
