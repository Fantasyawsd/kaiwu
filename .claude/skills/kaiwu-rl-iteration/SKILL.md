---
name: kaiwu-rl-iteration
description: Orchestrate a multi-stage KaiWu / KaiWuDRL optimization workflow: establish git baseline, maintain a linked work progress document, inspect the current algorithm, research new candidate methods, implement one hypothesis at a time, run experiments, analyze results, and decide whether to continue. Use when user says '优化算法', '持续迭代', '帮我组织整个开悟实验流程', or wants an end-to-end workflow rather than a single action.
argument-hint: [goal-budget-and-scope]
allowed-tools: Bash(*), Read, Grep, Glob, Edit, Write, TaskCreate, TaskUpdate, TaskList, Skill, AskUserQuestion, Agent
---

# KaiWu RL Iteration Workflow

工作流：$ARGUMENTS

## 概述

这个 skill 负责组织 KaiWu / KaiWuDRL 算法优化全流程，但不再自己承担所有细节。它的职责只有五类：

1. 建立 Git 基线
2. 维护工作进度文档
3. 按阶段调用专门 skills
4. 控制每轮只验证一个主假设
5. 根据结果决定继续、停止、提交或回退

默认采用双文档联动：

- `工作进度.md`：记录计划、状态、阻塞、阶段进展、决策和下一步
- `实验记录.md`：记录实验细节、指标结果、日志位置和结论摘要

两份文档必须通过统一的 work item / 轮次 ID 互相引用。不要把“当前算法 inspection”“Codex 调研细节”“实验运行细节”重新塞回这个 skill。本 skill 应始终优先调用更细粒度的 skills。

## 何时使用

在以下场景触发：

- 用户要一个端到端工作流，而不是一次性动作
- 用户说“持续迭代”“组织整个流程”“自动推进每一轮”
- 用户希望把当前算法检查、候选生成、实验运行、结果分析、Git 记录串起来
- 用户希望同时维护工作记录、工作规划和实验归档

## 阶段总览

```text
git baseline + 工作进度.md
→ /kaiwu-rl-current-algo
→ /kaiwu-rl-research-algo
→ implementation
→ /kaiwu-rl-run-experiment
→ /monitor-experiment
→ /analyze-results
→ 更新 工作进度.md + 实验记录.md
→ commit / stop / next iteration
```

## 双文档职责

### `工作进度.md`

用于记录：
- 当前轮次 / work item ID
- 当前状态
- Git 分支 / HEAD / baseline commit
- 主假设与目标指标
- 本阶段计划动作
- 阻塞项
- 下一步
- 关键决策

### `实验记录.md`

用于记录：
- smoke test / 正式实验的运行命令
- 日志与结果文件位置
- 指标结果与 baseline 对照
- 实验结论
- 值得保留的观察

### 统一规则

- 每轮都必须绑定唯一的 work item / 轮次 ID
- 两份文档必须互相引用同一个 ID
- 不允许只更新 `实验记录.md` 而不更新 `工作进度.md`
- 若仓库已有等价进度文档，优先复用，不重复新建

## Stage 0: 建立 Git 基线与工作条目

每轮开始前先执行：

- `git status`
- `git diff`
- `git log --oneline -5`

然后创建或引用仓库根目录的 `工作进度.md` 条目。若仓库中不存在等价文档，按 `references/work-progress-template.md` 初始化。

然后记录：

- work item / 轮次 ID
- 当前状态（初始建议为 `PLAN`）
- 当前分支
- HEAD commit
- baseline commit
- 工作区是否干净
- 本轮是否需要新建实验分支

规则：

- 若工作区存在与当前任务无关的脏改动，先向用户说明
- 若处于 `main` / `master` 且要做非微小改动，优先建立独立实验分支
- 每轮一个主假设，一个代码 commit；实验记录可单独一个结果 commit
- `工作进度.md` 负责计划与状态，`实验记录.md` 负责实验细节与结果

## Stage 1: 查看当前算法 / baseline

调用：

```text
/kaiwu-rl-current-algo
```

本阶段目标：
- 明确当前算法、workflow、关键配置
- 确认最小验证方式
- 识别当前 baseline 的真实入口
- 发现 `train_test.py` 与平台算法入口是否不一致

在结束本阶段前，把以下摘要写回当前 work item：
- 当前算法
- 最小验证命令
- 关键配置
- 风险或不一致

不要在这个阶段给出新算法方案。

## Stage 2: 查看新算法候选

查看

```text
算法整理.md
```

本阶段目标：
- 得到 2-4 个可落地候选
- 每个候选必须带真实文件路径与最小实验设计
- 标明低 / 中 / 高风险

