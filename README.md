# Gorge Chase KaiWuDRL 强化学习项目

本项目是腾讯开悟（KaiWuDRL）“峡谷追猎 / Gorge Chase”强化学习代码包，用于训练控制鲁班七号在 128×128 栅格地图中躲避怪物、收集宝箱并尽量存活到最大步数的智能体。

项目当前包含两套智能体实现：

- `agent_ppo/`：完整 PPO 基线实现，可作为主要训练与改造对象。
- `agent_diy/`：DIY 模板，保留与基线一致的目录结构，但核心方法多为待实现模板。

## 快速开始

建议在项目指定的 Docker 容器中运行代码：

```bash
docker exec -it kaiwu-dev-kaiwudrl-1 bash
```

进入容器后，在代码目录中使用 Python 3 运行脚本：

```bash
python3 train_test.py
```

`train_test.py` 会调用 KaiWuDRL 框架提供的 `run_train_test`，执行一次最小训练闭环，用于在正式训练前做代码正确性烟测。

## Claude Code / KaiWu skills 使用约定

如需借助 Claude Code 完成本仓库中的算法检查、候选调研、实验验证与持续迭代，默认应优先使用已配置好的 KaiWu 专用 skills，而不是跳过工作流直接盲改代码。

推荐使用顺序如下：

1. `/kaiwu-rl-current-algo`
   - 用途：只读检查当前 baseline。
   - 输出：当前算法、平台 algo、Agent / workflow、关键训练配置、环境配置、最小验证命令。
3. `/kaiwu-rl-run-experiment`
   - 用途：执行当前仓库的 smoke test 或正式实验。
   - 当前仓库最小验证入口：先进入容器，再执行 `python3 train_test.py`。
   - 执行阶段要求同步更新 `工作进度.md` 与 `实验记录.md`。
4. `/kaiwu-rl-iteration`
   - 用途：把 Git baseline、当前算法快照、候选选择、实现、实验、分析、提交与停止条件组织成完整闭环。
   - 适用场景：需要持续迭代优化，而不是只做一次性修改时。

配套 skills：

- `/analyze-results`：分析日志、结果文件与实验记录，判断是否优于 baseline。

默认规则：

- 先 `/kaiwu-rl-current-algo`，不要直接跨过 baseline 检查。
- 先 smoke test，再长实验，不要直接启动长时间训练。
- 进入实验阶段后，必须维护双文档联动：
  - `工作进度.md`：记录计划、状态、阻塞、决策、下一步。
  - `实验记录.md`：记录实验细节、指标、日志位置、结论。
- 涉及多轮优化时，优先使用 `/kaiwu-rl-iteration` 统一组织流程。
- 涉及当前仓库实验任务时，不要自行发明运行入口；默认复用本 README 与 skills 中约定的容器命令和 `train_test.py` 入口。

如需切换烟测算法，修改 `train_test.py` 中的：

```python
algorithm_name = "ppo"
```

可选值：

- `ppo`：运行 `agent_ppo` 基线。
- `diy`：运行 `agent_diy` 模板。

> 当前仓库未提供独立的 pytest/unittest、lint 或 build 配置；主要验证入口是 `python3 train_test.py`。

## 项目结构

```text
.
├── agent_ppo/              # 完整 PPO 基线智能体
│   ├── agent.py            # Agent 主类：预测、训练、模型保存/加载、动作处理
│   ├── algorithm/          # PPO loss 与优化逻辑
│   ├── conf/               # PPO 超参数与训练环境配置
│   ├── feature/            # 特征处理、样本定义、GAE 计算
│   ├── model/              # PyTorch Actor-Critic 模型
│   └── workflow/           # 训练工作流：环境交互、样本收集、模型保存
├── agent_diy/              # DIY 智能体模板
├── conf/                   # 平台与训练系统级配置
├── ckpt/                   # 模型 checkpoint 相关目录
├── 开发文档/               # 官方/整理后的开发文档与 AI 查询索引
├── kaiwu.json              # 项目标识配置
├── train_test.py           # 训练烟测入口
├── 实验记录.md             # 实验方法与指标记录模板
└── AGENTS.md               # 面向 AI/Agent 工具的说明文档
```

## 关键配置

### 1 项目标识

`kaiwu.json`：

```json
{
  "version": "15.0.1-comp-normal-lite.26comp",
  "project_code": "gorge_chase"
}
```

### 2 算法与 workflow 注册

`conf/app_conf_gorge_chase.toml` 当前指定训练算法：

```toml
[gorge_chase.policies.train_one]
policy_builder = "kaiwudrl.server.aisrv.async_policy.AsyncBuilder"
algo = "ppo"
```

