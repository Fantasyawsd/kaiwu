---
name: kaiwu-train-analysis
description: Analyze KaiWu Gorge Chase training logs, generate structured CSV metrics and curve plots, summarize learner and episode behavior, and provide concrete next-step tuning advice. Use when a user wants to inspect training logs, reward curves, loss curves, episode score trends, or platform training outcomes.
argument-hint: [training-log-path-or-result-summary]
allowed-tools: Read, Grep, Glob, Edit, Write
---

# KaiWu Train Analysis

## 目标

把 KaiWu 训练日志从“人难以直接阅读的 JSONL + message 字符串”转换成可分析产物：

- 结构化 CSV
- 训练总览曲线图
- 摘要报告
- 基于指标的诊断与下一轮建议

默认优先分析本仓库的本地训练日志目录：`train/log/`。

## 必读来源

先确认日志与指标语义，再开始解释曲线：

1. `开发文档/README.md`
2. `开发文档/开发文档.md`
3. `references/log-sources.md`
4. `agent_ppo/workflow/train_workflow.py`
5. `agent_ppo/algorithm/algorithm.py`
6. `agent_ppo/conf/monitor_builder.py`

## 执行流程

### Step 1：先跑日志分析脚本

优先运行：

```bash
python code/.claude/skills/kaiwu-train-analysis/scripts/analyze_kaiwu_train_logs.py --log-root train/log
```

默认行为：

- 自动从 learner 日志里定位“最新一轮训练启动时间”
- 只分析这轮训练之后的日志
- 导出 CSV、PNG、Markdown、JSON 到 `train/analysis/<run-label>/`

常用变体：

```bash
python code/.claude/skills/kaiwu-train-analysis/scripts/analyze_kaiwu_train_logs.py --log-root train/log --all-history
python code/.claude/skills/kaiwu-train-analysis/scripts/analyze_kaiwu_train_logs.py --log-root train/log --start-time 2026-04-10T14:56:44
python code/.claude/skills/kaiwu-train-analysis/scripts/analyze_kaiwu_train_logs.py --log-root train/log --start-time 2026-04-10T14:56:44 --end-time 2026-04-10T15:27:15
```

### Step 2：先看脚本产物，再做判断

重点读取：

- `summary.md`
- `summary.json`
- `training_overview.png`
- `learner_train_metrics.csv`
- `learner_step_metrics.csv`
- `aisrv_episode_metrics.csv`
- `env_episode_metrics.csv`

不要直接靠原始日志逐行人工判断，除非需要排查异常栈或极个别 episode。

### Step 3：按模块解释指标

#### 3.1 Learner

重点看：

- `total_loss`
- `value_loss`
- `policy_loss`
- `entropy`
- `approx_kl`
- `train_ms`
- `sample_ratio`
- `skip update` 次数

判断重点：

- loss 是否总体下降并逐步稳定
- `approx_kl` 是否经常顶到阈值导致跳过更新
- 单步训练耗时是否异常升高
- `sample_ratio` 是否失衡

#### 3.2 AISrv

重点看：

- `sim_score`
- `total_reward`
- `steps`
- `rolling_win_rate_100`

判断重点：

- `sim_score` 是否比 reward 更接近真实任务表现
- episode score 是否明显上升
- reward 与 sim_score 是否背离
- 存活步数是否增长
- 是否长期 0 胜率或几乎全 FAIL

#### 3.3 Kaiwu Env

重点看：

- `total_score`
- `finished_steps`
- `treasures_collected`
- 其他 `monitor_data`

判断重点：

- 是否和 AISrv 的 episode 结果相互印证
- 是否存在环境行为异常或配置异常
- env 记录是否明显稀疏，如果稀疏则以 AISrv 为主

### Step 4：形成诊断

至少回答下面几个问题：

1. 这轮训练有没有学到东西？
2. 学到的是 reward，还是更接近真实任务分数的行为？
3. 训练是稳定收敛，还是震荡、过早饱和、被 KL 限制住？
4. 当前问题更像是奖励设计问题、特征问题、超参问题，还是环境配置问题？
5. 下一轮最应该只改哪一个主方向？

### Step 5：需要时再更新项目文档

如果用户明确要求归档或同步状态，再更新：

- `DEV_MEMORY/NOW.md`
- `GLOBAL_DOCS/算法总表.md`
- 对应算法文档

默认不要在没有证据的情况下把这一轮训练写成“有效改进”。

## 输出要求

最终分析应包含：

```markdown
## 训练结果分析：<run-name>

### 1. 基本信息
- 日志路径：
- 训练时间窗口：
- learner 全局步数：
- episode 数：

### 2. 关键曲线结论
- loss：
- sim_score：
- total_reward：
- episode_steps：

### 3. 问题诊断
- 主要问题：
- 证据：
- 最可能原因：

### 4. 与真实任务表现的关系
- reward 和 sim_score 是否一致：
- 是否可能“奖励变好但任务没变好”：

### 5. 下一轮建议
- 只改一个主方向：
- 预期观察指标：
- 不建议改动的部分：
```

## 规则

- 先跑脚本，后读图和 CSV，再下结论。
- 区分 `reward` 和 `sim_score/total_score`，不要混为一谈。
- 若多轮训练混在一起，必须用 `--start-time` 或最新 run 自动检测来收窄窗口。
- 若脚本产物与原始日志矛盾，以原始日志为准并明确标注矛盾点。
- 给出建议时必须落到可执行项，例如具体参数、文件或奖励项，而不是泛泛而谈。
