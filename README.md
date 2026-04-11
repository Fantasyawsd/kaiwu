# Gorge Chase KaiWuDRL 项目

腾讯开悟（KaiWuDRL）"峡谷追猎 / Gorge Chase"强化学习代码包。训练智能体控制鲁班七号，在 128×128 栅格地图中躲避怪物、收集宝箱，尽量存活到最大步数（1000 步）。

---
## 开发前置动作

进入任何非微小算法开发前，必须先完成下面这组 Git 起手动作：

```bash

git pull

git status

git checkout -b feature/<topic>

```

如果分支已经存在，就切换到已有的 `feature/<topic>`。

只有在已经位于合适的 `feature/*` 分支后，才进入算法设计、算法实现、算法测试和归档流程；第一个 skill 必须是 `/kaiwu-dev-init`。

## 推荐 Repo-local Skills 工作流

如果你的 AI 工具支持读取仓库内 skills，推荐优先按下面顺序协作：

```text
/kaiwu-dev-init
-> /kaiwu-algo-compare        # 当需要比较外部调研算法 / reference_algos / 历史版本 / 用户方案时
-> /kaiwu-algo-design
-> /kaiwu-algo-implementation
-> 人执行真实训练与截图整理
-> /kaiwu-memory-archive
```

按需补充的辅助 skill：

- `/kaiwu-doc-query`：查询环境规则、数据协议、框架接口和 workflow 约束
- `/kaiwu-current-algo-analysis`：快速查看当前 baseline 快照、入口链路和已知限制
- `/kaiwu-algo-compare`：在进入设计前，把候选算法和当前 baseline 放到同一坐标系下比较，判断是否值得做

---
## 项目结构

```text
.
├── agent_ppo/              # 正式算法实现目录（所有算法迭代都在这里修改）
│   ├── agent.py            # Agent 主类：与环境交互、动作选择、模型推理
│   ├── algorithm/          # PPO loss 与优化逻辑：损失计算、梯度更新
│   ├── conf/               # 超参数与训练环境配置
│   ├── feature/            # 特征处理、样本定义、GAE 计算
│   ├── model/              # PyTorch Actor-Critic 模型定义
│   └── workflow/           # 训练工作流：数据收集、训练循环、模型保存
├── agent_diy/              # DIY 模板（仅作模板参考，不作为正式算法实现目录）
├── reference_algos/        # 外部参考算法源码（调研得到的第三方算法实现，供借鉴）
├── conf/                   # 平台与训练系统级配置
│   ├── app_conf_gorge_chase.toml   # 平台算法选择：当前启用哪个算法
│   ├── algo_conf_gorge_chase.toml  # 算法名到 Agent/workflow 类的映射
│   └── configure_app.toml          # 系统训练参数：batch size、buffer、同步频率
├── ckpt/                   # 模型 checkpoint 目录
├── 开发文档/               # 官方开发文档与 AI 查询索引
│   ├── README.md           # 文档查询入口（AI 优先读这里）
├── GLOBAL_DOCS/            # 全局稳定知识库
│   ├── 算法总表.md         # 已实现算法清单（AI 维护）
│   ├── 算法调研.md         # 外部调研候选方向（人维护）
│   └── 算法文档/           # 正式算法文档目录（每个算法为一个文件夹，内含 README.md 与 screenshots/；截图目录存放训练监控与官方评估结果）
├── DEV_MEMORY/             # 当前开发状态记忆（用于断线重连与快速接手）
│   └── NOW.md              # 当前要实现什么、做到哪一步、下一步做什么
├── .claude/skills/         # Repo-local Claude Code skills
├── .codex/skills/          # Repo-local Codex skills
├── .copilot/skills/        # Repo-local Copilot skills
├── KAIWU-WORKFLOW.md       # 工作流规范与 skills 使用顺序
├── CONTRIBUTE.md           # Git 协作与提交规范
├── 人类开发者AI协作指南.md   # 面向使用 AI 开发工具的人类开发者
├── kaiwu.json              # 项目标识（project_code: gorge_chase）
└── train_test.py           # 训练烟测入口：最小验证脚本
```

---

## 各目录/文件详细说明

### agent_ppo/ — 正式算法实现目录

> **注意**：`agent_ppo/` 是目录名（源于最初实现为 PPO），但**不限制必须使用 PPO 算法**。你可以在该目录下实现任何 RL 算法（DQN、SAC、A3C、PPO 等），只要保持接口兼容即可。

