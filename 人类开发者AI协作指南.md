# 人类开发者 AI 协作指南

本文件面向使用 Codex、Claude Code 等 AI 开发工具的人类开发者，目标不是解释算法细节本身，而是回答下面这些更实际的问题：

- 这个项目到底要做什么

- 项目结构是什么，应该先看哪里

- 人自己负责什么，AI 负责什么

- 想改奖励、特征、网络、超参数时该改哪些文件

- 应该用什么提示词和命令驱动 AI 去迭代算法

- Git 应该怎么协作

- 一轮完整算法迭代里，人和 AI 分别在什么阶段做什么

这份文档是对 [人类开发者前置知识.md](人类开发者前置知识.md) 的展开版。前者更像“上岗前 checklist”，本文则是“实际开工操作手册”。

---

## 1. 项目在做什么

这是腾讯开悟 Gorge Chase / 峡谷追猎强化学习代码包。

当前项目目标是：训练一个智能体控制鲁班七号，在 `128x128` 栅格地图中躲避怪物、收集宝箱，并尽量存活到最大步数。

当前仓库里的正式算法基线是：

- 算法名：`ppo`

- 正式实现目录：`agent_ppo/`

- 当前完整算法名：`agent_ppo_20260409_1733`

- 当前状态：已完成 smoke test，通过；暂无正式训练得分

重要约束：

- **所有正式算法迭代默认都在 `agent_ppo/` 里做**

- `agent_diy/` 只是模板参考，不是正式算法落库目录

- README 不维护细粒度算法实现，算法当前状态以 `GLOBAL_DOCS/算法总表.md` 和对应正式算法文档为准

---

## 2. 先看什么

如果你是第一次接手这个仓库，建议按下面顺序阅读：

1. [人类开发者前置知识.md](人类开发者前置知识.md)

2. [README.md](README.md)

3. [KAIWU-WORKFLOW.md](KAIWU-WORKFLOW.md)

4. [CONTRIBUTE.md](CONTRIBUTE.md)

5. [GLOBAL_DOCS/算法总表.md](GLOBAL_DOCS/算法总表.md)

6. [GLOBAL_DOCS/算法文档/agent_ppo_20260409_1733.md](GLOBAL_DOCS/算法文档/agent_ppo_20260409_1733.md)

7. [开发文档/README.md](开发文档/README.md)

如果不是第一次接手，而是继续上一轮工作，额外先看：

1. [DEV_MEMORY/TODO.md](DEV_MEMORY/TODO.md)

2. [DEV_MEMORY/算法文档.md](DEV_MEMORY/算法文档.md)

3. [DEV_MEMORY/CHANGELOG.md](DEV_MEMORY/CHANGELOG.md)

4. [DEV_MEMORY/EXPERIENCE.md](DEV_MEMORY/EXPERIENCE.md)

简单理解：

- `GLOBAL_DOCS/` 看“长期稳定事实”

- `DEV_MEMORY/` 看“当前这一轮做到哪了”

- `开发文档/` 看“官方环境规则、协议和框架接口”

---

## 3. 目录结构和关键文件

### 3.1 最重要的目录

| 路径 | 作用 |

| --- | --- |

| `agent_ppo/` | 正式算法实现目录，真正要改的核心代码都在这里 |

| `agent_diy/` | 模板目录，只参考，不作为正式算法落库位置 |

| `conf/` | 平台算法选择、算法映射、系统训练配置 |

| `开发文档/` | 官方文档，回答环境规则、字段协议、框架接口问题 |

| `GLOBAL_DOCS/` | 全局稳定知识库 |

| `DEV_MEMORY/` | 当前轮次状态记忆，方便 AI 断线重连和快速接手 |

### 3.2 代码入口链路

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

### 3.3 改什么去哪里改

| 目标 | 主要文件 |

| --- | --- |

| 改特征工程、合法动作、即时奖励 | `agent_ppo/feature/preprocessor.py` |

| 改样本结构、GAE、回报计算 | `agent_ppo/feature/definition.py` |

| 改网络结构 | `agent_ppo/model/model.py` |

| 改 PPO loss、优化流程 | `agent_ppo/algorithm/algorithm.py` |

| 改算法超参数 | `agent_ppo/conf/conf.py` |

| 改训练 workflow、终局奖励、模型保存 | `agent_ppo/workflow/train_workflow.py` |

| 改训练环境配置 | `agent_ppo/conf/train_env_conf.toml` |

| 改系统训练配置 | `conf/configure_app.toml` |

| 切换平台启用算法 | `conf/app_conf_gorge_chase.toml` + `conf/algo_conf_gorge_chase.toml` |

---

## 4. 人负责什么，AI 负责什么

### 4.1 人类开发者主要负责

- 决定本轮优化目标和主假设

- 做外部调研，决定要不要尝试新方向

- 决定是否继续当前方向，还是切换方向

- 启动平台真实训练，观察监控和日志

- 记录正式实验结果

- 最终决定是否 push / merge

### 4.2 AI 主要负责

- 阅读仓库文档和官方开发文档

- 分析当前基线实现和代码入口

