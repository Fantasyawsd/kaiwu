# KaiWu 训练日志来源与格式

## 本地日志目录

- 本地训练日志根目录：`train/log/`
- 子目录按模块拆分：
  - `train/log/learner`
  - `train/log/aisrv`
  - `train/log/kaiwu_env`

`train/.env` 中的 `KAIWU_TRAIN_LOG=./log` 会被 docker compose 挂载到容器内 `/workspace/log`。

## 日志文件格式

- 每行一个 JSON 对象，也就是 JSONL。
- 常见字段：
  - `time`
  - `level`
  - `message`
  - `file`
  - `line`
  - `module`
  - `process`
  - `function`
  - `stack`
  - `pid`

真正需要画曲线的训练指标，很多并不在 JSON 顶层，而是塞在 `message` 字符串里，需要二次解析。

## 各模块可提取指标

### learner

主要来源：

- `agent_ppo/algorithm/algorithm.py`
- `learner_train_*.log`

可提取：

- `total_loss`
- `policy_loss`
- `value_loss`
- `entropy`
- `approx_kl`
- `beta`
- `train_count`
- `global_step`
- `train_ms`
- `data_fetch_ms`
- `real_train_ms`
- `sample_ratio`
- `buffer_utilization`
- `skip update due to approx_kl`

### aisrv

主要来源：

- `agent_ppo/workflow/train_workflow.py`
- `aisrv_kaiwu_rl_helper_*.log`

可提取：

- `episode`
- `steps`
- `result`
- `sim_score`
- `total_reward`

这里的 `sim_score` 更接近任务真实表现，通常比训练 reward 更值得重点关注。

### kaiwu_env

主要来源：

- `env_*_log_*.log`
- `monitor_helper.py` 输出的 `finish monitor_data`

可提取：

- `finished_steps`
- `total_score`
- `step_score`
- `treasure_score`
- `treasures_collected`
- `flash_count`
- 其他环境完成态指标

这里嵌入的是 Python 字典字符串，不是标准 JSON，需要用 `ast.literal_eval` 一类方式再解析。

## 优先级建议

做训练分析时，推荐优先级如下：

1. `learner`：看优化是否稳定
2. `aisrv`：看 episode 表现是否真的变好
3. `kaiwu_env`：做环境侧交叉验证

如果三者冲突：

- 先保留冲突
- 标注证据
- 不要凭直觉挑一个“看起来对”的结论
