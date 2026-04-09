---
name: kaiwu-version-control
description: Perform git version-control wrap-up for the Gorge Chase KaiWuDRL repository. Check workspace state, verify documentation sync, and prepare clear commit messages for staged or final algorithm work.
argument-hint: [change-scope]
allowed-tools: Bash(*), Read, Grep, Glob
---

# KaiWu Version Control

收口目标：$ARGUMENTS

## 目标

检查工作区、确认文档同步状态，并生成适合当前阶段的 commit 建议。

## 执行步骤

### Step 1：检查工作区

- `git status`
- `git diff --stat`
- 必要时查看关键文件 diff

### Step 2：检查文档同步

确认以下是否已更新：

- `DEV_MEMORY/*`
- 正式算法文档
- `GLOBAL_DOCS/算法总表.md`
- 必要时 `GLOBAL_DOCS/CHANGELOG.md` / `TODO.md` / `EXPERIENCE.md`

### Step 3：生成提交建议

区分：

- 小步 commit
- 完整算法 commit

完整算法 commit 必须显式包含算法完整名。

## 规则

- 不自动 push。
- 若文档未同步，不建议做完整收口提交。
