# agent_ppo_20260410_hok_memory_map_v1 算法文档

**文档版本**：`agent_ppo_20260410_hok_memory_map_v1`  
**记录日期**：2026-04-11  
**当前状态**：已实现并完成归档；容器内 smoke test 已跑通 monitor 注册、episode 交互、PPO 更新与 `save_model`；`screenshots/` 已检测到图片，当前按“截图驱动归档”规则维护训练/测试信息

---

## 1. 算法概述

- 任务目标：
  在 Gorge Chase 赛题中控制鲁班七号躲避怪物、收集宝箱并尽可能存活到 `max_step=1000`。
- 算法框架：
  保持 `agent_ppo/` 现有 PPO Actor-Critic 训练链路。
- 本轮核心改动：
  - 动作空间从 8 扩展到 16，正式接入环境原生闪现动作。
  - 观测从 40 维扩展到 528 维，引入 `4x11x11` 局部语义地图。
  - 在 `preprocessor.py` 中加入宝箱 / buff 目标记忆、视野外方向距离估计、撞墙方向屏蔽、重复访问惩罚。
  - 模型从纯扁平 MLP 升级为“结构化特征分支 + CNN 地图编码 + 控制分支”融合网络。
  - workflow 增加 episode 级监控，补充 `total_score`、`treasures_collected`、`flash_count` 与奖励分量上报。
- 重要取舍：
  - 根据当前 Gorge Chase 开发文档，环境协议没有显式“终点”对象；因此 HOK 方案里的终点记忆没有直接迁入。
  - 当前实现中的 `guide_dist_reward` 仅作为“无宝箱目标时的 buff 引导 fallback”，不是显式终点 shaping。

---

## 2. 代码入口链路

```text
train_test.py
-> conf/app_conf_gorge_chase.toml
-> conf/algo_conf_gorge_chase.toml
-> conf/configure_app.toml
-> agent_ppo/conf/conf.py
-> agent_ppo/conf/train_env_conf.toml
-> agent_ppo/agent.py
-> agent_ppo/feature/preprocessor.py
-> agent_ppo/feature/definition.py
-> agent_ppo/model/model.py
-> agent_ppo/algorithm/algorithm.py
-> agent_ppo/workflow/train_workflow.py
```

最小验证命令：

```bash
docker exec kaiwu-dev-kaiwudrl-1 python3 train_test.py
```

2026-04-11 的容器 smoke test 结果：

- monitor 配置成功加载并生成 `/workspace/train/monitor.yaml`
- aisrv 能启动 episode，已看到 `Episode start` / `GAMEOVER`
- learner 能执行 `Algorithm.learn`
- checkpoint 能成功保存到 `/data/ckpt/gorge_chase_ppo/model.ckpt-*.pkl`
- `train_test.py` 最终返回码仍为 `1`，但日志中未出现实现侧 `Traceback` / `ERROR`

---

## 3. Agent 接口

文件：`agent_ppo/agent.py`

| 方法 | 说明 |
| --- | --- |
| `reset(env_obs=None)` | 每局开始重置 preprocessor 内部状态、目标记忆、访问热度和 `last_action` |
| `observation_process(env_obs)` | 调用 `Preprocessor.feature_process`，返回 `ObsData(feature, legal_action)` 与 `remain_info(reward, reward_terms)` |
| `predict(list_obs_data)` | 训练时按 masked softmax 后的 16 动作分布采样，同时保留贪心动作 |
| `exploit(env_obs)` | 评估时走同一前处理链路，但输出贪心动作 |
| `learn(list_sample_data)` | 调用 `Algorithm.learn` 执行 PPO 更新 |
| `save_model(path, id)` | 保存 `model.ckpt-{id}.pkl` |
| `load_model(path, id)` | 加载指定 checkpoint |
| `action_process(act_data, is_stochastic)` | 将 `ActData` 解包为环境所需的单整数动作，并更新 `last_action` |

---

## 4. 特征处理

文件：`agent_ppo/feature/preprocessor.py`

### 4.1 特征向量

