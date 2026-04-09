# KAIWU-WORKFLOW

## 1. 目的

本文定义当前仓库的人机协作方式、文档分层、repo-local skills 使用顺序，以及算法实现与归档的标准闭环。

使用本仓库时，优先遵守以下原则：

1. 先读文档，再改代码。
2. 先检查当前开发状态，再决定是继续未完成算法还是开启新方向。
3. 先分析当前算法，再实现新改动。
4. 实现过程中持续维护 DEV_MEMORY，使 AI 即使没有之前上下文也能快速接手。
5. 小步验证，小步提交；完整算法完成后再做完整收口。
6. 训练得分和实验结论不得虚构；没有结果就明确写“暂无”。

---

## 2. 文档地图

### 2.1 根目录文档

- `README.md`
  - 项目总入口。
  - 说明当前项目结构、最小验证方式、repo-local skills 入口。
- `KAIWU-WORKFLOW.md`
  - 当前文件。
  - 说明工作流、skills 顺序、文档同步规则、人和 AI 的协作闭环。
- `CONTRIBUTE.md`
  - Git 协作与提交规范。
  - 说明分支、提交、合并、文档同步要求。

### 2.2 GLOBAL_DOCS

`GLOBAL_DOCS/` 用于保存全局稳定信息，是项目级长期记忆。

- `GLOBAL_DOCS/算法总表.md`
  - 算法清单总入口。
  - 记录已实现算法的算法名、完整算法名、训练得分、算法文档路径。
  - 由 AI 维护，不记录未实现候选方向。
- `GLOBAL_DOCS/算法调研.md`
  - 外部调研候选方向入口。
  - 主要由人维护，用于记录尚未实现的候选算法、论文方向、优化思路。
- `GLOBAL_DOCS/算法文档/`
  - 已实现算法的详细文档目录。
  - 正式算法文档统一使用 `算法名_时间.md` 命名。
- `GLOBAL_DOCS/TODO.md`
  - 全局待办。
  - 只保留跨轮次、跨算法仍然有意义的任务。
- `GLOBAL_DOCS/CHANGELOG.md`
  - 全局变更记录。
  - 记录值得长期保留的重要实现、文档结构变更、训练结论、SOTA 记录。
- `GLOBAL_DOCS/EXPERIENCE.md`
  - 全局经验库。
  - 只归档通用经验、常见坑、稳定可复用 trick。

### 2.3 DEV_MEMORY

`DEV_MEMORY/` 用于保存当前开发状态记忆，是开发过程中的外部记忆。

它的首要目标不是长期沉淀，而是让 AI 在断线重连、会话中断、上下文丢失、任务转交后，仍然能仅凭仓库内文件快速恢复当前工作状态并继续推进。

- `DEV_MEMORY/算法文档.md`
  - 当前算法状态快照。
  - 记录当前在做什么、做到哪一步、下一步准备做什么。
- `DEV_MEMORY/TODO.md`
  - 当前轮次待办与下一步。
  - 应让新的 AI 一眼看出“现在最该做什么”。
- `DEV_MEMORY/CHANGELOG.md`
  - 当前轮次局部变更轨迹。
  - 用于快速恢复“刚刚改了什么、验证到了哪一步”。
- `DEV_MEMORY/EXPERIENCE.md`
  - 当前轮次遇到的问题、解决方案、小 trick、风险记录。

### 2.4 开发文档

`开发文档/` 用于保存官方接口、环境规则、协议字段、框架流程。

- `开发文档/README.md`：开发文档索引与查询入口。
- `开发文档/开发文档.md`：总览文档。
- `开发文档/开发指南/*`：赛题与环境说明。
- `开发文档/腾讯开悟强化学习框架/*`：框架、Agent、workflow、模型、算法接口说明。
- `开发文档/EXPERIENCE.md`：开发文档查询与理解过程中的经验模板。

### 2.5 repo-local skills

仓库内 skills 位于：

- `.claude/skills/`
- `.codex/skills/`
- `.copilot/skills/`

当前仓库约定拆分为 7 个核心 skills：

- `/kaiwu-dev-init`
- `/kaiwu-doc-query`
- `/kaiwu-current-algo-analysis`
- `/kaiwu-algo-implementation`
- `/kaiwu-full-iteration`
- `/kaiwu-version-control`
- `/kaiwu-memory-archive`

---

## 3. Skills 的职责与顺序

