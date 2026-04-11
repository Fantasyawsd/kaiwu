---
name: kaiwu-dev-init
description: Initialize a new development round for the Gorge Chase KaiWuDRL repository. This skill is mandatory before any algorithm design or implementation work.
argument-hint: [task-goal-or-algorithm-name]
allowed-tools: Bash(*), Read, Grep, Glob
---

# KaiWu Dev Init

初始化目标：$ARGUMENTS

## 目标

在任何算法设计、算法实现、算法测试、算法训练前，先确认仓库状态、当前基线、正式算法文档和 `DEV_MEMORY/NOW.md` 的上下文。

这是算法开发的第一步，必须优先使用。

> **重要提示**：`agent_ppo/` 是算法实现目录的名称（源于最初为 PPO 实现），但**不限制必须使用 PPO 算法**。你可以在该目录下实现任何 RL 算法（DQN、SAC、A3C、PPO 等），只要保持 `agent.py` 接口兼容（能通过 `train_test.py` 烟测）即可。

## 执行步骤

### Step 0:检查分支

任意非微小算法开发前，必须先创建或切换到 `feature/*` 分支，若当前分支不是 `feature/*`，本 skill 必须阻断后续算法设计/实现，并明确给出切分支命令建议

### Step 1：检查 Git 状态

执行：

- `git status`
- `git log --oneline -5`
- `git branch --show-current`

重点确认：

- 当前是否有未提交修改
- 当前是否位于 `main`
- 最近一次提交是否与当前任务相关

### Step 2：读取项目入口文档

按顺序读取：

1. `README.md`
2. `GLOBAL_DOCS/算法总表.md`
3. 当前 baseline 对应正式算法文档
4. `DEV_MEMORY/NOW.md`
5. `开发文档/README.md`

如果存在 `KAIWU-WORKFLOW.md`，一并读取；若缺失，要在初始化报告中注明。

### Step 3：确认当前开发状态

从 `DEV_MEMORY/NOW.md` 提取：

- 当前轮次目标
- 当前已经做到哪一步
- 当前下一步计划
- 是否存在未完成实现
- 是否已经形成算法文档初稿

### Step 4：输出初始化报告

至少包含：

- 当前分支
- Git 工作区状态
- 当前 baseline 算法
- 当前正式算法文档路径
- `NOW.md` 是否为空模板、过程记录还是算法文档初稿
- 是否建议继续当前轮次，还是开启新方向
- 当前下一步最应该使用哪个 skill

## 推荐输出格式

```markdown
## 初始化报告

- 当前分支：
- Git 状态：
- 当前 baseline：
- 当前正式算法文档：
- NOW.md 状态：
- 当前轮次是否有未完成任务：
- 建议下一步：
```

## 规则

- 只做读取和判断，不直接改代码
- 若发现 `main` 上有较大开发任务，明确提醒切分支
- 若发现当前轮次已经进入归档前阶段，建议后续使用 `/kaiwu-memory-archive`

---

## 下一步行动（执行后必须输出）

根据初始化结果，明确告诉用户接下来该做什么：

| 场景 | 下一步 Skill | 说明 |
|------|-------------|------|
| 当前在 `main` 分支，有未完成任务 | **先执行 Git 命令** | `git checkout -b feature/xxx`，切分支后再用 `/kaiwu-algo-implementation` |
| NOW.md 为空或只有模板 | `/kaiwu-algo-design` | 需要先做算法设计 |
| NOW.md 有完整设计但未实现 | `/kaiwu-algo-implementation` | 直接进入实现阶段 |
| NOW.md 已实现但未归档 | `/kaiwu-memory-archive` | 完成算法归档 |
| 想看当前算法状态 | `/kaiwu-current-algo-analysis` | 快速分析当前实现 |
| 训练完成需要整理结果 | 人工查看官方训练监控，按 `算法完整名 + 训练步数` 上传模型做 5 次官方评估，并将截图放入算法文档目录 | 整理真实训练结果与 10 张地图得分 |