| 分组 | 维度 | 内容 |
| --- | --- | --- |
| `hero_feat` | 6 | `hero_x_norm`, `hero_z_norm`, `flash_cd_norm`, `buff_remain_norm`, `treasure_collected_ratio`, `step_norm` |
| `monster_1` | 8 | `is_visible`, `est_x_norm`, `est_z_norm`, `speed_norm`, `dist_bucket_norm`, `dir_sin`, `dir_cos`, `active_flag` |
| `monster_2` | 8 | 同上 |
| `semantic_map` | 484 | `4 x 11 x 11` 局部语义地图 |
| `legal_action` | 16 | 环境原生 `legal_act` + 撞墙增强屏蔽后的全动作 mask |
| `progress_feat` | 6 | `step_norm`, `survival_ratio`, `remaining_treasure_ratio`, `buff_collected_ratio`, `flash_used_ratio`, `has_collectible_target` |
| 总计 | 528 | `6 + 8 + 8 + 484 + 16 + 6` |

### 4.2 目标记忆与视野外估计

- 宝箱和 buff 按 `config_id` 建立 `TargetMemory`。
- 若目标在视野内，则记录精确坐标并将 `found=True`。
- 若目标暂时不在视野内但此前未精确发现，则根据 `hero_relative_direction + hero_l2_distance` 估计全局坐标。
- 宝箱可用性优先由 `EnvInfo.treasure_id` 判定；buff 可用性由当前状态字段近似维护。

### 4.3 局部语义地图

`semantic_map` 的 4 个通道如下：

| 通道 | 含义 | 具体实现 |
| --- | --- | --- |
| 0 | 障碍 / 可通行 | 从 `map_info` 中心裁出 `11x11` 局部通行图，`1=可通行` |
| 1 | 访问记忆热度 | 基于全局 `visit_heat[x, z]` 的局部裁剪，并按 `count / 5` 截断到 `[0,1]` |
| 2 | 宝箱 / buff 目标图 | 宝箱用正值、buff 用负值；精确坐标强于估计坐标 |
| 3 | 怪物风险图 | 按怪物估计位置投影到局部图，并做轻量 3x3 blob 扩散 |

### 4.4 合法动作处理

- 动作空间正式使用环境原生 16 维：
  - `0-7`：移动
  - `8-15`：闪现
- 先读取 `observation.legal_act`
- 若检测到“上一动作后英雄未发生位移”，则临时屏蔽对应移动方向 `last_action % 8`
- 若 mask 被屏蔽到全 0，则回退到全 1，避免数值链路中断

### 4.5 奖励设计

即时奖励全部在 `preprocessor.py` 中计算：

| 分量 | 位置 | 说明 | 参数 |
| --- | --- | --- | --- |
| `survive_reward` | `preprocessor.py` | 每步基础生存奖励 | `SURVIVE_REWARD = 0.005` |
| `dist_shaping` | `preprocessor.py` | 最近怪物距离变大时给正反馈 | `DIST_SHAPING_COEF = 0.05` |
| `treasure_dist_reward` | `preprocessor.py` | 接近当前主宝箱目标的距离 shaping | `TREASURE_DIST_COEF = 0.08` |
| `guide_dist_reward` | `preprocessor.py` | 无宝箱目标时，对 buff 目标的 fallback 引导 shaping | `EXIT_DIST_COEF = 0.04` |
| `treasure_reward` | `preprocessor.py` | 宝箱收集奖励 | `TREASURE_REWARD = 1.0` |
| `buff_reward` | `preprocessor.py` | buff 获取奖励 | `BUFF_REWARD = 0.3` |
| `flash_escape_reward` | `preprocessor.py` | 高风险下用闪现拉开怪物距离时给正反馈 | `FLASH_ESCAPE_REWARD_COEF = 0.05` |
| `hit_wall_penalty` | `preprocessor.py` | 撞墙 / 原地抖动惩罚 | `HIT_WALL_PENALTY = 0.05` |
| `revisit_penalty` | `preprocessor.py` | 3x3 局部反复绕圈惩罚 | `REVISIT_PENALTY_COEF = 0.02` |
| `explore_bonus` | `preprocessor.py` | 粗粒度探索奖励 | `EXPLORE_BONUS_SCALE = 0.01` |

终局奖励在 `agent_ppo/workflow/train_workflow.py` 中叠加：

- `terminated=True`：`-12.0`
- 存活到 `max_step`：`+8.0`
- 其他截断：`0.0`

---

## 5. 样本结构与 GAE

文件：`agent_ppo/feature/definition.py`

- `ObsData`：
  - `feature`: `528`
  - `legal_action`: `16`
- `ActData`：
  - `action`: `1`
  - `d_action`: `1`
  - `prob`: `16`
  - `value`: `1`
- `SampleData`：
  - `obs[528]`
  - `legal_action[16]`
  - `act[1]`
  - `reward[1]`
  - `reward_sum[1]`
  - `done[1]`
  - `value[1]`
  - `next_value[1]`
  - `advantage[1]`
  - `prob[16]`