- 完成代码修改

- 跑最小验证，比如 `python3 train_test.py`

- 把当前状态同步到 `DEV_MEMORY/*`

- 在结论稳定后整理到 `GLOBAL_DOCS/*`

- 生成 commit 建议、整理变更说明

### 4.3 边界要说清

- 人提方向，AI 负责落地

- AI 不能虚构训练结果

- AI 不能跳过文档同步

- 正式训练结果以人跑出来的平台结果为准

- 正式 push / merge 之前必须有人确认

---

## 5. 怎么驱动 AI

这里分两种情况。

### 5.1 工具支持 repo-local skills 时

如果你的 AI 工具支持读取仓库里的 skills，优先使用这套顺序：

```text

/kaiwu-dev-init

/kaiwu-doc-query

/kaiwu-current-algo-analysis

/kaiwu-algo-implementation

/kaiwu-version-control

/kaiwu-memory-archive

/kaiwu-version-control

```

如果你想让 AI 一次把整轮流程串起来，可以直接说：

```text

/kaiwu-full-iteration

```

推荐提示词示例：

#### 1. 初始化仓库状态

```text

/kaiwu-dev-init

目标：确认当前仓库状态、当前算法入口、当前是否有未完成任务。先不要改代码。

```

#### 2. 分析当前基线

```text

/kaiwu-current-algo-analysis ppo

重点告诉我：

1. 当前算法入口链路

2. 想改奖励/特征/网络/超参数分别改哪些文件

3. 当前实现有哪些已知限制

```

#### 3. 开始一轮实现

```text

/kaiwu-algo-implementation

目标：在 agent_ppo 中优化 xxx。

要求：

1. 先读 README、KAIWU-WORKFLOW、GLOBAL_DOCS/算法总表、DEV_MEMORY/*、开发文档/README

2. 只改 agent_ppo/ 里的正式实现，不要把正式改动做在 agent_diy/

3. 改完后运行 python3 train_test.py 做 smoke test

4. 同步 DEV_MEMORY/TODO.md、CHANGELOG.md、EXPERIENCE.md、算法文档.md

5. 不要 push

```

#### 4. 收口和归档

```text

/kaiwu-version-control

请检查本轮改动范围，给出建议 commit message，暂时不要 push

```

```text

/kaiwu-memory-archive

请把本轮稳定结论归档到 GLOBAL_DOCS，并同步算法总表和正式算法文档

```

### 5.2 工具不支持 skills 时

如果你用的是通用型 Codex 或其他 AI 工具，没有 slash skills，也可以直接用下面的 prompt 模板。

#### 模板 A：先分析，不直接改代码

```text

先不要改代码。请先阅读以下文件：

README.md

KAIWU-WORKFLOW.md

CONTRIBUTE.md

GLOBAL_DOCS/算法总表.md

GLOBAL_DOCS/算法文档/agent_ppo_20260409_1733.md

开发文档/README.md

DEV_MEMORY/TODO.md

DEV_MEMORY/算法文档.md

DEV_MEMORY/CHANGELOG.md

DEV_MEMORY/EXPERIENCE.md

读完后只输出：

1. 当前项目目标

2. 当前算法入口链路

3. 如果我要改奖励/特征/网络/超参数，各该改哪些文件

4. 当前是否存在未完成的轮次任务

5. 建议的下一步

```

#### 模板 B：让 AI 开始改代码

```text

目标：在 agent_ppo 中尝试 xxx。

要求：

1. 正式实现只改 agent_ppo/，不要把正式实现放到 agent_diy/

2. 改代码前先复述将修改哪些文件、为什么改这些文件

3. 改完后运行最小验证命令

4. 同步 DEV_MEMORY/TODO.md、CHANGELOG.md、EXPERIENCE.md、算法文档.md

5. 如果结论已经稳定，再更新 GLOBAL_DOCS/算法总表.md 和正式算法文档

6. 不要编造训练分数

7. 不要 push，先给我 diff 摘要和验证结果

```

#### 模板 C：喂给 AI 一轮训练结果

```text

我已经跑完一轮正式训练，下面是结果和日志摘要：

1. 训练任务 ID：

2. 地图/配置：

3. 关键监控指标：

4. 最终表现：

5. 观察到的问题：

请你基于这些结果：

1. 更新当前算法文档

2. 更新 GLOBAL_DOCS/算法总表.md 中的训练状态

3. 给出下一轮迭代建议

4. 如有必要，同步 GLOBAL_DOCS/CHANGELOG.md、TODO.md、EXPERIENCE.md

```

---

## 6. 常用命令

### 6.1 Git 起手式

```bash

git pull

git status

git checkout -b feature/<topic>

```

示例：

```bash

git checkout -b feature/ppo-reward-shaping

```

### 6.2 最小验证

根据当前 README，默认在容器内做 smoke test：

```bash

docker exec -it kaiwu-dev-kaiwudrl-1 bash

python3 train_test.py

```

如果你的容器名不是这个，就替换成你自己的容器名。

### 6.3 查看改动和提交

```bash

git status

git diff

git add <files>

git commit -m "feat(ppo): tune reward shaping"

```

