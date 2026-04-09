---
name: kaiwu-dev-init
description: Initialize a new development session for the Gorge Chase KaiWuDRL repository. Check git state, read key governance documents, and confirm the current algorithm entry points and DEV_MEMORY state before any code changes.
argument-hint: [task-goal-or-algorithm-name]
allowed-tools: Bash(*), Read, Grep, Glob, AskUserQuestion
---

# KaiWu Dev Init

初始化目标：$ARGUMENTS

## 目标

在做任何代码改动之前，先确认仓库状态、文档入口和当前开发起点，避免在错误上下文上继续开发。

## 执行步骤

### Step 1：检查 Git 状态

- `git status`
- `git log --oneline -5`
- `git branch --show-current`

若当前在 `main` 上且准备做非微小改动，建议切到 `feature/*` 分支。

### Step 2：阅读治理文档

按顺序读取：

1. `README.md`
2. `KAIWU-WORKFLOW.md`
3. `GLOBAL_DOCS/算法总表.md`

### Step 3：确认 DEV_MEMORY 状态

读取：

- `DEV_MEMORY/TODO.md`
- `DEV_MEMORY/CHANGELOG.md`
- `DEV_MEMORY/EXPERIENCE.md`
- `DEV_MEMORY/算法文档.md`

重点提取：

- 当前做到哪一步
- 下一步是什么
- 是否存在未完成算法实现

### Step 4：输出初始化报告

至少包括：

- 当前分支 / Git 状态
- 当前基线算法
- 当前主要文档入口
- DEV_MEMORY 是否为空模板
- 建议下一步使用哪个 skill

## 规则

- 只做检查，不改代码。
- 若 `GLOBAL_DOCS/算法总表.md` 与 `DEV_MEMORY/*` 不一致，要显式指出。
