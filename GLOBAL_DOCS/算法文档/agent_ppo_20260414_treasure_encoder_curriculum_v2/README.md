# agent_ppo_20260414_treasure_encoder_curriculum_v2 算法文档

**文档版本**：`agent_ppo_20260414_treasure_encoder_curriculum_v2`  
**记录日期**：`2026-04-15`  
**当前状态**：已实现；已归档；已检测到训练监控 HTML 文档与结构化导出结果；当前作为仓库现行基线  
**HTML 文档目录**：`GLOBAL_DOCS/算法文档/agent_ppo_20260414_treasure_encoder_curriculum_v2/html/`

---

## 1. 算法概述

- **任务目标**：在 Gorge Chase 中兼顾生存、捡宝箱、闪现使用和阶段切换决策。
- **算法框架**：保持 `agent_ppo/` 现有 `PPO Actor-Critic` 主链路，不改训练接口。
- **本轮核心改动**：
  - 新增独立宝箱特征模块 `treasure_feat`（10 维），从 `progress_feat` 中解耦。
  - 新增独立宝箱编码器 `treasure_encoder`（`Linear 10→16 + ReLU`）。
  - 将 `treasure_dist_reward` 改为对**视野内最近宝箱**生效，而不是只绑定预选目标。
  - 新增 `treasure_passability`，显式表达英雄到目标宝箱方向的局部可通行性。
  - 在 `PPO` 基础上，继续使用四阶段 curriculum，强化前期捡箱与后期保命的阶段差异。
- **相对上一代基线 `agent_ppo_20260410_hok_memory_map_v1` 的关键变化**：
  - 观测维度从 `919` 提升到 `929`。
  - 局部地图保留 `7 x 11 x 11` 语义拓扑表达。
  - 奖励权重整体向“前期高质量捡箱”进一步倾斜，同时降低纯生存信号的压制。

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

核心实现文件：

- `agent_ppo/conf/conf.py`
- `agent_ppo/agent.py`
- `agent_ppo/feature/preprocessor.py`
- `agent_ppo/feature/definition.py`
- `agent_ppo/model/model.py`
- `agent_ppo/algorithm/algorithm.py`
- `agent_ppo/workflow/train_workflow.py`

最小验证命令：

```bash
python3 train_test.py
```

---

## 3. Agent 接口

文件：`agent_ppo/agent.py`

| 方法 | 说明 |
| --- | --- |
| `reset(env_obs=None, usr_conf=None)` | 每局开始时重置 preprocessor 内部状态、目标记忆、访问热度和 `last_action` |
| `observation_process(env_obs)` | 调用 `Preprocessor.feature_process`，返回 `ObsData(feature, legal_action)` 与 `remain_info(reward, reward_terms, speedup_state)` |
| `predict(list_obs_data)` | 训练时执行 masked softmax，并对 16 维动作分布做随机采样，同时保留贪心动作 |
| `exploit(env_obs)` | 评估时走同一前处理链路，但输出贪心动作 |
| `learn(list_sample_data)` | 调用 `Algorithm.learn` 执行一轮 PPO 更新 |
| `save_model(path, id)` | 保存 `model.ckpt-{id}.pkl` |
| `load_model(path, id)` | 加载指定 checkpoint |
| `action_process(act_data, is_stochastic)` | 将 `ActData` 解包为环境整数动作，并更新 `last_action` |

---

## 4. 特征处理

文件：`agent_ppo/feature/preprocessor.py`

### 4.1 特征向量

当前总 observation 维度为 `929`：

| 分组 | 维度 | 内容 |
| --- | --- | --- |
| `hero_feat` | 12 | 英雄位置、闪现冷却、buff 剩余、宝箱收集比例、危险度、停滞/横跳/重复访问强度 |
| `monster_1` | 10 | 第一只怪物可见性、位置、速度、距离桶、方向、激活态、威胁分数 |
| `monster_2` | 10 | 第二只怪物同构特征 |
| `treasure_feat` | 10 | 当前宝箱目标的可见性、位置、可通行性、距离、方向、可用性、机会分数 |
| `semantic_map` | 847 | `7 x 11 x 11` 局部语义地图 |
| `legal_action` | 16 | 环境原生动作 mask + preprocessor 额外屏蔽 |
| `progress_feat` | 24 | 阶段、资源、怪物压力、宝箱/buff 机会与保命辅助特征 |
| 总计 | 929 | 完整输入向量 |

特征拼接顺序：

```text
[hero_feat(12), monster_1(10), monster_2(10), treasure_feat(10),
 semantic_map(847), legal_action(16), progress_feat(24)]
```