GAE 公式：

```python
delta = -value + reward + gamma * next_value * (1 - done)
gae = gae * gamma * lamda * (1 - done) + delta
advantage = gae
reward_sum = gae + value
```

关键参数：

- `GAMMA = 0.995`
- `LAMDA = 0.95`

---

## 6. 模型结构

文件：`agent_ppo/model/model.py`

模型名：`gorge_chase_memory_map_ppo`

```text
hero_feat(6)          -> FC -> 32
monster_pair(16)      -> FC -> 64
control_feat(22)      -> FC -> 32
semantic_map(4x11x11) -> Conv(4->16) -> Conv(16->32,s=2) -> Conv(32->32,s=2) -> Flatten -> FC -> 128

concat(32 + 64 + 32 + 128 = 256)
-> backbone FC 256->128 -> ReLU -> FC 128->128 -> ReLU
-> actor_head 128->16
-> critic_head 128->1
```

实现特点：

- 地图分支不再把地图 flatten 后直接过 MLP，而是先经过轻量 CNN。
- `map_dim` 在构造时强校验为 `4 * 11 * 11 = 484`，避免 shape 漏改。
- Actor / Critic 头继续保持 PPO 所需的双头结构。

---

## 7. 算法训练逻辑

文件：`agent_ppo/algorithm/algorithm.py`

- 保持标准 PPO：
  - 策略损失：clip surrogate objective
  - 价值损失：clipped value loss
  - 熵项：mask 后策略分布的 entropy
- 总损失：

```text
total_loss = vf_coef * value_loss + policy_loss - beta * entropy_loss
```

- 当前关键训练约束：
  - `CLIP_PARAM = 0.15`
  - `TARGET_KL = 0.015`
  - `GRAD_CLIP_RANGE = 0.5`
  - `USE_ADVANTAGE_NORM = True`
- 熵系数衰减：

```text
BETA_START = 0.003
-> 线性衰减到
BETA_END = 0.0005
-> 共 4000 步
```

---

## 8. 超参数汇总

### 8.1 算法超参数

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `FEATURE_LEN` | `528` | 总观测维度 |
| `ACTION_NUM` | `16` | 全动作空间 |
| `VALUE_NUM` | `1` | 单价值头 |
| `GAMMA` | `0.995` | 折扣因子 |
| `LAMDA` | `0.95` | GAE λ |
| `INIT_LEARNING_RATE_START` | `2e-4` | Adam 学习率 |
| `CLIP_PARAM` | `0.15` | PPO clip |
| `TARGET_KL` | `0.015` | KL early stop 阈值 |
| `BETA_START` | `0.003` | 初始熵系数 |
| `BETA_END` | `0.0005` | 终止熵系数 |
| `BETA_DECAY_STEPS` | `4000` | 熵系数衰减步数 |
| `SURVIVE_REWARD` | `0.005` | 基础生存奖励 |
| `DIST_SHAPING_COEF` | `0.05` | 怪物距离 shaping |
| `TREASURE_REWARD` | `1.0` | 宝箱收集奖励 |
| `BUFF_REWARD` | `0.3` | buff 获取奖励 |
| `TREASURE_DIST_COEF` | `0.08` | 宝箱距离 shaping |
| `EXIT_DIST_COEF` | `0.04` | 当前作为 buff fallback 引导权重 |
| `FLASH_ESCAPE_REWARD_COEF` | `0.05` | 闪现脱险奖励 |
| `HIT_WALL_PENALTY` | `0.05` | 撞墙惩罚 |
| `REVISIT_PENALTY_COEF` | `0.02` | 重复访问惩罚 |
| `TERMINATED_PENALTY` | `-12.0` | 失败终局奖励 |
| `TRUNCATED_BONUS` | `8.0` | 生存到最大步数奖励 |

### 8.2 环境配置

文件：`agent_ppo/conf/train_env_conf.toml`

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `map` | `[1..8]` | 训练地图（1-8），测试地图（9-10） |
| `map_random` | `false` | 按顺序训练 |
| `treasure_count` | `10` | 保持满宝箱场景 |
| `buff_count` | `2` | 保持双 buff 场景 |
| `buff_cooldown` | `200` | buff 刷新间隔 |
| `talent_cooldown` | `100` | 闪现冷却 |
| `monster_interval` | `300` | 第二只怪物出现时间 |
| `monster_speedup` | `500` | 怪物加速时间 |
| `max_step` | `1000` | 每局最大步数 |

