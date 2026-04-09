---
name: kaiwu-rl-current-algo
description: Inspect the active algorithm, workflow, and baseline configuration in a KaiWu / KaiWuDRL repository. Use when user says "当前用的是什么算法", "先看看 baseline", "检查当前配置", or before starting a new optimization round.
argument-hint: [repo-path-or-scope]
allowed-tools: Read, Grep, Glob
---

# KaiWu RL Current Algorithm Snapshot

检查：$ARGUMENTS

## 目标

只读解析当前 KaiWu / KaiWuDRL 仓库里的“算法入口 + 基线配置 + 最小验证方式”，输出一个可复用的 baseline 快照。不要改代码，不要提出新算法，只回答“当前是什么”。

## 何时使用

在以下场景优先触发本 skill：

- 用户问“当前跑的是哪个算法？”
- 用户想先确认 baseline，再决定是否优化
- 开始新一轮迭代前，需要核对当前入口、配置和最小验证命令
- 发现 `train_test.py`、`conf/*.toml` 可能不一致，需要做只读检查

## 读取顺序

1. 顶层说明：`README*`、`AGENTS.md`
2. 项目标识：`kaiwu.json`
3. 烟测入口：`train_test.py`
4. 算法选择：`conf/app_conf*.toml`
5. 算法映射：`conf/algo_conf*.toml`
6. 系统训练配置：`conf/configure_app.toml`
7. 对应算法的环境配置：`agent_*/conf/train_env_conf.toml`

如果仓库结构符合 Gorge Chase / 开悟比赛项目，再加载 `references/minimal-file-set.md`。

## 必须提取的信息

至少提取并汇总以下内容：

- 项目名 / `project_code`
- 当前最小验证入口与命令
- `train_test.py` 中的 `algorithm_name`
- `conf/app_conf*.toml` 中真正被平台使用的 `algo`
- `conf/algo_conf*.toml` 中该算法映射到的 Agent / workflow
- `conf/configure_app.toml` 中关键训练配置摘要
- 当前算法对应 `train_env_conf.toml` 中的环境配置摘要
- 基线最值得先读的代码入口

## 一致性检查

必须主动检查并明确指出：

1. `train_test.py` 中的 `algorithm_name` 是否与 `conf/app_conf*.toml` 的 `algo` 一致
2. `conf/algo_conf*.toml` 是否为该算法提供了合法映射
3. 当前算法对应的 `agent_*/conf/train_env_conf.toml` 是否存在
4. 当前仓库是否明确存在最小验证命令；若没有，必须如实说明

若发现不一致，不要替用户做选择，只输出“哪里不一致、会影响什么”。

## 输出格式

始终按下面结构输出：

### 1. 当前算法快照
- 项目：
- 烟测算法：
- 平台算法：
- Agent / workflow：

### 2. 最小验证方式
- 容器 / 环境入口：
- 最小命令：
- 额外前提：

### 3. 关键配置摘要
- 系统训练配置：
- 环境配置：
- `train_test.py` 临时覆盖项：

### 4. 最关键文件
- 文件路径 + 作用（3-6 条）

### 5. 风险或不一致
- 若无，明确写“未发现明显不一致”

## 规则

- 只做只读 inspection，不给优化建议
- 不把“当前 baseline 是什么”与“下一步该改什么”混在一起
- 优先引用真实文件路径与真实字段名
- 如果仓库缺少标准 KaiWu 入口，明确说明缺了什么，而不是猜测
- 如果当前仓库没有独立 `pytest` / `unittest` / `lint` 流程，也要如实写出
