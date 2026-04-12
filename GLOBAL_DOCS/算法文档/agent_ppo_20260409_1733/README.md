# agent_ppo 算法文档

**文档版本**：agent_ppo_20260409_1733  
**记录日期**：2026-04-09  
**当前状态**：已实现，历史基线，smoke test 通过，暂无正式训练得分

---

## 1. 算法概述

`agent_ppo` 是 Gorge Chase（峡谷追猎）赛题的 PPO 基线实现。

- 任务目标：控制鲁班七号在 128×128 栅格地图中躲避怪物、收集宝箱，尽量存活到最大步数（1000 步）。
- 算法框架：Proximal Policy Optimization（PPO），Actor-Critic 结构，基于策略梯度。
- 初始基线特点：
  - 40 维结构化特征
  - 8 维移动动作（未接入环境原生 16 维，闪现未启用）
  - 三层即时奖励 + 终局奖励
  - GAE 优势估计
  - Legal action masking
  - 轻量探索奖励

---

## 2. 代码入口链路

```text
train_test.py
  └─ run_train_test(algorithm_name="ppo", ...)
       └─ conf/app_conf_gorge_chase.toml        # 平台算法选择：algo = "ppo"
       └─ conf/algo_conf_gorge_chase.toml       # 算法映射
               actor_agent   = "agent_ppo.agent.Agent"
               learner_agent = "agent_ppo.agent.Agent"
               train_workflow = "agent_ppo.workflow.train_workflow.workflow"
       └─ conf/configure_app.toml               # 系统训练配置
       └─ agent_ppo/conf/conf.py                # 超参数
       └─ agent_ppo/conf/train_env_conf.toml    # 环境配置
```

最小验证命令（容器内执行）：

```bash
python3 train_test.py
```

---

## 3. Agent 接口

文件：`agent_ppo/agent.py`

| 方法 | 说明 |
| --- | --- |
| `reset(env_obs=None)` | 每局开始时重置 Preprocessor 状态和 last_action |
| `observation_process(env_obs)` | 调用 `Preprocessor.feature_process`，返回 `(ObsData, remain_info)` |
| `predict(list_obs_data)` | 随机采样动作（训练/探索），返回 `[ActData]` |
| `exploit(env_obs)` | 贪心选择动作（评估），返回 int 动作 |
| `learn(list_sample_data)` | 调用 `Algorithm.learn`，执行 PPO 更新 |
| `save_model(path, id)` | 保存模型到 `{path}/model.ckpt-{id}.pkl` |
| `load_model(path, id)` | 加载模型；训练时传 `id="latest"` |
| `action_process(act_data, is_stochastic)` | 解包 `ActData`，更新 `last_action`，返回 int 动作 |

推理流程：

```python
feature, legal_action, reward = preprocessor.feature_process(env_obs, last_action)
logits, value, prob = _run_model(feature, legal_action)
action = _legal_sample(prob, use_max=False)
d_action = _legal_sample(prob, use_max=True)
```

---

## 4. 特征处理

文件：`agent_ppo/feature/preprocessor.py`

### 4.1 特征向量（40 维）

| 分组 | 维度 | 内容 |
| --- | --- | --- |
| 英雄自身 | 4 | `hero_x_norm, hero_z_norm, flash_cd_norm, buff_remain_norm` |
| 怪物 1 | 5 | `is_in_view, m_x_norm, m_z_norm, m_speed_norm, dist_norm` |
| 怪物 2 | 5 | 同上（不可见时全 0，dist_norm=1） |
| 局部地图 | 16 | 中心 4×4 格子的障碍物标志（0/1） |
| 合法动作掩码 | 8 | 8 维移动动作是否合法（0/1） |
| 进度特征 | 2 | `step_norm, survival_ratio` |

归一化常量：地图尺寸 128，最大闪现冷却 2000，怪物速度 5，buff 持续 50。

### 4.2 Legal Action Masking

- 从观测中提取合法动作列表
- 只保留前 8 个（索引 0-7，移动动作）；闪现动作（8-15）不使用
- 若合法动作为空，默认全部合法

### 4.3 即时奖励（三层叠加）

```python
reward = survive_reward + dist_shaping + explore_bonus
```

| 分量 | 说明 | 参数 |
| --- | --- | --- |
| `survive_reward` | 每步固定生存奖励 | `SURVIVE_REWARD = 0.01` |
| `dist_shaping` | 与最近怪物归一化距离的变化量 | `DIST_SHAPING_COEF = 0.1` |
| `explore_bonus` | 进入较少访问粗粒度格子时的奖励 | `EXPLORE_BONUS_SCALE = 0.02` |

探索奖励参数：

- 网格大小：`EXPLORE_BONUS_GRID_SIZE = 16`
- 新颖度公式：`1 / sqrt(visit_count)`
- 最小阈值：`EXPLORE_BONUS_MIN_RATIO = 0.25`
- 仅在格子变化时触发

