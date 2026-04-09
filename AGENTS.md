# AGENTS.md

This file provides guidance to AI assistant when working with code in this repository.

## 运行环境与入口命令

- 优先在项目要求的 Docker 容器内执行代码：
  - `docker exec -it kaiwu-dev-kaiwudrl-1 bash`
- 进入容器后使用 Python 3 运行脚本：
  - `python3 xxx.py`
- 本仓库未发现 repo-local 的 build、lint、pytest/unittest 配置；当前可验证的主入口是一次训练烟测：
  - `python3 train_test.py`
- `train_test.py` 通过 `kaiwudrl.common.utils.train_test_utils.run_train_test` 跑一次最小训练闭环；运行前需要先在 `train_test.py` 中设置：
  - `algorithm_name = "ppo"`：跑完整 PPO 基线
  - `algorithm_name = "diy"`：跑 DIY 模板
- 仓库内未提供“单个 pytest 用例”这类粒度的测试命令；最接近的单项验证方式是切换 `train_test.py` 里的 `algorithm_name`，分别对 `ppo` 或 `diy` 做一次烟测。

## 关键配置文件

- `kaiwu.json`
  - 项目标识，当前 `project_code` 为 `gorge_chase`。
- `conf/app_conf_gorge_chase.toml`
  - 选择当前启用的策略/算法；现在 `gorge_chase.policies.train_one.algo = "ppo"`。
- `conf/algo_conf_gorge_chase.toml`
  - 把算法名映射到具体 Agent 类和 workflow 入口；`ppo` 与 `diy` 都在这里注册。
- `conf/configure_app.toml`
  - 训练系统级参数：replay buffer、preload_ratio、train_batch_size、dump_model_freq、模型同步、预加载模型等。
- `agent_ppo/conf/train_env_conf.toml`
- `agent_diy/conf/train_env_conf.toml`
  - 环境配置入口；`workflow` 会在 `env.reset()` 前读取这里的 `usr_conf`。

## 代码结构总览

仓库本质上是一个腾讯开悟（KaiWuDRL）强化学习代码包，核心不是“独立 Python 应用”，而是“交给平台/容器加载的 Agent 实现”。很多导入如 `kaiwudrl`、`common_python`、`tools` 来自平台运行环境，不在本仓库内。

### 1 `agent_ppo/`：完整可运行的 PPO 基线

这是理解项目的主线，改训练逻辑时通常应先读这一套实现：

- `agent_ppo/agent.py`
  - Agent 主类，组合 `Model`、`Algorithm`、`Preprocessor`。
  - 负责 `observation_process / predict / exploit / learn / save_model / load_model / action_process`。
- `agent_ppo/feature/preprocessor.py`
  - 把环境返回的原始观测变成模型输入与即时奖励。
  - 当前会构造 **40 维特征**：英雄自身、两只怪物、局部地图、合法动作、进度特征。
- `agent_ppo/feature/definition.py`
  - 定义 `ObsData`、`ActData`、`SampleData`，并在 `sample_process()` 中计算 GAE 与 `reward_sum`。
- `agent_ppo/model/model.py`
  - 一个共享 MLP 骨干 + actor/critic 双头的 PyTorch 模型。
- `agent_ppo/algorithm/algorithm.py`
  - PPO 更新逻辑，包含 masked softmax、policy clip、value clip、entropy regularization。
- `agent_ppo/workflow/train_workflow.py`
  - 训练主循环：读环境配置、reset 环境、调用 agent 预测动作、收集轨迹、做 `sample_process()`、把样本发给 learner、定期保存模型。

### 2 `agent_diy/`：DIY 模板

- 目录结构与 `agent_ppo/` 对齐，但大部分核心方法仍是 `pass` 或模板代码。
- 如果用户要求“基于现有可运行逻辑修改”，优先参考 `agent_ppo/`；`agent_diy/` 更适合从零自定义。

### 3 `开发文档/`：文档主入口

这部分很重要，很多环境/协议/平台行为不在代码里，而在文档里：

- `开发文档/README.md`
  - 面向 AI 的文档索引，适合先读。
- `开发文档/开发文档.md`
  - 汇总版总文档。
- `开发文档/开发指南/环境详述.md`
  - 环境配置、`env.reset` / `env.step` 返回、动作空间。
- `开发文档/开发指南/数据协议.md`
  - observation / extra_info / EnvInfo / FrameState 等字段定义。
- `开发文档/腾讯开悟强化学习框架/综述.md`
  - 框架总览，解释 Agent / workflow / 分布式训练闭环。

处理“环境字段含义”“协议字段”“平台配置”的问题时，先查 `开发文档/README.md`，再跳到对应分文档，不要只凭代码猜。

## 必须先理解的跨文件关系

### 1 训练闭环是如何串起来的

1. `train_test.py` 调 `run_train_test(...)` 做一次最小训练验证。
2. 框架根据 `conf/app_conf_gorge_chase.toml` 和 `conf/algo_conf_gorge_chase.toml` 决定当前算法名、Agent 类和 workflow。
3. `agent_ppo/workflow/train_workflow.py` 读取 `agent_ppo/conf/train_env_conf.toml`，并驱动环境交互。
4. `agent_ppo/agent.py` 调 `Preprocessor` 把原始观测转成 `ObsData`，再调用 `Model` 推理动作，用 `Algorithm` 做学习。
5. `agent_ppo/feature/definition.py` 在 episode 结束后把轨迹补成带 GAE 的训练样本。
6. `agent_ppo/algorithm/algorithm.py` 用这些样本做 PPO 更新。

### 2 当前 PPO 基线只用了 8 维动作，不是环境原生 16 维

这是本仓库最容易看漏的点之一：

- 文档里的环境原生动作空间是 **16 维**：8 个移动 + 8 个闪现。
- 但当前基线在 `agent_ppo/conf/conf.py` 里设定 `ACTION_NUM = 8`。
- `agent_ppo/feature/preprocessor.py` 也只保留前 8 个合法动作。
- `agent_ppo/model/model.py` 的 actor head 只输出 8 个 logits。

也就是说，当前 PPO 基线实际上只学“8 方向移动”，没有把闪现动作接进策略网络。若要扩展动作空间，需要同时改 `Config`、preprocessor、模型输出维度、采样逻辑以及相关数据定义。

### 3 奖励分两层：即时 shaping 在 preprocessor，终局奖励在 workflow

- `agent_ppo/feature/preprocessor.py`
  - 每步即时奖励由“生存奖励 + 与怪物距离变化 shaping”组成。
- `agent_ppo/workflow/train_workflow.py`
  - episode 结束时再额外加终局奖励：
    - `terminated`（被抓）时加 `-10`
    - `truncated`（达到最大步数等）时加 `+10`

分析训练表现时要同时看这两层，不要只在单个文件里找完整 reward 逻辑。

## 修改代码时的实用判断

- 想改特征、合法动作、reward shaping：先看 `agent_ppo/feature/preprocessor.py`
- 想改样本结构、GAE、回报计算：先看 `agent_ppo/feature/definition.py`
- 想改网络结构：看 `agent_ppo/model/model.py`
- 想改 PPO loss / 优化过程：看 `agent_ppo/algorithm/algorithm.py`
- 想改 episode 驱动、何时加载/保存模型、监控上报：看 `agent_ppo/workflow/train_workflow.py`
- 想切换当前平台使用的算法实现：看 `conf/app_conf_gorge_chase.toml` + `conf/algo_conf_gorge_chase.toml`
- 想改训练环境参数：看对应 `agent_*/conf/train_env_conf.toml`