| Skill | 主要职责 | 典型输入 | 主要输出 | 下一步 |
| --- | --- | --- | --- | --- |
| `/kaiwu-dev-init` | 做开发前初始化 | 任务目标、算法名 | 分支建议、文档入口、当前开发起点 | `/kaiwu-doc-query` 或 `/kaiwu-current-algo-analysis` |
| `/kaiwu-doc-query` | 查询开发文档与接口说明 | 问题、字段、接口、配置 | 文档依据、关键结论、相关路径 | `/kaiwu-current-algo-analysis` 或实现 |
| `/kaiwu-current-algo-analysis` | 分析当前算法实现 | 算法名、目录、baseline | 算法入口、接口、超参数、限制 | `/kaiwu-algo-implementation` |
| `/kaiwu-algo-implementation` | 执行算法实现闭环 | 目标算法或目标改动 | 代码改动、验证结果、DEV_MEMORY 更新 | `/kaiwu-version-control` 或 `/kaiwu-memory-archive` |
| `/kaiwu-full-iteration` | 执行完整算法迭代闭环 | 目标算法、优化方向、全流程请求 | 从初始化到实现、收口、等待训练结果、归档的完整推进状态 | 结束或 `/kaiwu-version-control` |
| `/kaiwu-version-control` | 做版本收口 | 本轮改动、提交范围 | 小步 commit / 完整 commit / push 建议 | `/kaiwu-memory-archive` 或结束 |
| `/kaiwu-memory-archive` | 把 DEV_MEMORY 归档到 GLOBAL_DOCS | 当前轮次 DEV_MEMORY | 全局 TODO / CHANGELOG / EXPERIENCE / 算法文档更新 | `/kaiwu-version-control` |

推荐默认顺序：

```text
/kaiwu-dev-init
-> /kaiwu-doc-query
-> /kaiwu-current-algo-analysis
-> /kaiwu-algo-implementation
-> /kaiwu-version-control
-> /kaiwu-memory-archive
-> /kaiwu-version-control
```

说明：

- 第一次 `/kaiwu-version-control` 用于小步提交或阶段性收口。
- `/kaiwu-memory-archive` 完成归档后，可再调用一次 `/kaiwu-version-control` 做最终文档收口。
- 如果用户目标是“一次完整迭代走到底”，可直接使用 `/kaiwu-full-iteration` 作为总控 skill。

---

## 4. 人与 AI 的协作闭环

### 4.1 人负责的部分

1. 外部调研算法、论文、改进方向。
2. 把尚未实现的候选算法或方向写入 `GLOBAL_DOCS/算法调研.md`。
3. 启动真实训练，记录平台训练日志或实验结果。
4. 决定是否继续该方向、是否合并、是否推远程。

### 4.2 AI 负责的部分

1. 读取 README / workflow / 开发文档。
2. 分析当前 baseline 与当前算法实现。
3. 实现代码或补全文档。
4. 执行最小验证。
5. 维护 `DEV_MEMORY/*` 作为当前开发状态记忆，保证后续 AI 即使没有本次会话上下文也能快速接手。
6. 维护 `GLOBAL_DOCS/算法总表.md` 作为已实现算法清单，并在需要时同步其他 `GLOBAL_DOCS/*`。
7. 根据用户指令做版本管理与归档。

### 4.3 协作边界

- 人提出方向，AI 负责落地。
- AI 不能虚构训练结果。
- AI 不能跳过文档同步。
- 正式 push / merge 以前，必须由人确认。

---

## 5. 标准算法实现闭环

### Stage 0：开发 init

执行：`/kaiwu-dev-init`

目标：

- 拉取最新状态或至少确认当前 Git 状态。
- 确认当前分支是否适合继续开发。
- 阅读 `README.md` 与 `KAIWU-WORKFLOW.md`。
- 确认算法总表、算法调研、DEV_MEMORY、开发文档入口。
- 检查 `DEV_MEMORY/TODO.md`、`DEV_MEMORY/算法文档.md`，确认当前是否存在进行中 / 未完成算法实现。
- 基于当前开发状态，明确本轮行动是“继续当前实现”还是“启动新方向”。

### Stage 1：开发文档查询

执行：`/kaiwu-doc-query`

目标：

- 查询环境、协议、接口、框架流程。
- 明确哪些信息来自官方开发文档，哪些来自当前仓库实现。
- 对有歧义的问题，优先回到 `开发文档/README.md` 进行路由。

### Stage 2：分析当前算法实现

执行：`/kaiwu-current-algo-analysis`

目标：

- 先根据开发状态确定当前目标算法。
- 若存在进行中 / 未完成算法，且用户没有明确切换方向，默认该算法为当前目标。
- 若不存在未完成算法，再从用户指定方向或 `GLOBAL_DOCS/算法调研.md` 中选择新方向。
- 阅读对应算法文档和代码路径。
- 输出当前算法实现细节、接口、超参数、workflow、已知限制。

### Stage 3：算法实现

执行：`/kaiwu-algo-implementation`

目标：

- 优先续做当前未完成算法；只有在无未完成算法，或用户明确要求切换方向时，才开始新算法实现。
- 初始化或更新 `DEV_MEMORY/*`。
- 进入“代码修改 -> 测试 -> 文档同步 -> 小步提交”的循环。

本阶段必须持续维护：

- `DEV_MEMORY/TODO.md`
- `DEV_MEMORY/CHANGELOG.md`
- `DEV_MEMORY/EXPERIENCE.md`
- `DEV_MEMORY/算法文档.md`

代码有实质性变化时，也要同步维护：

- 当前正式算法文档
- `GLOBAL_DOCS/算法总表.md`（当某个算法已实现并稳定落库，或其文档路径、训练得分发生变化）