### 4.4 终局奖励

文件：`agent_ppo/workflow/train_workflow.py`

```python
if terminated:
    final_reward[0] = -10.0
else:
    final_reward[0] = +10.0
```

最终步的 reward 叠加终局奖励：`collector[-1].reward += final_reward`

---

## 5. 样本结构与 GAE

文件：`agent_ppo/feature/definition.py`

### 5.1 数据类

```python
ObsData  = (feature: list[40], legal_action: list[8])
ActData  = (action: list[1], d_action: list[1], prob: list[8], value: array[1])
SampleData = (obs[40], legal_action[8], act[1], reward[1], reward_sum[1],
              done[1], value[1], next_value[1], advantage[1], prob[8])
```

### 5.2 GAE 计算

```python
delta = -value + reward + gamma * next_value * (1 - done)
gae   = gae * gamma * lambda * (1 - done) + delta
advantage = gae
reward_sum = gae + value
```

参数：`GAMMA = 0.99`，`LAMDA = 0.95`

---

## 6. 模型结构

文件：`agent_ppo/model/model.py`，模型名：`gorge_chase_lite`

### 6.1 结构化编码器

```text
输入(40维) -> 按 [4, 5, 5, 16, 8, 2] 拆分
    hero_feat(4)       -> hero_encoder    -> 16
    monster_1+2(5+5)   -> monster_encoder -> 32
    map_feat(16)       -> map_encoder     -> 32
    legal+progress(10) -> control_encoder -> 16
                                         ↓ concat -> 96
                             backbone(FC 96->64) -> ReLU -> 64
                             ↙                        ↘
                   actor_head(64->8)          critic_head(64->1)
```

所有线性层使用正交初始化。

### 6.2 推理模式

- 训练时：`model.train()`
- 推理时：`model.eval()`，`torch.no_grad()` 下执行

---

## 7. PPO 算法

文件：`agent_ppo/algorithm/algorithm.py`

### 7.1 Loss 组成

```text
total_loss = vf_coef × value_loss + policy_loss - beta × entropy_loss
```

Policy Loss（PPO Clip）：

```python
ratio = new_prob / old_action_prob
policy_loss = max(-ratio * adv, -clamp(ratio, 1-ε, 1+ε) * adv).mean()
```

Value Loss（Clipped）：

```python
value_clip = old_value + clamp(value_pred - old_value, -ε, +ε)
value_loss = 0.5 × max((tdret - value_pred)^2, (tdret - value_clip)^2).mean()
```

Entropy Loss：

```python
entropy_loss = (-prob * log(prob)).sum(1).mean()
```

### 7.2 优化过程

1. 若 `USE_ADVANTAGE_NORM=True`，对 advantage 做 batch 归一化
2. 前向计算 `(logits, value_pred)`
3. 计算 total_loss
4. 计算 `approx_kl`；若超过 `TARGET_KL=0.02` 则跳过本次更新
5. `total_loss.backward()`
6. 梯度裁剪：`clip_grad_norm_(params, 0.5)`
7. `optimizer.step()`

### 7.3 熵系数衰减

```python
beta = BETA_START + (BETA_END - BETA_START) * min(train_step / BETA_DECAY_STEPS, 1.0)
```

从 `0.001` 线性衰减到 `0.0002`，在 2000 步内完成。

---

## 8. 训练 Workflow

文件：`agent_ppo/workflow/train_workflow.py`

### 8.1 主流程

```python
workflow(envs, agents, ...)
    usr_conf = read_usr_conf("agent_ppo/conf/train_env_conf.toml")
    while True:
        for g_data in episode_runner.run_episodes():
            agent.send_sample_data(g_data)
            if 30min elapsed:
                agent.save_model()
```

### 8.2 Episode 流程

```text
env.reset(usr_conf)
agent.reset()
agent.load_model(id="latest")
observation_process() -> obs_data

loop:
    predict(obs_data) -> act_data
    action_process(act_data) -> act
    env.step(act) -> (env_reward, env_obs)
    observation_process(env_obs) -> next_obs_data
    build SampleData frame
    if done:
        add final_reward
        sample_process(collector)
        yield collector
        break
    obs_data = next_obs_data
```

### 8.3 监控上报

Episode 结束时上报：

- `reward`
- `episode_steps`
- `episode_cnt`

训练时上报：

- `total_loss`
- `value_loss`
- `policy_loss`
- `entropy_loss`
- `reward`

---

## 9. 超参数汇总

