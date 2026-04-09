---
name: kaiwu-memory-archive
description: Archive the current development session from DEV_MEMORY into GLOBAL_DOCS. Promote valuable experiences, changelogs, and algorithm documentation while filtering transient notes.
argument-hint: [archive-scope]
allowed-tools: Read, Grep, Glob, Edit, Write
---

# KaiWu Memory Archive

归档目标：$ARGUMENTS

## 目标

把当前轮次 `DEV_MEMORY/*` 中有长期价值的内容整理到 `GLOBAL_DOCS/*`，并在归档后重置 `DEV_MEMORY` 模板。

## 执行步骤

### Step 1：读取当前记忆

读取：

- `DEV_MEMORY/TODO.md`
- `DEV_MEMORY/CHANGELOG.md`
- `DEV_MEMORY/EXPERIENCE.md`
- `DEV_MEMORY/算法文档.md`

### Step 2：筛选可归档内容

区分：

- 当前轮次临时信息
- 可跨轮次复用的稳定经验
- 已稳定的算法实现描述

### Step 3：同步到 GLOBAL_DOCS

按需更新：

- `GLOBAL_DOCS/算法文档/*`
- `GLOBAL_DOCS/算法总表.md`
- `GLOBAL_DOCS/CHANGELOG.md`
- `GLOBAL_DOCS/TODO.md`
- `GLOBAL_DOCS/EXPERIENCE.md`

### Step 4：重置 DEV_MEMORY

归档完成后，把 `DEV_MEMORY/*` 恢复为模板化初始状态，便于下一轮继续使用。

## 规则

- 不要把 `DEV_MEMORY` 原样整份复制到 `GLOBAL_DOCS`。
- 先过滤、整理、去重，再归档。