`conf/algo_conf_gorge_chase.toml` 负责把算法名映射到具体 Agent 与 workflow，例如：

- `ppo` → `agent_ppo.agent.Agent`、`agent_ppo.workflow.train_workflow.workflow`
- `diy` → `agent_diy.agent.Agent`、`agent_diy.workflow.train_workflow.workflow`

### 3 训练系统配置

`conf/configure_app.toml` 包含 replay buffer、batch size、模型保存频率、模型同步、预加载模型等配置，例如：

- `replay_buffer_capacity`
- `preload_ratio`
- `train_batch_size`
- `dump_model_freq`
- `model_file_sync_per_minutes`
- `preload_model`

### 4 环境配置

环境配置在各 Agent 自己的目录中：

- `agent_ppo/conf/train_env_conf.toml`
- `agent_diy/conf/train_env_conf.toml`

常见配置项包括：

- `map`
- `map_random`
- `treasure_count`
- `buff_count`
- `buff_cooldown`
- `talent_cooldown`
- `monster_interval`
- `monster_speedup`
- `max_step`

训练 workflow 会在 `env.reset()` 前读取对应的 `train_env_conf.toml`。

## PPO 基线说明

`agent_ppo/` 是当前主要可运行基线，核心流程如下：

1. `train_test.py` 调用 KaiWuDRL 的 `run_train_test`。
2. 框架根据 `conf/app_conf_gorge_chase.toml` 和 `conf/algo_conf_gorge_chase.toml` 加载算法、Agent 和 workflow。
3. `agent_ppo/workflow/train_workflow.py` 读取 `agent_ppo/conf/train_env_conf.toml`，并驱动环境交互。
4. `agent_ppo/agent.py` 调用 `Preprocessor` 处理观测，再调用 `Model` 预测动作。
5. episode 结束后，`agent_ppo/feature/definition.py` 通过 GAE 计算 advantage 和 reward_sum。
6. `agent_ppo/algorithm/algorithm.py` 执行 PPO 更新。

### 1 当前动作空间注意点

环境原生动作空间是 16 维：

- 8 个移动动作
- 8 个闪现动作

但当前 PPO 基线只使用 8 维移动动作：

- `agent_ppo/conf/conf.py` 中 `ACTION_NUM = 8`
- `agent_ppo/feature/preprocessor.py` 只保留前 8 个合法动作
- `agent_ppo/model/model.py` 的 actor head 输出 8 个 logits

如果要让模型学习闪现，需要同步修改配置、特征处理、模型输出、动作采样与样本定义。

### 2 当前奖励结构

奖励逻辑分散在两个位置：

- `agent_ppo/feature/preprocessor.py`
  - 每步即时奖励：生存奖励 + 与怪物距离变化 shaping。
- `agent_ppo/workflow/train_workflow.py`
  - 终局奖励：
    - `terminated` 时加负奖励
    - `truncated` 时加正奖励

分析训练表现或修改 reward 时，需要同时检查这两个文件。

## 开发文档索引

如需查询环境规则、动作空间、字段协议和框架接口，优先阅读：

- `开发文档/README.md`：AI 查询索引与文档导航。
- `开发文档/开发文档.md`：汇总总文档。
- `开发文档/开发指南/环境详述.md`：环境配置、reset/step 返回值、动作空间。
- `开发文档/开发指南/数据协议.md`：observation、extra_info、EnvInfo、FrameState 等字段定义。
- `开发文档/腾讯开悟强化学习框架/综述.md`：KaiWuDRL 框架总览。

## 实验记录

本项目新增了 `实验记录.md`，用于记录尝试过的方法与对应指标。建议每次实验记录：

- 核心改动
- 涉及文件
- 训练配置
- 环境配置
- `total_loss`、`policy_loss`、`value_loss`、`entropy_loss`
- `reward`、`episode_steps`、`total_reward`、`sim_score / total_score`
- 结论与下一步

## 常见修改入口

- 修改特征或 reward shaping：`agent_ppo/feature/preprocessor.py`
- 修改样本结构或 GAE：`agent_ppo/feature/definition.py`
- 修改网络结构：`agent_ppo/model/model.py`
- 修改 PPO loss：`agent_ppo/algorithm/algorithm.py`
- 修改训练循环、模型保存、监控上报：`agent_ppo/workflow/train_workflow.py`
- 修改环境参数：`agent_ppo/conf/train_env_conf.toml`
- 修改训练系统参数：`conf/configure_app.toml`
- 切换平台算法入口：`conf/app_conf_gorge_chase.toml` 与 `conf/algo_conf_gorge_chase.toml`