文件：`agent_ppo/conf/conf.py`

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `FEATURE_LEN` | 40 | 特征向量总维度 |
| `ACTION_NUM` | 8 | 动作空间（仅移动，未接入闪现） |
| `VALUE_NUM` | 1 | 价值头数量 |
| `GAMMA` | 0.99 | 折扣因子 |
| `LAMDA` | 0.95 | GAE λ |
| `INIT_LEARNING_RATE_START` | 3e-4 | Adam 初始学习率 |
| `CLIP_PARAM` | 0.2 | PPO clip ε |
| `VF_COEF` | 1.0 | 价值损失权重 |
| `GRAD_CLIP_RANGE` | 0.5 | 梯度裁剪范围 |
| `USE_ADVANTAGE_NORM` | True | 是否归一化 advantage |
| `ADVANTAGE_NORM_EPS` | 1e-8 | 归一化 eps |
| `TARGET_KL` | 0.02 | KL early stopping 阈值 |
| `BETA_START` | 0.001 | 熵系数初始值 |
| `BETA_END` | 0.0002 | 熵系数终止值 |
| `BETA_DECAY_STEPS` | 2000 | 熵系数衰减步数 |
| `SURVIVE_REWARD` | 0.01 | 生存奖励 |
| `DIST_SHAPING_COEF` | 0.1 | 距离 shaping 系数 |
| `ENABLE_EXPLORE_BONUS` | True | 是否启用探索奖励 |
| `EXPLORE_BONUS_SCALE` | 0.02 | 探索奖励系数 |
| `EXPLORE_BONUS_GRID_SIZE` | 16 | 探索网格数 |
| `EXPLORE_BONUS_MIN_RATIO` | 0.25 | 探索奖励阈值 |

---

## 10. 环境配置

文件：`agent_ppo/conf/train_env_conf.toml`

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `map` | [1..10] | 训练地图列表 |
| `map_random` | false | 不随机选图 |
| `treasure_count` | 10 | 宝箱数量 |
| `buff_count` | 2 | 加速 buff 数量 |
| `buff_cooldown` | 200 | buff 刷新冷却步数 |
| `talent_cooldown` | 100 | 闪现技能冷却步数 |
| `monster_interval` | 300 | 第二只怪物出现步数 |
| `monster_speedup` | 500 | 怪物加速时间步数 |
| `max_step` | 1000 | 每局最大步数 |

系统训练配置（`conf/configure_app.toml`）：

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `replay_buffer_capacity` | 10000 | 样本池容量 |
| `preload_ratio` | 1.0 | 触发训练的样本池比例 |
| `train_batch_size` | 2048 | 训练批大小 |
| `dump_model_freq` | 100 | 模型保存频率 |
| `model_file_sync_per_minutes` | 1 | 模型同步频率 |

---

## 11. 已知限制

1. 动作空间只用 8 维：环境原生 16 维，但当前 `ACTION_NUM=8`，未接入闪现。
2. 奖励分两层：即时奖励在 `preprocessor.py`，终局奖励在 `workflow/train_workflow.py`。
3. 探索奖励按格子计数：每局重置，对稀疏奖励场景可能效果有限。
4. 无正式训练得分：截至文档编写时，仅完成 smoke 验证。

---

## 12. 实验记录引用

| 实验 ID | 类型 | 状态 | 说明 |
| --- | --- | --- | --- |
| smoke-001 | smoke test | 历史记录 | 该历史基线 smoke test 通过；正式实验结果待补充 |

---

## 13. 官方训练与评估截图归档

- 截图存放目录：`GLOBAL_DOCS/算法文档/agent_ppo_20260409_1733/screenshots/`
- 训练截图来源：平台官方训练监控，由人手动截图后放入该目录
- 评估截图来源：官网模型评估最终结果页，由人手动截图后放入同一目录
- 建议归档内容：优先保留能说明训练趋势和最终结果的关键页面，例如奖励曲线、episode 表现、算法指标、环境指标、对局指标，以及最终评估结果页
- 当前状态：待补充正式训练监控截图与官方评估结果截图

---

## 14. 官网模型评估记录

- 模型上传命名规则：严格使用 `算法完整名 + 训练步数`，建议写成 `agent_ppo_20260409_1733_<训练步数>`
- 评估要求：在官网上传模型后，对开放 10 张地图执行 5 次官方评估
- 归档要求：正式算法文档中记录 5 次评估对应的任务信息、10 张地图得分和最终采用结果
- 结果截图位置：与训练截图相同，统一放在 `GLOBAL_DOCS/算法文档/agent_ppo_20260409_1733/screenshots/`
- 当前状态：待补充官方评估结果

---

## 15. 后续优化方向（供参考）

- 扩展动作空间接入闪现（ACTION_NUM: 8 -> 16）
- 更精细的奖励设计（宝箱收集、buff 获取）
- 更复杂的特征（目标相对方向、历史轨迹）
- 网络结构改进（LSTM、attention）
- 超参数调优（学习率调度、clip 范围）