### Stage 4：版本管理

执行：`/kaiwu-version-control`

目标：

- 检查工作区、差异、提交范围。
- 形成小步 commit 或完整算法 commit。
- 必要时准备 push，但是否真正 push 由用户决定。

### Stage 5：信息归档

执行：`/kaiwu-memory-archive`

目标：

- 从 `DEV_MEMORY/*` 中筛出有长期价值的内容。
- 归档到 `GLOBAL_DOCS/*`。
- 把当前算法草稿整理为正式算法文档。

### Stage 6：最终收口

再次执行：`/kaiwu-version-control`

目标：

- 确认代码、文档、归档内容都已同步。
- 完成最终 commit。
- 若用户明确要求，再 push 到远程。

### Stage 7：完整迭代总控（可选）

执行：`/kaiwu-full-iteration`

适用场景：

- 用户希望从项目熟悉、状态检查、目标确认一路推进到实现、训练结果整理、归档。
- 用户不想手动拆分 skill 顺序，希望由一个 skill 串起整条闭环。

目标：

- 串起 Stage 0 到 Stage 6。
- 在“需要用户执行真实训练”的位置显式停住等待。
- 用户返回训练结果后，再完成结果整理、归档与最终收口。

---

## 6. GLOBAL_DOCS 与 DEV_MEMORY 的同步规则

### 6.1 何时更新 DEV_MEMORY

以下场景必须更新 `DEV_MEMORY/*`：

- 确定本轮目标算法或主假设时。
- 改动代码后。
- 跑完最小验证后。
- 遇到问题并定位到原因时。
- 发现有价值的小 trick、解决方案时。
- 任何可能导致会话中断、任务转交、需要稍后继续的节点。

### 6.2 何时更新 GLOBAL_DOCS

以下场景必须更新 `GLOBAL_DOCS/*`：

- 算法从“未实现”变为“已实现”。
- 当前实现名或算法文档路径发生变化。
- 训练得分或实验结论得到确认。
- 某个经验已经证明是跨轮次有效的稳定经验。
- 某个 TODO / CHANGELOG 不再只是当前任务局部信息，而成为全局事项。

### 6.3 归档原则

- `DEV_MEMORY` 首先是当前开发状态记忆，其次才是工作草稿，不追求稳定排版。
- `DEV_MEMORY` 的写法要优先服务于“无上下文快速接手”和“断线重连”。
- `GLOBAL_DOCS` 是长期知识库，要求结构清晰、可被后续 AI 直接读取。
- 不要把 `DEV_MEMORY` 原样整份复制到 `GLOBAL_DOCS`；必须先过滤、整理、去重。

---

## 7. Git 协作工作流

推荐流程：

1. `git pull` 拉取最新代码。
2. 创建或切换到 `feature/*` 分支。
3. 阅读 `README.md`、`KAIWU-WORKFLOW.md`、`CONTRIBUTE.md`。
4. 开发与最小验证。
5. 做小步 commit。
6. 算法完整实现后，再做完整 commit。
7. 用户确认后，再 push / merge。

约束：

- `main` 只接受已经完整实现、并经过验证的版本。
- 非微小改动不要直接在 `main` 上开发。
- 未更新文档前，不做“完整实现”收口提交。

---

## 8. 文档同步硬规则

每完成一个有意义的改动，至少检查以下清单：

- 代码是否已验证？
- `DEV_MEMORY/TODO.md` 是否更新？
- `DEV_MEMORY/CHANGELOG.md` 是否更新？
- `DEV_MEMORY/EXPERIENCE.md` 是否更新？
- 当前算法文档是否补充了实现细节？
- 如果状态变化已稳定，是否同步到 `GLOBAL_DOCS/算法总表.md`？
- 如果是通用经验，是否同步到 `GLOBAL_DOCS/EXPERIENCE.md`？

---

## 9. 当前仓库的基线结论

- 当前完整可运行 baseline：`agent_ppo/`
- 当前模板算法：`agent_diy/`
- 当前 smoke / 最小验证入口：`python3 train_test.py`
- 当前平台启用算法：`conf/app_conf_gorge_chase.toml` 中 `algo = "ppo"`
- 当前 workflow 注册：`conf/algo_conf_gorge_chase.toml` 中 `ppo -> agent_ppo.workflow.train_workflow.workflow`

---

## 10. 使用建议

如果目标是继续做算法开发，推荐直接按下面顺序开始：

```text
/kaiwu-dev-init
/kaiwu-doc-query
/kaiwu-current-algo-analysis
/kaiwu-algo-implementation
```

如果目标是挑选新的未实现方向，先看：

```text
GLOBAL_DOCS/算法调研.md
```

如果目标是一次执行完整迭代闭环，推荐：

```text
/kaiwu-full-iteration
```

如果目标是整理和归档当前开发成果，推荐：

```text
/kaiwu-memory-archive
/kaiwu-version-control
```

如果目标是只看当前 baseline 而不改代码，推荐：

```text
/kaiwu-current-algo-analysis
```
