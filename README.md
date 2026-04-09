# Gorge Chase KaiWuDRL 项目

腾讯开悟（KaiWuDRL）"峡谷追猎 / Gorge Chase"强化学习代码包。训练智能体控制鲁班七号，在 128×128 栅格地图中躲避怪物、收集宝箱，尽量存活到最大步数（1000 步）。

---

## 1. 项目结构

```text
.
├── agent_ppo/              # 正式算法实现目录（所有算法迭代都在这里修改）
│   ├── agent.py            # Agent 主类
│   ├── algorithm/          # PPO loss 与优化逻辑
│   ├── conf/               # 超参数与训练环境配置
│   ├── feature/            # 特征处理、样本定义、GAE 计算
│   ├── model/              # PyTorch Actor-Critic 模型
│   └── workflow/           # 训练工作流
├── agent_diy/              # DIY 模板（仅作模板参考，不作为正式算法实现目录）
├── conf/                   # 平台与训练系统级配置
│   ├── app_conf_gorge_chase.toml   # 平台算法选择
│   ├── algo_conf_gorge_chase.toml  # 算法名到 Agent/workflow 映射
│   └── configure_app.toml          # 系统训练参数
├── ckpt/                   # 模型 checkpoint 目录
├── 开发文档/               # 官方开发文档与 AI 查询索引
│   ├── README.md           # 文档查询入口（AI 优先读这里）
│   └── EXPERIENCE.md       # 开发文档查询经验
├── GLOBAL_DOCS/            # 全局稳定知识库
│   ├── 算法总表.md         # 已实现算法清单（AI 维护）
│   ├── 算法调研.md         # 外部调研候选方向（人维护）
│   ├── 算法文档/           # 正式算法文档（算法名_时间.md 命名）
│   ├── CHANGELOG.md        # 全局变更记录
│   ├── TODO.md             # 全局待办
│   └── EXPERIENCE.md       # 全局经验库
├── DEV_MEMORY/             # 当前开发状态记忆（用于断线重连与快速接手）
│   ├── 算法文档.md         # 当前算法状态快照
│   ├── TODO.md             # 当前轮次待办与下一步
│   ├── CHANGELOG.md        # 当前轮次变更轨迹
│   └── EXPERIENCE.md       # 当前轮次问题、经验与风险
├── .claude/skills/         # Repo-local Claude Code skills
├── .codex/skills/          # Repo-local Codex skills
├── .copilot/skills/        # Repo-local Copilot skills
├── KAIWU-WORKFLOW.md       # 工作流规范与 skills 使用顺序
├── CONTRIBUTE.md           # Git 协作与提交规范
├── 人类开发者AI协作指南.md   # 面向使用 AI 开发工具的人类开发者
├── kaiwu.json              # 项目标识（project_code: gorge_chase）
└── train_test.py           # 训练烟测入口
```

> 人类开发者如果使用 Codex、Claude Code 等 AI 工具协作开发，建议先阅读 [人类开发者AI协作指南.md](人类开发者AI协作指南.md)。

---

## 2. 快速开始

### 2.1 最小验证入口

在 Docker 容器内执行：

```bash
docker exec -it kaiwu-dev-kaiwudrl-1 bash
python3 train_test.py
```

`train_test.py` 会执行一次最小训练闭环（smoke test），用于在正式训练前验证代码可运行。

### 2.2 切换烟测算法

修改 `train_test.py`：

```python
algorithm_name = "ppo"   # 或 "diy"
```

### 2.3 当前基线的定义


当前基线请查阅 [GLOBAL_DOCS/算法总表.md](GLOBAL_DOCS/算法总表.md)。

- 当前基线、训练得分、实现状态等动态信息，以 `GLOBAL_DOCS/算法总表.md` 为准。
- 当前算法的实现细节、超参数、已知限制等动态信息，以算法总表中对应条目所链接的正式算法文档为准。
- README 只保留项目入口和开发导航，不负责维护会随算法迭代变化的细节。
- 当前正式算法实现源码目录固定为 `agent_ppo/`；`agent_diy/` 只作为模板，不作为正式算法实现目录。
- 历史算法版本请通过“算法完整名 + git commit”回溯定位。

---

## 3. 工作流与文档体系

### 3.1 文档分层

| 目录/文件 | 用途 |
| --- | --- |
| `README.md` | 项目总入口（当前文件） |
| `KAIWU-WORKFLOW.md` | 工作流规范、skills 的职责与调用顺序 |
| `CONTRIBUTE.md` | Git 协作规范、提交规范、文档同步要求 |
| `GLOBAL_DOCS/` | 全局稳定知识库（已实现算法总表、外部调研、正式文档、经验、变更） |
| `DEV_MEMORY/` | 当前开发状态记忆，用于 AI 在没有先前上下文时快速接手、断线重连和恢复当前工作状态 |
| `开发文档/` | 官方开发文档（环境规则、协议字段、框架接口） |
| `.claude/skills/` | Repo-local Claude Code skills |
| `.codex/skills/` | Repo-local Codex skills |
| `.copilot/skills/` | Repo-local Copilot skills |

### 3.2 Repo-local Skills

可使用以下 repo-local skills：

