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

这里的“算法文档初稿”应当参考当前正式算法文档结构，包含除训练信息以外的全部内容，并为后续人工补充训练/测试 HTML 文档预留目录。

> **重要**：`agent_ppo/` 只是目录名（源于最初实现为 PPO），不代表必须保持 PPO 结构。你可以在该目录下实现任何算法（DQN、SAC、A3C 等），只要接口兼容即可。

## 强制前置步骤

- 根据用户指令，判断实现**用户指定算法**/**继续完成NOW.md**

- 当前 baseline 算法和正式算法文档是什么

如果这些信息不清楚，先回到 `/kaiwu-dev-init`，不要直接改代码。

**查看当前所处分支，是否为该算法实现对应分支，若否，则根据当前实现的算法创建新分支**

- `git branch`
- `git checkout -b feature/*`

## 实现前必须具备的前置知识

### 1. 开发文档与外部参考理解

至少要知道：

- 环境配置来自 `agent_ppo/conf/train_env_conf.toml`
- 训练系统配置来自 `conf/configure_app.toml`
- 环境返回结构、动作空间、字段协议来自 `开发文档/开发指南/环境详述.md` 与 `开发文档/开发指南/数据协议.md`
- Agent / 特征 / 模型 / 算法 / workflow 的框架接口来自 `开发文档/腾讯开悟强化学习框架/智能体/*.md`

**若涉及外部参考算法**：

- 查阅 `reference_algos/<算法名>/README.md` 了解整体结构
- 查阅 `reference_algos/<算法名>/code/` 下的具体实现：
  - 特征处理代码（如 `feature/state_manager.py`）
  - 模型结构代码（如 `model/model.py`）
  - 奖励计算逻辑
- **明确区分**：哪些代码可以直接迁移、哪些需要适配修改、哪些不能照搬
- 在实现注释中标注灵感来源（如 `# 思路来自 reference_algos/hok_prelim/...`）

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
| 算法 loss、优化逻辑 | `agent_ppo/algorithm/algorithm.py` |
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

### Step 4：做最小验证（必须在 Docker 中执行）

> **⚠️ 重要：测试必须在 Docker 容器内执行，本地环境缺少依赖，直接运行会失败**

实现完成后，至少执行一次 smoke test：

```bash
# 1. 进入 Docker 容器（必须在容器内执行测试）
docker exec -it kaiwu-dev-kaiwudrl-1 bash

# 2. 在容器内执行烟测
cd /data/projects/gorge_chase
git status  # 确认代码已同步进容器
python3 train_test.py
```

**注意**：`kaiwu-dev-kaiwudrl-1` 是容器名，若不同请用 `docker ps` 查看实际容器名。

### Step 5：更新 NOW.md

实现阶段维护 `DEV_MEMORY/NOW.md`，记录：

- 本轮目标
- 已改动文件
- 已完成内容
- smoke test 结果
- 尚未做的训练事项

### Step 6：创建算法文档目录并生成初稿

这是算法实现的最后一步，必须执行。

#### 步骤 6.1：预创建算法文档目录

提前创建训练结果存放目录，方便后续人工放入 HTML 文档：

- 训练全部曲线 HTML 文档和测试 HTML 文档都统一放入 `html/`
- HTML 文档文件名（去掉扩展名）默认视作上传到官网的模型全称

```bash
mkdir -p GLOBAL_DOCS/算法文档/<算法完整名>/html
```

#### 步骤 6.2：生成算法文档初稿

在 `GLOBAL_DOCS/算法文档/<算法完整名>/README.md` 生成初稿：

- 内容参考 `GLOBAL_DOCS/算法文档/agent_ppo_20260409_1733/README.md`
- 把 `DEV_MEMORY/NOW.md` 从过程性记录整理成正式结构
- 只保留实现层面的稳定信息（特征、模型、奖励、超参数等）
- 明确标注「待训练补充项」
- **不编造训练结果、训练得分、训练结论**
- 训练相关内容留给后续“人工训练结果整理、官网评估”和“信息归档”阶段

#### 步骤 6.3：同步更新 NOW.md

在 `NOW.md` 中：
- 保留简版实现记录和本轮状态
- 添加指针：`算法文档初稿位置：GLOBAL_DOCS/算法文档/<算法完整名>/README.md`
- 添加指针：`HTML 文档目录：GLOBAL_DOCS/算法文档/<算法完整名>/html/`

#### 算法文档目录结构

```
GLOBAL_DOCS/算法文档/<算法完整名>/
├── README.md          # 算法文档初稿（训练结果部分留空/标注待补充）
└── html/       # 训练完成后人工放入训练/测试 HTML 文档；
                       # HTML 文档文件名（去掉扩展名）默认视作官网模型全称
```

## 算法文档初稿模板

生成到 `GLOBAL_DOCS/算法文档/<算法完整名>/README.md`：

```markdown
# <算法完整名> 算法文档

**文档版本**：<算法完整名>
**记录日期**：<YYYY-MM-DD>
**当前状态**：已实现；smoke test 通过；暂无正式训练得分
**HTML 文档目录**：`GLOBAL_DOCS/算法文档/<算法完整名>/html/`（训练完成后人工放入）

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

最小验证命令（⚠️ 必须在 Docker 容器内执行）：

```bash
# 进入容器
docker exec -it kaiwu-dev-kaiwudrl-1 bash

# 在容器内执行测试
cd /data/projects/gorge_chase
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
- 策略 loss（如 PPO clip、DQN Q-loss 等）：
- value loss：
- 探索项（如 entropy、epsilon-greedy 等）：
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
- `html/` 中的 HTML 文档文件名：
- 由 HTML 文档文件名得到的官网模型全称：
- 5 次官方评估 / 10 张开放地图结果（如有）：
- 测试 HTML 文档：
- 是否进入归档：
```

## 规则

- 不在不理解源码入口的情况下直接改代码
- 不跳过开发文档约束
- 不把正式改动做进 `agent_diy/`
- 不编造训练结果
- 算法实现结束时必须完成”NOW -> 算法文档初稿”

---

## 下一步行动（执行后必须输出）

根据实现完成度，明确告诉用户：

### 场景 1：Smoke test 失败
```
下一步：修复代码错误
- 根据报错信息修改对应文件
- 重新进入 Docker 容器执行测试：
  docker exec -it kaiwu-dev-kaiwudrl-1 bash
  cd /data/projects/gorge_chase
  python3 train_test.py
- 直到 smoke test 通过
```

### 场景 2：Smoke test 通过，算法文档初稿已完成
```
下一步：提交代码并准备训练
1. 确认目录结构已创建：
   GLOBAL_DOCS/算法文档/<算法完整名>/
   ├── README.md          # 算法文档初稿
   └── html/       # 空目录，用于存放训练 HTML 文档

2. 提交代码：
   git add -A
   git commit -m “feat(<scope>): <算法完整名>”
   git push -u origin feature/<分支名>

   示例 commit message：
   ─────────────────────────────────────────
   feat(ppo): agent_ppo_20260410_hok_memory_map_v1

   - 实现内容：接入 HOK 风格记忆地图、16 维动作空间、分层奖励
   - 关键设计：CNN 地图编码、目标记忆器、闪现脱险奖励
   - 涉及文件：agent_ppo/conf/conf.py, agent_ppo/feature/preprocessor.py, agent_ppo/model/model.py
   - 烟测状态：通过
   - 训练状态：暂无正式训练得分
   - 算法文档：GLOBAL_DOCS/算法文档/agent_ppo_20260410_hok_memory_map_v1/README.md
   ─────────────────────────────────────────

3. 在平台上启动正式训练

4. 训练完成后人工操作：
   - 查看官方训练监控并导出 HTML 文档 → 放入 html/
   - 对开放 10 图做 5 次官方评估，并将测试 HTML 文档 → 放入 html/
   - HTML 文档文件名（去掉扩展名）视作上传到官网的模型全称
   - AI 后续只检测 html/ 中是否有 HTML 文档，不校验 HTML 文档真伪
   - 如需补充结构化结果，再在 README.md 中补充训练得分或评估摘要

5. HTML 文档和结果整理完毕后，执行 /kaiwu-memory-archive 完成归档
```

### 场景 3：算法文档初稿尚未完成
```
下一步：完成算法文档
- 继续完善 `DEV_MEMORY/NOW.md`
- 将其整理为算法文档初稿格式
- 完成后即可进入训练阶段
```
