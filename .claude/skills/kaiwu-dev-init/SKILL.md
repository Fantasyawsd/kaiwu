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

## 强制规则

- 任意新的开发轮次，第一步必须执行 `/kaiwu-dev-init`
- 未执行本 skill，不进入 `/kaiwu-algo-design` 或 `/kaiwu-algo-implementation`
- 如果 `GLOBAL_DOCS/算法总表.md` 与 `DEV_MEMORY/NOW.md` 不一致，必须先指出冲突

## 执行步骤

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
