---
name: kaiwu-algo-implementation
description: Execute a complete algorithm implementation cycle for the Gorge Chase KaiWuDRL repository. Check whether to continue the current unfinished round or start a new direction, implement code changes, run minimum validation, and keep DEV_MEMORY and formal docs in sync.
argument-hint: [algorithm-name-or-goal]
allowed-tools: Bash(*), Read, Grep, Glob, Edit, Write
---

# KaiWu Algo Implementation

实现目标：$ARGUMENTS

## 目标

执行一次算法实现闭环：确认当前开发状态，决定继续当前实现还是开始新方向，完成代码修改、最小验证与文档同步。

## 执行步骤

### Step 1：确认当前开发状态

先读：

- `GLOBAL_DOCS/算法总表.md`
- `DEV_MEMORY/TODO.md`
- `DEV_MEMORY/算法文档.md`
- `DEV_MEMORY/CHANGELOG.md`
- `DEV_MEMORY/EXPERIENCE.md`

若存在未完成实现且用户未明确切换方向，默认优先续做当前实现。

### Step 2：按需补查开发文档

若目标涉及环境、动作空间、字段协议或 workflow 约束，读取 `开发文档/` 对应文档。

### Step 3：实现代码

默认约束：

- 正式算法实现只在 `agent_ppo/` 中进行
- `agent_diy/` 只作为模板参考
- 每轮只验证一个主方向

### Step 4：最小验证

完成代码改动后，执行：

```bash
python3 train_test.py
```

### Step 5：同步文档

至少同步：

- `DEV_MEMORY/TODO.md`
- `DEV_MEMORY/CHANGELOG.md`
- `DEV_MEMORY/EXPERIENCE.md`
- `DEV_MEMORY/算法文档.md`

如果结论已经稳定，还要同步：

- 正式算法文档
- `GLOBAL_DOCS/算法总表.md`

## 规则

- 不虚构训练结果。
- 不自动 push。
- 若 smoke test 未通过，不做完整收口。