| 文件/目录 | 功能说明 |
|-----------|----------|
| `agent.py` | Agent 主类，封装与环境的交互接口。负责特征预处理、动作采样、模型推理调用。 |
| `algorithm/` | 算法核心实现，包含损失函数计算、梯度更新、学习率调度。可以是 PPO、DQN、SAC 等任意算法。 |
| `conf/` | 配置目录。`conf.py` 定义算法超参数；`train_env_conf.toml` 定义训练环境参数。 |
| `feature/` | 特征工程目录。`preprocessor.py` 处理观测到特征的转换，包含奖励计算；`definition.py` 定义样本结构、GAE 计算、回报计算。 |
| `model/` | 神经网络定义。`model.py` 定义网络结构（根据所用算法可以是 Actor-Critic、Q-Network 等）。 |
| `workflow/` | 训练流程编排。`train_workflow.py` 实现训练循环：数据收集、模型更新、checkpoint 保存、训练指标上报。 |

### conf/ — 平台级配置

| 文件 | 功能说明 |
|------|----------|
| `app_conf_gorge_chase.toml` | 平台算法选择配置。指定当前启用哪个算法（如 `algo = "ppo"`），决定系统加载哪个算法模块。 |
| `algo_conf_gorge_chase.toml` | 算法映射配置。定义算法名到具体 Python 类的映射（如 `ppo -> agent_ppo.agent.Agent`）。 |
| `configure_app.toml` | 系统训练参数。定义训练批次大小、经验回放缓冲区大小、模型同步频率、日志上报间隔等系统级参数。 |

### 记忆与文档体系

| 目录/文件 | 功能说明 |
|-----------|----------|
| `开发文档/` | 官方开发文档，包含环境规则说明、数据协议定义、框架接口文档。AI 查询环境相关问题优先查阅此处。 |
| `GLOBAL_DOCS/` | 全局稳定知识库。`算法总表.md` 记录所有已实现算法的状态和性能；`算法调研.md` 记录待调研的候选方向；`算法文档/` 为各算法的归档目录，每个算法使用单独文件夹存放 `README.md`，并在 `screenshots/` 中归档训练监控截图与官方评估结果截图。 |
| `DEV_MEMORY/NOW.md` | 当前开发状态记忆。记录本轮要实现的内容、当前进度、下一步计划。用于 AI 断线重连后快速恢复上下文。 |
| `reference_algos/` | 外部参考算法源码目录。存放调研得到的第三方算法完整实现（如 `hok_prelim/`），供设计/实现阶段参考借鉴。**不直接作为训练入口**。 |


### 其他关键文件

| 文件 | 功能说明 |
|------|----------|
| `KAIWU-WORKFLOW.md` | 工作流规范文档。定义标准开发流程、skills 调用顺序、文档同步规则、人与 AI 的协作边界。 |
| `CONTRIBUTE.md` | Git 协作规范。定义分支策略、提交规范、commit 格式要求、代码审查流程。 |
| `人类开发者AI协作指南.md` | 面向人类开发者的指南。说明如何使用 AI 工具进行算法开发、各阶段人与 AI 的分工、常见误区避免。 |
| `kaiwu.json` | 项目标识文件。包含 `project_code: gorge_chase`，用于平台识别项目类型。 |
| `train_test.py` | 最小验证脚本（smoke test）。执行一次简短训练，验证代码可运行、无语法错误、基本逻辑正确。正式训练前的必做检查。 |

---

## 代码入口链路

训练执行的完整调用链：

```text
train_test.py
    ↓
conf/app_conf_gorge_chase.toml          # 确定使用 algo = "ppo"
    ↓
conf/algo_conf_gorge_chase.toml         # 映射到 Agent 和 workflow 类
    ↓
agent_ppo/agent.py                      # Agent 初始化与环境交互
    ↓
agent_ppo/feature/preprocessor.py       # 特征预处理与奖励计算
    ↓
agent_ppo/feature/definition.py         # 样本构建与 GAE 计算
    ↓
agent_ppo/model/model.py                # 神经网络前向推理
    ↓
agent_ppo/algorithm/algorithm.py        # PPO 损失计算与参数更新
    ↓
agent_ppo/workflow/train_workflow.py    # 训练循环与模型保存
```

---