### 4.2 宝箱特征模块 `treasure_feat`

`treasure_feat` 与怪物特征刻意对齐：

| 维度 | 特征名 | 说明 |
| --- | --- | --- |
| 0 | `treasure_visible` | 宝箱是否在当前视野内 |
| 1 | `pos_x` | 宝箱位置 x（归一化） |
| 2 | `pos_z` | 宝箱位置 z（归一化） |
| 3 | `treasure_passability` | 英雄→宝箱方向的局部路径可通行性 |
| 4 | `distance_norm` | 宝箱距离（归一化） |
| 5 | `distance_bucket` | 距离桶（归一化） |
| 6 | `dir_sin` | 宝箱方向 sin 分量 |
| 7 | `dir_cos` | 宝箱方向 cos 分量 |
| 8 | `treasure_available` | 宝箱是否仍可捡取 |
| 9 | `treasure_opportunity` | 宝箱机会综合分数 |

`treasure_passability` 的计算逻辑：

1. 计算英雄到目标宝箱的方向向量。
2. 选取与该方向最对齐的 8 个离散移动方向。
3. 在该方向上检查局部地图前 3 格 `walkable_channel`。
4. 以可通行格数 / 总检查格数作为 `passability`。

### 4.3 局部地图特征

局部地图使用 `7` 个通道：

1. `walkable`
2. `visit_heat`
3. `collectible`
4. `risk`
5. `openness`
6. `corridor_depth`
7. `dead_end_risk`

后三个通道用于表达局部拓扑，使策略在“走廊 / 开阔地 / 死角”之间建立更强的结构意识。

### 4.4 合法动作处理

动作空间固定为 `16` 维：

- `0 ~ 7`：移动
- `8 ~ 15`：闪现

合法动作由两部分共同约束：

- 环境原生 `legal_action`
- preprocessor 基于局部障碍和上一帧无效位移得到的额外屏蔽

### 4.5 奖励设计

即时奖励全部在 `preprocessor.py` 中构造，当前 reward_terms 包含：

- `survive_reward`
- `dist_shaping`
- `treasure_dist_reward`
- `close_treasure_reward`
- `guide_dist_reward`
- `treasure_reward`
- `early_loot_collection_bonus`
- `buff_reward`
- `treasure_miss_penalty`
- `early_loot_stall_penalty`
- `pre_speedup_buffer_reward`
- `second_monster_pressure_penalty`
- `flash_escape_reward`
- `flash_direction_reward`
- `flash_through_wall_reward`
- `flash_waste_penalty`
- `hit_wall_penalty`
- `stagnation_penalty`
- `oscillation_penalty`
- `revisit_penalty`
- `no_vision_patrol_bonus`
- `explore_bonus`

其中最关键的变化是：

- `treasure_dist_reward` 追踪**视野内最近宝箱**，减少目标切换带来的距离信号断裂。
- `EARLY_LOOT_*` 系列参数强化了单怪安全窗口内的捡箱优先级。
- `FLASH_*` 系列参数分别奖励脱险、方向合理、有效穿墙，并惩罚无收益乱交闪现。

---

## 5. 样本结构与 GAE

文件：`agent_ppo/feature/definition.py`

- `ObsData`
  - `feature[929]`
  - `legal_action[16]`
- `ActData`
  - `action[1]`
  - `d_action[1]`
  - `prob[16]`
  - `value[1]`
- `SampleData`
  - `obs[929]`
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
hero_feat(12)         -> FC(12→32)      + ReLU -> 32
monster_pair(20)      -> FC(20→64)      + ReLU -> 64
treasure_feat(10)     -> FC(10→16)      + ReLU -> 16
control_feat(40)      -> FC(40→32)      + ReLU -> 32
semantic_map(7x11x11) -> Conv(7→16) -> Conv(16→32,s=2) -> Conv(32→32,s=2)
                      -> Flatten -> FC(288→128) -> ReLU -> 128

