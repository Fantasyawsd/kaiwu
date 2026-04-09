# Gorge Chase 仓库地图（供工作流 skill 使用）

本参考文档用于 `kaiwu-rl-iteration` 工作流 skill，只保留编排阶段真正需要知道的仓库事实。更细的当前算法解析交给 `/kaiwu-rl-current-algo`，更细的实验运行说明交给 `/kaiwu-rl-run-experiment`。

## 1. 工作流最先关心的仓库事实

- 顶层入口：`README.md`、`AGENTS.md`
- 训练烟测入口：`train_test.py`
- 平台算法入口：`conf/app_conf_gorge_chase.toml`
- 算法映射：`conf/algo_conf_gorge_chase.toml`
- 系统训练配置：`conf/configure_app.toml`
- 环境配置：`agent_ppo/conf/train_env_conf.toml`、`agent_diy/conf/train_env_conf.toml`
- 工作进度文档：`工作进度.md`
- 实验记录：`实验记录.md`

## 2. 当前仓库的稳定执行事实

- 先进入容器：

```bash
docker exec -it kaiwu-dev-kaiwudrl-1 bash
```

- 最小验证命令：

```bash
python3 train_test.py
```

- 常见算法名：`ppo` / `diy`

## 3. 工作流如何分工

### 当前算法快照

交给：

```text
/kaiwu-rl-current-algo
```

### 新算法候选调研

交给：

```text
/kaiwu-rl-research-algo
```

### 实验执行

交给：

```text
/kaiwu-rl-run-experiment
```

### 运行中监控

交给：

```text
/monitor-experiment
```

### 结果分析

交给：

```text
/analyze-results
```

## 4. 工作流阶段应该始终记录什么

- work item / 轮次 ID
- 当前状态
- 当前分支名
- HEAD commit
- baseline commit
- 本轮主假设
- 最小验证是否通过
- 结果对应的日志/记录位置
- 阻塞项
- 下一步

其中：
- `工作进度.md` 负责记录状态、计划、阻塞、决策
- `实验记录.md` 负责记录实验细节、指标和结果摘要

## 5. 适合作为首轮优化方向的模块

如果需要快速定位最值得改的位置，通常优先查看：

- `agent_ppo/feature/preprocessor.py`
- `agent_ppo/feature/definition.py`
- `agent_ppo/algorithm/algorithm.py`
- `agent_ppo/model/model.py`
- `agent_ppo/workflow/train_workflow.py`

但具体“该改什么”应由 `/kaiwu-rl-research-algo` 输出，而不是工作流自己拍脑袋决定。