| Skill | 用途 |
| --- | --- |
| `/kaiwu-dev-init` | 开发前初始化：检查 Git 状态、阅读治理文档、确认当前起点 |
| `/kaiwu-doc-query` | 查询开发文档：路由到正确文档，回答字段/接口/协议问题 |
| `/kaiwu-current-algo-analysis` | 分析当前算法实现：输出入口、接口、超参数、workflow、已知限制 |
| `/kaiwu-algo-implementation` | 执行算法实现闭环：代码改动 -> smoke test -> DEV_MEMORY 同步 |
| `/kaiwu-full-iteration` | 执行完整迭代闭环：初始化 -> 状态检查 -> 目标确认 -> 实现 -> 收口 -> 等待训练结果 -> 归档 |
| `/kaiwu-version-control` | 版本收口：检查工作区、生成 commit、提示 push |
| `/kaiwu-memory-archive` | 归档：把 DEV_MEMORY 有价值内容沉淀到 GLOBAL_DOCS |

推荐调用顺序：

```text
/kaiwu-dev-init
-> /kaiwu-doc-query（按需）
-> /kaiwu-current-algo-analysis
-> /kaiwu-algo-implementation
-> /kaiwu-version-control
-> /kaiwu-memory-archive
-> /kaiwu-version-control
```

如果目标是从熟悉项目到实现、训练结果整理、归档的一次完整迭代，可直接使用：

```text
/kaiwu-full-iteration
```

### 3.3 开始算法迭代前先检查当前开发状态

在继续做算法开发前，先检查当前仓库是否存在未完成的算法实现或未收口的当前轮次任务。

- 先看 `DEV_MEMORY/TODO.md` 与 `DEV_MEMORY/算法文档.md`：确认当前轮次是否已有未收口任务
- 再看 `GLOBAL_DOCS/算法总表.md`：理解当前已实现算法与当前基线
- 若存在未完成实现且用户未明确切换方向，默认优先续做当前实现
- 若不存在未完成实现，再选择用户指定方向或 `GLOBAL_DOCS/算法调研.md` 中的候选方向

---

## 4. 正式算法代码入口与修改定位

### 4.1 代码入口链路

```text
train_test.py -> conf/app_conf_gorge_chase.toml (algo=ppo)
             -> conf/algo_conf_gorge_chase.toml (Agent + workflow)
             -> agent_ppo/conf/conf.py             (超参数)
             -> agent_ppo/conf/train_env_conf.toml (环境配置)
             -> agent_ppo/agent.py                 (Agent 接口)
             -> agent_ppo/feature/preprocessor.py  (特征+奖励)
             -> agent_ppo/feature/definition.py    (样本+GAE)
             -> agent_ppo/model/model.py           (网络结构)
             -> agent_ppo/algorithm/algorithm.py   (PPO loss)
             -> agent_ppo/workflow/train_workflow.py (训练循环)
```

### 4.2 修改定位指南

| 修改目标 | 主要文件 |
| --- | --- |
| 特征工程、合法动作、奖励 shaping | `agent_ppo/feature/preprocessor.py` |
| 样本结构、GAE、回报计算 | `agent_ppo/feature/definition.py` |
| 网络结构 | `agent_ppo/model/model.py` |
| PPO loss / 优化过程 | `agent_ppo/algorithm/algorithm.py` |
| 超参数 | `agent_ppo/conf/conf.py` |
| 训练循环、模型保存、监控上报 | `agent_ppo/workflow/train_workflow.py` |
| 环境配置（地图、步数、怪物） | `agent_ppo/conf/train_env_conf.toml` |
| 系统训练配置（batch、buffer） | `conf/configure_app.toml` |
| 切换平台算法 | `conf/app_conf_gorge_chase.toml` + `conf/algo_conf_gorge_chase.toml` |

### 4.3 当前实现细节的查阅方式

- 当前基线、当前训练得分、当前实现状态：查阅 `GLOBAL_DOCS/算法总表.md`
- 当前算法的特征、奖励、网络、超参数、已知限制：查阅算法总表中对应条目所链接的正式算法文档
- README 不维护这类会随算法迭代变化的实现级细节

---

## 5. 开发文档入口

环境规则、字段协议、框架接口不在代码里，在 `开发文档/` 中：

- `开发文档/README.md`：面向 AI 的文档索引（优先读这里）
- `开发文档/开发指南/环境详述.md`：`env.reset/step` 返回值、动作空间
- `开发文档/开发指南/数据协议.md`：observation/extra_info/EnvInfo 等字段定义
- `开发文档/腾讯开悟强化学习框架/综述.md`：框架总览

---

## 6. 关键配置文件速查

| 文件 | 关键参数 |
| --- | --- |
| `conf/app_conf_gorge_chase.toml` | 平台当前启用的算法 key |
| `conf/algo_conf_gorge_chase.toml` | 算法 key 到 Agent / workflow 的映射 |
| `conf/configure_app.toml` | 训练系统级参数（batch、buffer、模型同步等） |
| `agent_ppo/conf/conf.py` | 正式算法超参数定义 |
| `agent_ppo/conf/train_env_conf.toml` | 训练环境配置 |
| `kaiwu.json` | 项目标识（`project_code`） |