在结束本阶段前，把以下内容写回当前 work item：
- 候选列表与优先级
- 默认选中的主假设
- 风险等级
- 本轮暂不做的方向

默认只选择一个主假设进入实现阶段。除非用户明确要求并行探索，否则不要一轮同时实现多个方向。

## Stage 3: 实现单轮假设

本阶段由主流程控制代码实现，但必须遵循：

- 每轮只改一个主方向
- 优先小步改动，保持可回退
- 配置改动与算法改动分开说明
- 改动后先做 smoke test，再做长实验

在进入实现前，先把以下内容写入 `工作进度.md`：
- 当前状态（建议 `IN_PROGRESS`）
- 本轮计划动作
- 预计修改文件
- 验收标准

如果方案较多或代码范围不清，优先用 `Agent` 做局部搜索、方案比较或失败排查。若出现阻塞，把阻塞原因、影响范围和下一步写回当前 work item。

## Stage 4: 跑实验

调用：

```text
/kaiwu-rl-run-experiment
```

该 skill 负责：
- 仓库特定入口
- 容器命令
- smoke test 与长实验分流
- 与通用 `/run-experiment` 的衔接
- 执行阶段对 `工作进度.md` 的状态回填

进入实验前，先在 `工作进度.md` 里记录：
- smoke / long run 命令
- 日志位置
- 结果文件位置
- 当前状态（`RUNNING_SMOKE` / `RUNNING_FORMAL`）

若实验被阻塞或中断，状态改为 `BLOCKED`，并记录原因、影响和下一步。

## Stage 5: 分析结果

调用：

```text
/analyze-results <results-path-or-description>
```

分析时至少回答：

- 是否优于 baseline
- 指标是否稳定
- 退化是噪声还是方向错误
- 下一轮是继续细化、补对照、回退还是换方向

在结束本阶段前，把以下内容回填到 `工作进度.md`：
- 关键指标对照
- 结论 / verdict
- 是否继续
- 下一步
- 对应的 `实验记录.md` 条目或结果路径

## Stage 6: 提交与双文档记录

推荐两段式提交：

### 代码提交

在 smoke test 通过后提交，正文写清：
- hypothesis
- scope
- validation
- 对应的 work item / 轮次 ID

### 结果提交

在实验完成并写入 `工作进度.md` 与 `实验记录.md` 后提交，正文写清：
- baseline
- metrics
- verdict
- next step
- 对应的 work item / 轮次 ID

不要提交：
- 半成品
- 未验证改动
- 多个方向的混合改动
- 只更新 `实验记录.md`、未更新 `工作进度.md` 的结果

## Stage 7: 停止或进入下一轮

在以下条件之一满足时停止：

- 达到用户目标
- 连续 2-3 轮无明显提升
- 预算或时长耗尽
- 仓库或环境阻塞导致无法可靠验证
- 用户要求暂停

停止时必须总结：

- 当前最佳方案
- 相比 baseline 的提升
- 对应 Git commit / 分支
- 最值得继续的 1-2 个方向
- 尚未解决的问题
- `工作进度.md` 中的最终状态（建议 `DONE` 或 `STOPPED`）

## 默认决策规则

若用户没有给额外偏好，默认：

- 优先优化真实表现指标，其次优化训练稳定性
- 先低风险微调，再高风险结构改动
- 先 smoke test，再长实验
- 连续无提升时不机械加码，优先复盘 baseline
- 优先保证 `工作进度.md` 与 `实验记录.md` 的信息一致

## 工具编排

### 专门 skills
- `/kaiwu-rl-current-algo`
- `/kaiwu-rl-research-algo`
- `/kaiwu-rl-run-experiment`
- `/monitor-experiment`
- `/analyze-results`

### 其他工具
- `Bash`：Git、容器命令、最小验证
- `Edit` / `Write`：代码、`工作进度.md` 与 `实验记录.md` 修改
- `TaskCreate` / `TaskUpdate` / `TaskList`：多轮任务追踪
- `Agent`：搜索、比较、排错
- `AskUserQuestion`：只在关键约束缺失时提问

### 参考资料
- `references/iteration-playbook.md`
- `references/gorge-chase-repo-map.md`
- `references/work-progress-template.md`

## 常见失误

避免以下情况：

- 跳过 `/kaiwu-rl-current-algo` 就直接改代码
- 只看 reward，不看 `sim_score` / `total_score`
- 没记录 Git 基线，导致实验结果无法映射到代码版本
- 只更新 `实验记录.md`，没更新 `工作进度.md`
- 没给每轮分配唯一的 work item / 轮次 ID
- 没记录阻塞项与下一步
- 把单一职责 skill 的内容重新复制回本工作流 skill
