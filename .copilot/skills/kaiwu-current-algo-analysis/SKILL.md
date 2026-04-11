---
name: kaiwu-current-algo-analysis
description: Quickly analyze the current active algorithm in the Gorge Chase KaiWuDRL repository, focusing on algorithm design, hyperparameters, environment settings, and the current implementation snapshot.
argument-hint: [algorithm-name-or-scope]
allowed-tools: Read, Grep, Glob
---

# KaiWu Current Algo Analysis

分析目标：$ARGUMENTS

## 目标

这个 skill 的主要用途不是做深度源码审计，而是快速回答：

- 当前算法到底是什么
- 当前算法设计是什么样
- 关键超参数怎么配
- 环境设置怎么配
- 系统训练设置怎么配
- 当前实现处于什么状态

默认输出应当是一份“当前算法快照”，方便人快速接手、对齐 baseline、或决定下一步往哪里改。

## 默认分析策略

优先看“正式文档 + 配置文件”，只在必要时再下钻源码。

也就是说，默认先回答“当前怎么设计的、怎么配的”，再回答“代码具体落在哪”。

## 推荐读取顺序

### 第一层：快速快照必读

1. `GLOBAL_DOCS/算法总表.md`
2. 对应正式算法文档
3. `conf/app_conf_gorge_chase.toml`
4. `conf/algo_conf_gorge_chase.toml`
5. `agent_ppo/conf/conf.py`
6. `agent_ppo/conf/train_env_conf.toml`
7. `conf/configure_app.toml`

### 第二层：需要补充设计细节时再读

8. `train_test.py`
9. `agent_ppo/agent.py`
10. `agent_ppo/feature/preprocessor.py`
11. `agent_ppo/feature/definition.py`
12. `agent_ppo/model/model.py`
13. `agent_ppo/algorithm/algorithm.py`
14. `agent_ppo/workflow/train_workflow.py`

## 重点输出内容

默认必须优先输出下面这些内容：

### 1. 当前算法身份

- 当前启用的算法 key
- 当前正式算法完整名
- 当前状态：baseline / 已实现 / smoke test 通过 / 是否有正式训练结果

### 2. 当前算法设计

至少概括：

- 算法框架，例如 PPO / DQN / SAC / A3C / Actor-Critic
- 特征设计
- 动作空间设计
- 奖励设计
- 模型结构
- 训练主流程

### 3. 关键超参数

重点从 `agent_ppo/conf/conf.py` 提炼：

- 观测维度与动作维度
- RL 核心超参
- 奖励相关超参
- 编码器或网络结构相关超参

### 4. 环境设置

重点从 `agent_ppo/conf/train_env_conf.toml` 提炼：

- 地图配置
- 宝箱 / buff 配置
- 闪现冷却
- 第二只怪出现时间
- 怪物加速时间
- 最大步数

### 5. 系统训练设置

重点从 `conf/configure_app.toml` 提炼：

- replay buffer
- preload ratio
- sampler / remover / rate limiter
- train batch size
- dump model frequency
- model sync frequency
- preload model 相关配置

### 6. 当前实现状态与已知限制

例如：

- 当前是否只使用 8 维动作
- 当前是否还没接入闪现
- 当前是否只有 smoke test、没有正式训练得分
- 当前有哪些明确限制

## 若用户还想知道“该改哪里”

在快速快照之后，再补一个简版“改动定位”即可：

| 改动目标 | 主要文件 |
| --- | --- |
| 特征 / 合法动作 / 即时奖励 | `agent_ppo/feature/preprocessor.py` |
| 样本结构 / GAE | `agent_ppo/feature/definition.py` |
| 模型结构 | `agent_ppo/model/model.py` |
| 算法 loss / 优化 | `agent_ppo/algorithm/algorithm.py` |
| Agent 接口 | `agent_ppo/agent.py` |
| 超参数 | `agent_ppo/conf/conf.py` |
| 环境配置 | `agent_ppo/conf/train_env_conf.toml` |
| 系统训练配置 | `conf/configure_app.toml` |
| 训练 workflow | `agent_ppo/workflow/train_workflow.py` |

## 推荐输出模板

```markdown
## 当前算法快照

### 1. 当前算法
- 启用算法：
- 正式算法完整名：
- 当前状态：

### 2. 算法设计
- 算法框架：
- 特征设计：
- 动作空间：
- 奖励设计：
- 模型结构：
- 训练流程：

### 3. 关键超参数
| 参数 | 当前值 | 说明 |
| --- | --- | --- |

### 4. 环境设置
| 参数 | 当前值 | 说明 |
| --- | --- | --- |

### 5. 系统训练设置
| 参数 | 当前值 | 说明 |
| --- | --- | --- |

### 6. 已知限制
1.
2.
3.

### 7. 如需继续修改，优先看这些文件
- `...`
- `...`
```

## 规则

- 默认做快速分析，不默认展开全部源码细节
- 默认优先总结”设计、超参、环境、配置”
- 只有在文档或配置不够时，才继续下钻源码
- 若算法总表、正式算法文档、配置文件、源码不一致，必须明确指出
- 只读分析，不改代码

---

## 下一步行动（执行后必须输出）

根据分析结果，明确告诉用户：

```markdown
## 分析完成 - 建议下一步

| 场景 | 推荐行动 |
|------|---------|
| 当前算法设计完整但未实现 | 使用 `/kaiwu-algo-implementation` 开始实现 |
| 当前算法已实现但需优化 | 先修改代码，然后跑 `python train_test.py` 验证 |
| 需要修改超参数/环境配置 | 编辑对应配置文件，然后重新训练 |
| 训练已完成需要评估效果 | 人工查看官方训练监控，按 `算法完整名 + 训练步数` 上传模型做 5 次官方评估，并将训练截图与最终结果截图放入对应算法文档目录的 `screenshots/` |
| 发现算法设计有问题 | 更新 `DEV_MEMORY/NOW.md`，然后 `/kaiwu-algo-implementation` |
| 算法已稳定，准备归档 | 使用 `/kaiwu-memory-archive` 完成归档 |
```
