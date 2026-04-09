# Gorge Chase 实验运行手册

本参考文档用于 `kaiwu-rl-run-experiment`，把当前 Gorge Chase 仓库的实验运行方法固定下来，避免每次重新摸索入口。

## 1. 最小烟测入口

当前仓库的最小验证入口是：

```bash
python3 train_test.py
```

这通常需要先进入 Docker 容器：

```bash
docker exec -it kaiwu-dev-kaiwudrl-1 bash
```

## 2. 当前仓库没有的东西

当前仓库没有发现：

- 独立 `pytest` 主流程
- 独立 `unittest` 主流程
- 统一 `lint` / `build` 主流程

因此，“先跑 `python3 train_test.py`”是最稳妥的最小验证方式。

## 3. 需要联动检查的文件

### 算法切换

- `train_test.py`
- `conf/app_conf_gorge_chase.toml`
- `conf/algo_conf_gorge_chase.toml`

### 系统训练配置

- `conf/configure_app.toml`

### 环境配置

- `agent_ppo/conf/train_env_conf.toml`
- `agent_diy/conf/train_env_conf.toml`

### 监控项

- `agent_ppo/conf/monitor_builder.py`

## 4. 运行一个候选方案时的建议顺序

1. 确认 Git 分支与 commit
2. 确认当前候选对应的改动文件
3. 确认 work item / 轮次 ID 与 `工作进度.md` 位置
4. 在 `工作进度.md` 中写入当前计划和状态
5. 进入容器
6. 跑 `python3 train_test.py`
7. 回填 smoke test 结果与日志位置
8. 若 smoke test 通过，再决定是否发起长实验
9. 长实验尽量复用 `/run-experiment`
10. 运行中用 `/monitor-experiment`
11. 结束后用 `/analyze-results`
12. 更新 `工作进度.md`
13. 更新 `实验记录.md`

## 5. 建议记录的指标

- `reward`
- `total_loss`
- `policy_loss`
- `value_loss`
- `entropy_loss`
- `sim_score` / `total_score`
- `total_reward`
- `episode_steps`
- `result`

## 6. 实验阶段如何回填进度文档

实验阶段至少更新 `工作进度.md` 中的以下字段：

- work item / 轮次 ID
- 当前状态：
  - `RUNNING_SMOKE`
  - `RUNNING_FORMAL`
  - `BLOCKED`
  - `REVIEW`
- 本阶段命令
- 日志位置
- 结果文件位置
- 是否通过
- 下一步
- 对应 `实验记录.md` 条目

推荐做法：
- smoke test 开始前先把状态改为 `RUNNING_SMOKE`
- smoke test 结束后写明 PASS / FAIL
- 长实验启动前改为 `RUNNING_FORMAL`
- 若环境或命令阻塞，改为 `BLOCKED`
- 实验结束等待分析时改为 `REVIEW`

## 7. 常见错误

- 直接跑长实验，没先 smoke test
- `train_test.py` 里的 `algorithm_name` 和平台 `algo` 不一致
- 修改了 `configure_app.toml` 却忘了记录
- 只看 reward，不看 `sim_score`
- 没有记录 Git commit，结果后面无法对齐到代码版本
- 只更新 `实验记录.md`，没更新 `工作进度.md`
- 没记录 work item / 轮次 ID，导致计划与结果无法串起来
