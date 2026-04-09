# KaiWu 当前算法快照：最小文件集合

本参考文档用于 `kaiwu-rl-current-algo` skill，在 KaiWu / KaiWuDRL 仓库中快速判断当前 baseline。

## 1. 最小文件集合

按优先级读取：

1. `README.md`
2. `AGENTS.md`
3. `kaiwu.json`
4. `train_test.py`
5. `conf/app_conf_gorge_chase.toml` 或其他 `conf/app_conf*.toml`
6. `conf/algo_conf_gorge_chase.toml` 或其他 `conf/algo_conf*.toml`
7. `conf/configure_app.toml`
8. `agent_ppo/conf/train_env_conf.toml`
9. `agent_diy/conf/train_env_conf.toml`

## 2. 每个文件回答什么问题

### `train_test.py`

回答：
- 最小烟测入口是什么
- `algorithm_name` 当前设置成什么
- `run_train_test(...)` 中是否存在临时 `env_vars` 覆盖

### `conf/app_conf*.toml`

回答：
- 当前平台真正启用的 `algo` 是什么

### `conf/algo_conf*.toml`

回答：
- 这个算法映射到哪个 Agent 类
- 对应哪个 workflow

### `conf/configure_app.toml`

回答：
- replay buffer、batch size、model dump、preload 等系统级训练配置是什么

### `agent_*/conf/train_env_conf.toml`

回答：
- 当前算法对应的环境配置是什么
- 地图、怪物、最大步数等关键环境参数是什么

### `kaiwu.json`

回答：
- 当前项目 `project_code` 是什么

## 3. Gorge Chase 仓库中的稳定事实

在当前比赛仓库中，通常应得到以下结论：

- 最小验证入口：`python3 train_test.py`
- 运行环境：先进入 Docker 容器
- 容器命令：`docker exec -it kaiwu-dev-kaiwudrl-1 bash`
- 常见算法候选：`ppo` / `diy`
- 当前平台算法配置一般在 `conf/app_conf_gorge_chase.toml`

## 4. 输出时必须主动检查的不一致

- `train_test.py` 的 `algorithm_name` 与 `conf/app_conf*.toml` 的 `algo` 是否一致
- `conf/algo_conf*.toml` 是否真的存在该算法映射
- 对应 `agent_*/conf/train_env_conf.toml` 是否存在
- README / AGENTS 中写的最小命令是否与代码入口一致

## 5. 输出边界

这个 skill 只回答：
- 当前是什么
- 当前怎么跑
- 当前配置在哪里

这个 skill 不回答：
- 下一步该怎么优化
- 哪种新算法更好
- 是否应该改 reward / 特征 / 模型