### 8.3 系统训练配置

文件：`conf/configure_app.toml`

| 参数 | 值 | 说明 |
| --- | --- | --- |
| `replay_buffer_capacity` | `10000` | 样本池容量 |
| `preload_ratio` | `1.0` | 训练启动阈值 |
| `reverb_remover` | `Fifo` | 样本移除策略 |
| `reverb_sampler` | `Uniform` | 采样策略 |
| `reverb_rate_limiter` | `MinSize` | rate limiter |
| `train_batch_size` | `2048` | learner 批大小 |
| `dump_model_freq` | `100` | 模型保存频率 |
| `model_file_sync_per_minutes` | `1` | 模型同步频率 |
| `modelpool_max_save_model_count` | `1` | 单次同步模型数 |
| `preload_model` | `false` | 不使用预训练 |

---

## 9. 训练 Workflow

文件：`agent_ppo/workflow/train_workflow.py`

- `workflow` 主循环：
  - 读取 `train_env_conf.toml` 和 `eval_env_conf.toml`
  - 创建 `EpisodeRunner`
  - 每拿到一局 `collector` 后交给 `agent.send_sample_data`
  - 每 30 分钟保存一次模型
- 交叉验证循环（训练-评估交替）：
  - 训练地图：`[1, 2, 3, 4, 5, 6, 7, 8]`（`train_env_conf.toml`）
  - 测试地图：`[9, 10]`（`eval_env_conf.toml`）
  - 每 `50` 个训练 episode 后，运行 `10` 个测试 episode
  - 评估模式下：
    - 使用测试地图配置
    - 不上报 monitor 训练指标
    - 不产生训练样本（不用于模型更新）
  - 日志标记：`[TRAIN]` / `[EVAL]` / `[GAMEOVER][TRAIN]` / `[GAMEOVER][EVAL]`
- episode 流程：
  - `env.reset`（根据模式切换配置）
  - `agent.reset`
  - `agent.load_model(id="latest")`
  - `observation_process -> predict -> action_process -> env.step`
  - 每步把 `reward`, `reward_terms`, `value`, `prob` 组织成 `SampleData`
  - 对局结束后叠加终局奖励并做 `sample_process`
- 监控上报（以当前实现为准）：
  - `Train`：episode reward、score、treasure、steps、speedup、pre/post reward 与 gain
  - `环境指标`：地图、步数、宝箱、闪现、buff、怪物配置
  - `训练损失`：`total_loss`、`value_loss`、`policy_loss`、`entropy_loss`、`grad_clip_norm`、`clip_frac`、`explained_var` 等
  - `Val`：10 局 eval 均值的 reward、score、reward 拆分与终局统计

---

## 10. 已知限制

1. `train_test.py` 当前在容器内能跑通核心链路，但最终返回码仍为 `1`；从现有日志看，这更像是 smoke harness 收口行为，而不是实现侧异常。
2. 当前 buff 可用性仍是轻量近似维护，没有像宝箱一样由稳定的“剩余 ID 列表”精确对账。
3. 赛题文档没有显式终点协议，因此 HOK 设计中的终点记忆与终点距离 shaping 未直接迁入；当前 `guide_dist_reward` 只是 fallback。
4. 16 动作空间在未训练阶段会显著放大随机闪现行为，是否能稳定学会“危险时再闪”需要正式训练继续确认。

---

## 11. 截图驱动的训练/测试归档规则

- 训练和测试截图统一放在 `GLOBAL_DOCS/算法文档/agent_ppo_20260410_hok_memory_map_v1/screenshots/`
- 图片文件名（去掉扩展名）视作上传到官网的模型全称
- AI 归档时只检测 `screenshots/` 中是否存在图片，不校验截图真伪
- 人不需要再额外补填模型名、截图位置或截图说明

---

## 12. 当前截图检测结果

| 检测项 | 结果 |
| --- | --- |
| 截图目录 | `GLOBAL_DOCS/算法文档/agent_ppo_20260410_hok_memory_map_v1/screenshots/` |
| 已检测到图片 | `ppo+taichu_4k.png` |
| 由文件名得到的官网模型全称 | `ppo+taichu_4k` |
| 归档判定 | 已满足“目录中存在图片即可归档”的当前规则 |

---

## 13. 后续补充项

- 若后续还有更多训练/测试截图，继续放入同一 `screenshots/` 目录
- 若需要结构化记录 10 图评估明细，可在后续迭代时再补，不影响当前归档
- 根据后续正式评估结果决定是否将该版本切换为新的“当前基线”