如果这是一次“完整算法实现”的正式提交，commit 信息里必须显式带上**完整算法名**，例如：

```bash

git commit -m "feat(ppo): finalize agent_ppo_20260409_1733"

```

### 6.4 推送分支

```bash

git push origin feature/<topic>

```

注意：push 和 merge 默认放在“人确认之后”。

---

## 7. Git 协作原则

你可以把这部分理解成“人和 AI 都要遵守的底线”。

1. 非微小改动不要直接在 `main` 上开发。

2. 开工前先 `git pull`，再切到 `feature/*` 分支。

3. AI 每做完一个有意义的改动，就同步一次 `DEV_MEMORY/*`。

4. 没通过最小验证，不要做“完整算法实现”收口提交。

5. 没更新文档，不要把这轮工作当成已完成。

6. 没有正式训练结果时，要明确写“暂无正式训练得分”。

7. 完整算法 commit 必须带完整算法名，并与 `GLOBAL_DOCS/算法总表.md` 保持一致。

8. `main` 只接收已经完成验证、文档同步完整的版本。

---

## 8. 一轮完整算法迭代怎么做

下面是推荐的人机协作闭环。

### Stage 0：确定目标

人负责：

- 决定本轮主方向，例如“优化奖励 shaping”或“接入 16 维动作空间”

AI 负责：

- 复述目标

- 映射到需要改动的代码文件

- 检查是否和当前 `DEV_MEMORY/*` 冲突

### Stage 1：初始化和看现状

人负责：

- 确认是否继续当前轮次，还是开启新方向

AI 负责：

- 读 README、KAIWU-WORKFLOW、CONTRIBUTE

- 读 `GLOBAL_DOCS/算法总表.md`

- 读 `DEV_MEMORY/*`

- 输出“当前做到哪一步、下一步建议”

### Stage 2：查文档和分析基线

人负责：

- 指出自己关注的问题，比如 reward、动作空间、环境协议

AI 负责：

- 去 `开发文档/` 查官方说明

- 梳理当前基线入口、接口、超参数和已知限制

### Stage 3：代码实现

人负责：

- 确认这轮主要尝试点，不让 AI 同时改太多方向

AI 负责：

- 在 `agent_ppo/` 中实现改动

- 写必要但简短的注释

- 维护 `DEV_MEMORY/*`

### Stage 4：最小验证

人负责：

- 确认验证范围是否足够

AI 负责：

- 执行 `python3 train_test.py`

- 说明 smoke test 是否通过

- 如果失败，定位原因并修复

### Stage 5：真实训练

人负责：

- 在平台或正式环境启动训练

- 观察监控、日志、得分

- 记录真实实验结果

AI 负责：

- 给出训练前检查清单

- 帮你整理监控指标和日志

- 基于结果提出下一轮建议

### Stage 6：文档同步

人负责：

- 确认哪些结论是稳定的，哪些还只是尝试

AI 负责：

- 当前轮次信息写入 `DEV_MEMORY/*`

- 稳定结论整理进 `GLOBAL_DOCS/*`

- 必要时更新正式算法文档和算法总表

### Stage 7：Git 收口

人负责：

- 决定是否 commit、push、merge

AI 负责：

- 整理 diff 摘要

- 生成 commit message 建议

- 核对文档、验证、代码是否同步完成

---

## 9. 常见误区

### 误区 1：一上来就让 AI 改代码

正确做法：先让 AI 读文档、看 `DEV_MEMORY/*`、确认当前任务状态，再动手。

### 误区 2：把正式实现做进 `agent_diy/`

正确做法：正式算法迭代默认改 `agent_ppo/`，`agent_diy/` 只当模板。

### 误区 3：让 AI 一次改奖励、特征、网络、workflow 四个方向

正确做法：一轮只验证一个主假设，否则很难知道结果是哪个改动带来的。

### 误区 4：只改代码，不更新记忆和文档

正确做法：每轮都维护 `DEV_MEMORY/*`；结论稳定后再归档到 `GLOBAL_DOCS/*`。

### 误区 5：没有正式训练结果，却写成“效果提升”

正确做法：没有正式训练结果就写清楚“仅 smoke test 通过，暂无正式训练得分”。

---

## 10. 最短可执行版本

如果你只想记住最短流程，可以直接照这个顺序走：

1. `git pull`

2. `git checkout -b feature/<topic>`

3. 让 AI 先读 `README.md`、`KAIWU-WORKFLOW.md`、`CONTRIBUTE.md`、`GLOBAL_DOCS/算法总表.md`、`DEV_MEMORY/*`

4. 让 AI 输出当前入口链路和改动文件定位

5. 让 AI 在 `agent_ppo/` 中实现单一方向改动

6. 跑 `python3 train_test.py`

7. 让 AI 更新 `DEV_MEMORY/*`

8. 人跑正式训练

9. 让 AI 基于真实结果更新 `GLOBAL_DOCS/*`

10. 人确认后再 commit / push / merge

这就是这个仓库里“人做决策，AI 做实现与整理”的标准协作闭环。