concat(32 + 64 + 16 + 128 + 32 = 272)
-> backbone FC 272→128 -> ReLU -> FC 128→128 -> ReLU
-> actor_head 128→16
-> critic_head 128→1
```

实现特点：

- 英雄、怪物、宝箱、控制特征使用分支编码器。
- 地图分支使用 `CNN` 而不是直接 flatten 到 `MLP`。
- `map_dim` 会在构造时强校验为 `7 * 11 * 11 = 847`。
- 所有 `Linear` 层使用 orthogonal init。

---

## 7. 算法训练逻辑

文件：`agent_ppo/algorithm/algorithm.py`

- 保持标准 PPO：
  - 策略损失：clip surrogate objective
  - 价值损失：clipped value loss
  - 熵项：合法动作掩码后的策略熵
- 总损失：

```text
total_loss = vf_coef * value_loss + policy_loss - beta * entropy_loss
```

- 当前关键训练约束：
  - `CLIP_PARAM = 0.15`
  - `VF_COEF = 1.0`
  - `TARGET_KL = 0.015`
  - `GRAD_CLIP_RANGE = 0.5`
  - `USE_ADVANTAGE_NORM = True`
- 熵系数线性衰减：

```text
BETA_START = 0.003
-> 线性衰减到
BETA_END = 0.0005
-> 共 4000 步
```

---

## 8. 超参数汇总

### 8.1 算法超参数

文件：`agent_ppo/conf/conf.py`

| 参数 | 当前值 | 说明 |
| --- | --- | --- |
| `FEATURE_LEN` | `929` | 总观测维度 |
| `ACTION_NUM` | `16` | 动作空间（8 移动 + 8 闪现） |
| `LOCAL_MAP_CHANNEL` | `7` | 局部语义地图通道数 |
| `LOCAL_MAP_SIZE` | `11` | 局部地图边长 |
| `TREASURE_ENCODER_DIM` | `16` | 宝箱分支编码维度 |
| `HERO_ENCODER_DIM` | `32` | 英雄分支编码维度 |
| `MONSTER_ENCODER_DIM` | `64` | 怪物分支编码维度 |
| `MAP_ENCODER_DIM` | `128` | 地图分支编码维度 |
| `CONTROL_ENCODER_DIM` | `32` | 控制分支编码维度 |
| `FUSION_HIDDEN_DIM` | `128` | 融合主干隐藏维度 |
| `GAMMA` | `0.995` | 折扣因子 |
| `LAMDA` | `0.95` | GAE λ |
| `INIT_LEARNING_RATE_START` | `2e-4` | Adam 学习率 |
| `CLIP_PARAM` | `0.15` | PPO clip |
| `VF_COEF` | `1.0` | value loss 权重 |
| `TARGET_KL` | `0.015` | KL 早停阈值 |
| `BETA_START` | `0.003` | 初始熵系数 |
| `BETA_END` | `0.0005` | 末端熵系数 |
| `BETA_DECAY_STEPS` | `4000` | 熵系数衰减步数 |
| `SURVIVE_REWARD` | `0.001` | 基础生存奖励 |
| `DIST_SHAPING_COEF` | `0.03` | 怪物距离 shaping |
| `POST_SPEEDUP_SURVIVE_MULTIPLIER` | `1.15` | 加速后生存奖励乘数 |
| `POST_SPEEDUP_DIST_MULTIPLIER` | `1.1` | 加速后距离 shaping 乘数 |
| `TRUNCATED_BONUS` | `4.0` | 存活到最大步数奖励 |
| `TERMINATED_PENALTY` | `-8.0` | 死亡终局惩罚 |
| `TREASURE_REWARD` | `2.5` | 宝箱直接奖励 |
| `BUFF_REWARD` | `0.5` | buff 奖励 |
| `TREASURE_DIST_COEF` | `0.18` | 最近可见宝箱距离 shaping |
| `CLOSE_TREASURE_APPROACH_COEF` | `0.15` | 近距离冲刺奖励 |
| `TREASURE_MISS_PENALTY` | `0.3` | 靠近后走开的惩罚 |
| `EXIT_DIST_COEF` | `0.06` | 无宝箱时的 buff fallback 引导 |
| `EARLY_LOOT_TREASURE_PRIORITY_MULTIPLIER` | `2.2` | 前期安全窗口捡箱优先级 |
| `EARLY_LOOT_COLLECTION_BONUS` | `0.6` | 前期捡箱额外奖励 |
| `EARLY_LOOT_FIRST_TREASURE_BONUS` | `1.0` | 首箱额外奖励 |
| `EARLY_LOOT_STALL_PENALTY` | `0.03` | 盯箱不动惩罚 |
| `SECOND_MONSTER_PRESSURE_COEF` | `0.025` | 第二只怪压力惩罚 |
| `FLASH_ESCAPE_REWARD_COEF` | `0.05` | 闪现脱险奖励 |
| `FLASH_DIRECTION_REWARD_COEF` | `0.04` | 闪现方向奖励 |
| `FLASH_THROUGH_WALL_REWARD_COEF` | `0.06` | 穿墙闪现奖励 |
| `FLASH_WASTE_PENALTY` | `0.08` | 闪现浪费惩罚 |
| `HIT_WALL_PENALTY` | `0.05` | 撞墙惩罚 |
| `STAGNATION_PENALTY_COEF` | `0.05` | 卡住惩罚 |
| `OSCILLATION_PENALTY_COEF` | `0.06` | 来回横跳惩罚 |
| `REVISIT_PENALTY_COEF` | `0.02` | 重访惩罚 |
| `EXPLORE_BONUS_SCALE` | `0.01` | 探索 bonus |

### 8.2 环境配置

文件：`agent_ppo/conf/train_env_conf.toml`、`agent_ppo/conf/eval_env_conf.toml`

基础环境配置：

| 参数 | 当前值 | 说明 |
| --- | --- | --- |
| `train.map` | `[1,2,3,4,5,6,7,8]` | 训练地图 |
| `train.map_random` | `true` | 训练阶段随机抽图 |
| `eval.map` | `[9,10]` | 评估地图 |
| `eval.map_random` | `true` | 评估阶段随机抽图 |
| `treasure_count` | `10` | 基础默认宝箱数 |
| `buff_count` | `2` | 基础默认 buff 数 |
| `buff_cooldown` | `200`（train）/ `100`（eval） | buff 刷新时间 |
| `talent_cooldown` | `100` | 闪现冷却 |
| `monster_interval` | `300`（train 默认）/ `500`（eval） | 第二只怪出现时间 |
| `monster_speedup` | `500`（train 默认）/ `700`（eval） | 怪物加速时间 |
| `max_step` | `2000`（train）/ `1000`（eval） | 每局最大步数 |

四阶段 curriculum（实际训练时覆盖部分 train 默认值）：

| 阶段 | episode 范围 | 宝箱数 | buff 数 | 第二只怪出现时间 | 怪物加速时间 | 最大步数 |
| --- | --- | --- | --- | --- | --- | --- |
| `warmup_stable` | `0 ~ 149` | `9 ~ 10` | `2` | `220 ~ 300` | `360 ~ 460` | `2000` |
| `mid_pressure` | `150 ~ 499` | `8 ~ 10` | `1 ~ 2` | `160 ~ 280` | `240 ~ 420` | `2000` |
| `late_speedup_survival` | `500 ~ 899` | `7 ~ 10` | `1 ~ 2` | `120 ~ 220` | `180 ~ 320` | `2000` |
| `hard_generalization` | `900+` | `6 ~ 10` | `0 ~ 2` | `120 ~ 320` | `140 ~ 420` | `2000` |

### 8.3 系统训练配置

文件：`conf/configure_app.toml`

| 参数 | 当前值 | 说明 |
| --- | --- | --- |
| `replay_buffer_capacity` | `10000` | 样本池容量 |
| `preload_ratio` | `1.0` | 训练启动阈值 |
| `reverb_remover` | `reverb.selectors.Fifo` | 样本移除策略 |
| `reverb_sampler` | `reverb.selectors.Uniform` | 采样策略 |
| `reverb_rate_limiter` | `MinSize` | rate limiter |
| `reverb_samples_per_insert` | `5` | 单样本最大复用次数上限 |
| `reverb_error_buffer` | `5` | 采样 / 插入比缓冲 |
| `train_batch_size` | `2048` | learner 批大小 |
| `dump_model_freq` | `1` | 模型参数文件输出频率 |
| `model_file_sync_per_minutes` | `1` | 模型同步频率 |
| `modelpool_max_save_model_count` | `1` | 单次同步模型数 |
| `preload_model` | `false` | 默认从头训练 |
| `preload_model_dir` | `agent_ppo/ckpt` | 续训目录 |
| `preload_model_id` | `9705` | 续训模型步数 ID |

---

## 9. 训练 Workflow

文件：`agent_ppo/workflow/train_workflow.py`

- `workflow` 主循环：
  - 读取 `train_env_conf.toml` 和 `eval_env_conf.toml`
  - 创建 `EpisodeRunner`
  - 对每局 `collector` 调用 `agent.send_sample_data`
  - 每 30 分钟执行一次 `agent.save_model()`
- 交叉验证循环：
  - 训练地图：`[1,2,3,4,5,6,7,8]`
  - 评估地图：`[9,10]`
  - 每 `50` 个训练 episode 后，运行 `10` 个评估 episode
- 课程学习：
  - `EpisodeRunner._build_train_episode_conf()` 会按 `Config.CURRICULUM_STAGES` 动态覆盖宝箱数、buff 数、双怪出现时间、怪物加速时间和 `max_step`
  - 若检测到合法续训 checkpoint，则从 `RESUME_CURRICULUM_STAGE_NAME = hard_generalization` 对应的 episode 段继续
- episode 终局奖励：
  - `terminated=True`：`Config.TERMINATED_PENALTY = -8.0`
  - 存活到 `max_step`：`Config.TRUNCATED_BONUS = 4.0`
- 监控上报：
  - 训练损失：`reward`、`total_loss`、`value_loss`、`policy_loss`、`entropy_loss`、`grad_clip_norm`、`clip_frac`、`explained_var`、`adv_mean`、`ret_mean`
  - episode 指标：`total_score`、`treasures_collected`、`episode_steps`、`danger_level`、`nearest_treasure_dist`
  - 阶段指标：`pre/post_speedup_*`、`time_to_first_treasure`、`flash_*`、`hit_wall_penalty`、`stagnation_penalty`、`oscillation_penalty` 等

---

## 10. 验证状态与已知限制

### 10.1 已完成验证

已通过的最小验证：

```bash
python -m py_compile agent_ppo/conf/conf.py agent_ppo/feature/preprocessor.py agent_ppo/feature/definition.py agent_ppo/model/model.py
```

容器内验证：

```bash
docker exec kaiwu-dev-kaiwudrl-1 sh -lc "cd /data/projects/gorge_chase && python3 -m py_compile agent_ppo/conf/conf.py agent_ppo/feature/preprocessor.py agent_ppo/feature/definition.py agent_ppo/model/model.py"
```

Docker smoke：

```bash
docker exec kaiwu-dev-kaiwudrl-1 sh -lc "cd /data/projects/gorge_chase && python3 train_test.py"
```

验证记录显示：

- `feature_len = 929`
- 模型前向输出形状正常：`logits (1, 16)`、`value (1, 1)`
- learner / aisrv / workflow 均能启动
- 能进入训练 episode 并看到课程学习采样结果
- 未出现由本轮实现引入的新 traceback

### 10.2 已知限制

1. `929` 维观测与上一代 `919` 维版本不兼容，不能直接混用旧 checkpoint。
2. `topology` 通道属于启发式构造，稳定收益仍需以持续训练结果验证。
3. 前期捡箱与后期保命的权重平衡仍有继续调参空间。
4. `treasure_passability` 只检查局部前 3 格，可通行性仍是近似表达，不是完整路径规划。
5. 当前 `html/` 目录中尚未检测到独立的 5 次官网评估结果 HTML 文档，因此官网评估部分仍待补充。

---

## 11. 真实训练信息

当前已检测到以下真实训练材料：

- 训练监控 HTML 文档：`训练监控 -_ 腾讯开悟比赛平台 (2026_4_15 00：32：12).html`
- 配套导出表：`kaiwu.xlsx`

从 `kaiwu.xlsx` 可直接读取到的 steps 节点包括：

- `2000`
- `5000`
- `8000`
- `11000`

导出表头字段为：

- `非周赛步数`
- `非周赛宝箱`
- `非周赛总得分`
- `周赛步数`
- `周赛宝箱`
- `周赛总得分`
- `非周赛步数衰减`
- `非周赛宝箱增加`
- `周赛步数衰减`
- `周赛宝箱增加`

最新一行（`steps = 11000`）记录为：

| 字段 | 值 |
| --- | --- |
| `非周赛步数` | `460` |
| `非周赛宝箱` | `552` |
| `非周赛总得分` | `1242` |
| `周赛步数` | `580` |
| `周赛宝箱` | `658` |
| `周赛总得分` | `1527` |
| `非周赛步数衰减` | `69` |
| `非周赛宝箱增加` | `384` |
| `周赛步数衰减` | `-22` |
| `周赛宝箱增加` | `362` |

说明：以上字段名称和数值均直接来自当前归档目录中的导出表，本文档不对平台字段做额外二次解释。

---

## 12. HTML 文档索引

目录：`GLOBAL_DOCS/算法文档/agent_ppo_20260414_treasure_encoder_curriculum_v2/html/`

| 文件名 | 类型 | 说明 |
| --- | --- | --- |
| `训练监控 -_ 腾讯开悟比赛平台 (2026_4_15 00：32：12).html` | 训练监控 HTML 文档 | 当前已检测到的训练监控导出文件 |
| `kaiwu.xlsx` | 配套导出表 | 当前监控数据的结构化导出结果 |

---

## 13. 官网模型评估记录

当前仍待人工补充：

- 官网模型上传命名：待补充
- 5 次官方评估：待补充
- 10 张开放地图得分：待补充
- 最终结果 HTML 文档：待补充

在补齐上述内容前，当前归档结论为：

- 已完成实现归档
- 已有训练监控 HTML 文档与结构化导出表
- 暂无独立的官网评估结果 HTML 文档
