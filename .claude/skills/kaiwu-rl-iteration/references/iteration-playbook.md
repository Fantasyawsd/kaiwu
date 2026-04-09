# KaiWu / KaiWuDRL 迭代优化作战手册

本参考文档用于在触发 `kaiwu-rl-iteration` 工作流 skill 后，为 Claude 提供阶段编排、双文档记录和决策规范。

## 一、工作流职责

`kaiwu-rl-iteration` 只负责：

1. 建立 Git 基线
2. 维护 `工作进度.md`
3. 调用专门 skills
4. 组织每轮实现、验证、记录和停止判断
5. 汇总最佳结果

它不直接承担：

- 当前算法 inspection 的细节
- Codex 算法调研的细节
- 仓库特定实验入口的全部说明

这些分别交给：

- `/kaiwu-rl-current-algo`
- `/kaiwu-rl-research-algo`
- `/kaiwu-rl-run-experiment`

## 二、双文档联动

### `工作进度.md`

用于记录：
- work item / 轮次 ID
- 当前状态
- Git 分支 / HEAD / baseline commit
- 主假设
- 目标指标 / 验收标准
- 阶段计划
- 阻塞项
- 决策
- 下一步

### `实验记录.md`

用于记录：
- smoke test / 正式实验命令
- 日志位置
- 结果文件
- 关键指标
- 结论摘要

### 统一规则

- 每轮都必须绑定唯一 ID（如 `iter-001`）
- 两份文档必须引用同一个 ID
- 不允许只更新 `实验记录.md` 而不更新 `工作进度.md`
- 若仓库已有等价进度文档，优先复用，不重复创建

## 三、标准阶段顺序

### Stage 0：Git baseline + 工作条目

- `git status`
- `git diff`
- `git log --oneline -5`
- 创建或引用当前 work item

记录到 `工作进度.md`：
- 当前状态（初始建议 `PLAN`）
- 当前分支
- HEAD commit
- baseline commit
- 工作区是否干净
- 是否需要新建实验分支

### Stage 1：当前算法快照

调用：

```text
/kaiwu-rl-current-algo
```

输出后写回 `工作进度.md`：
- 当前算法
- 最小验证命令
- 关键配置
- 风险或不一致

### Stage 2：算法候选调研

调用：

```text
/kaiwu-rl-research-algo <goal-and-constraints>
```

输出后写回 `工作进度.md`：
- 2-4 个可落地候选
- 每个候选的目标文件、风险、最小实验设计
- 选中的主假设
- 暂不采用的方向

### Stage 3：实现单轮假设

规则：
- 每轮只选 1 个主假设
- 小步改动
- 保持可回退

开始实现前写回 `工作进度.md`：
- 当前状态（建议 `IN_PROGRESS`）
- 本轮计划动作
- 预计修改文件
- 验收标准
- 阻塞项（若有）

### Stage 4：实验执行

调用：

```text
/kaiwu-rl-run-experiment
```

若是长任务，再调用：

```text
/monitor-experiment
```

执行阶段至少回填到 `工作进度.md`：
- smoke / long run 命令
- 日志位置
- 结果文件位置
- 当前状态（`RUNNING_SMOKE` / `RUNNING_FORMAL` / `BLOCKED`）

### Stage 5：结果分析

调用：

```text
/analyze-results
```

分析后写回 `工作进度.md`：
- 与 baseline 的指标对照
- 结果
- 决策
- 下一步
- 对应 `实验记录.md` 条目

### Stage 6：提交与记录

- smoke test 通过后提交代码版本
- `工作进度.md` 与 `实验记录.md` 更新完成后提交结果版本

### Stage 7：继续或停止

根据结果决定：
- 继续细化
- 补控制变量实验
- 回退
- 换方向
- 停止

停止时更新 `工作进度.md` 最终状态：
- `DONE`
- `STOPPED`

## 四、单轮工作模板

- 轮次编号 / work item：`iter-001` / `iter-002` / ...
- 当前状态：
- Git 分支：
- HEAD commit：
- baseline commit：
- 主假设：
- 目标指标：
- 验收标准：
- 本轮计划：
- 最小验证：
- 正式实验：
- 日志 / 结果位置：
- 结果：
- 决策：
- 阻塞项：
- 下一步：
- `实验记录.md` 条目：

如需完整结构，优先参考：
- `references/work-progress-template.md`

## 五、何时停

满足任一条件时停止：

- 达到用户目标
- 连续 2-3 轮无提升
- 预算/时长耗尽
- 环境阻塞导致无法可靠验证

停止时输出：

- 当前最佳方案
- 最佳 commit / 分支
- 相比 baseline 的提升
- 最值得继续的 1-2 个方向
- 尚未解决的问题
- `工作进度.md` 最终状态

## 六、常见失误

- 没先 `/kaiwu-rl-current-algo` 就直接改代码
- 没先 `/kaiwu-rl-research-algo` 就盲改多个方向
- 不先 smoke test 就跑长实验
- 没记录 Git 基线
- 只看 reward，不看 score
- 只更新 `实验记录.md`，不更新 `工作进度.md`
- 没记录阻塞项与下一步
- 把单一职责 skill 的细节重新塞回工作流 skill
