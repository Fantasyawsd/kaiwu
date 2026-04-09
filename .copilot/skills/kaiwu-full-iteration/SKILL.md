---

name: kaiwu-full-iteration

description: Run a full KaiWu algorithm iteration cycle for the Gorge Chase KaiWuDRL repository from project onboarding and workflow familiarization through current-state inspection, asking the user which algorithm or direction to implement, code implementation, version-control wrap-up, waiting for user-run training results, and final archive. Use when the user asks for a full iteration, end-to-end loop, 全流程, 完整迭代, or wants Codex to drive the whole implementation-to-archive cycle.

argument-hint: [algorithm-name-or-goal]

allowed-tools: Bash(*), Read, Grep, Glob, Edit, Write, AskUserQuestion

---



# KaiWu Full Iteration



迭代目标：$ARGUMENTS



## 目标



组织一次完整算法迭代闭环：熟悉项目与工作流、检查当前开发状态、确认本轮算法目标、完成实现与最小验证、做版本收口、等待用户执行真实训练并返回结果、最后归档并重置 `DEV_MEMORY`。



## 何时使用



- 用户希望“一次走完整个迭代闭环”

- 用户说“全流程”、“完整迭代”、“从实现到归档”

- 需要从当前仓库状态出发，推进到“代码完成 + 用户训练 + 文档归档”

- 需要一个统一 skill 串起现有多个 repo-local skills



## 执行步骤



### Step 0：建立起点



按以下顺序读取并理解：



1. `README.md`
2. `KAIWU-WORKFLOW.md`
3. `GLOBAL_DOCS/算法总表.md`
4. `DEV_MEMORY/TODO.md`
5. `DEV_MEMORY/算法文档.md`



必要时补充：

- `开发文档/README.md`

- 对应算法正式文档

- 当前算法相关代码入口



目标：

- 明确项目结构与标准工作流

- 明确当前是否存在未完成算法实现或未收口任务

- 明确当前基线、当前正式实现目录、当前文档入口



### Step 1：确认当前开发状态



- 先检查 `GLOBAL_DOCS/算法总表.md` 中是否有 `进行中` / 未完成算法

- 再检查 `DEV_MEMORY/*` 是否仍在跟踪某个未完成轮次

- 若存在未完成实现且用户未明确切换方向，默认优先续做当前实现

- 若算法总表与 `DEV_MEMORY` 指向不一致，先明确指出冲突，再继续



输出一个简短状态摘要：

- 当前开发起点

- 是否存在未完成算法

- 推荐本轮默认行动



### Step 2：向用户确认本轮目标



使用 `AskUserQuestion` 明确本轮目标，至少确认：

- 是继续当前未完成实现，还是切换到新方向

- 本轮要实现的算法名或改动方向



若仓库里已有未完成实现，提问时要把“继续当前实现”作为默认推荐项。



### Step 3：按需查询开发文档



若本轮目标涉及环境协议、动作空间、字段含义、接口约束，读取 `开发文档/` 中对应文档，避免带着错误假设写代码。



重点查询场景：

- `env.reset` / `env.step`

- `observation` / `extra_info`

- 动作空间与合法动作

- Agent / workflow 接口约束



### Step 4：分析当前算法实现



根据本轮目标定位当前算法：

- 读取算法总表中的对应条目

- 读取正式算法文档

- 读取代码入口链路



至少明确：

- 代码入口

- 当前实现状态

- 关键接口

- 当前限制

- 本轮应修改哪些文件



### Step 5：执行算法实现



进入实现阶段时：

- 每轮只改一个主方向

- 优先在 `agent_ppo/` 中实现正式算法迭代

- 改动后立即同步 `DEV_MEMORY/*`

- 完成后执行最小验证：`python3 train_test.py`



实现完成的最低条件：

1. 本轮目标对应代码已落地
2. smoke test 通过
3. `DEV_MEMORY/*` 已同步
4. 若接口或超参数变化明显，对应正式算法文档已更新



### Step 6：第一次版本收口



在本轮实现完成后：

- 检查工作区范围

- 确认文档同步状态

- 生成清晰的阶段性或完整实现 commit



不要自动 push。



### Step 7：等待用户执行真实训练



到这里必须显式暂停，等待用户执行真实训练。



向用户说明：

- 代码实现与最小验证已完成

- 现在需要用户在真实训练环境中启动训练

- 返回时请提供真实训练结果、日志、得分或结论



在拿到真实训练结果之前：

- 不更新正式训练得分

- 不宣称算法优于旧基线

- 不把推测写入 `GLOBAL_DOCS/算法总表.md`



### Step 8：接收并整理训练结果



当用户带着训练结果回来时：

- 读取用户提供的日志、得分、实验结论

- 区分“已验证结果”和“主观判断”

- 将可确认结果同步到对应算法文档与 `GLOBAL_DOCS/算法总表.md`



如果结果不足以支持结论，明确写“暂无正式训练得分”或“暂无确定结论”。



### Step 9：信息归档



完成结果整理后：

- 把 `DEV_MEMORY/*` 中有长期价值的内容归档到 `GLOBAL_DOCS/*`

- 更新正式算法文档

- 更新算法总表

- 归档完成后重置 `DEV_MEMORY`



### Step 10：最终版本收口



归档完成后再做一次版本收口：

- 检查归档后的变更范围

- 提交最终文档与归档更新

- 提示用户是否需要 push



## 输出节奏



执行本 skill 时，建议按以下阶段给出阶段性汇报：



1. 当前仓库状态与推荐行动
2. 本轮目标与改动范围
3. 实现与 smoke test 结果
4. 等待用户训练
5. 训练结果整理
6. 归档与最终收口



## 规则



- 先检查当前开发状态，再决定是否开启新方向

- 若存在未完成算法且用户未明确切换方向，默认优先续做当前实现

- 必须显式向用户确认本轮算法或改动方向

- 不虚构训练结果

- 不跳过最小验证

- 不自动 push

- 归档完成后必须重置 `DEV_MEMORY`

- 若流程进行到“等待训练结果”阶段，必须停住，不要假装训练已完成