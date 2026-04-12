# agent_ppo_20260412_full_observation_curriculum_v1 算法文档

**文档版本**：`agent_ppo_20260412_full_observation_curriculum_v1`  
**记录日期**：`2026-04-12`  
**算法状态**：已实现，可启动训练，已通过本地与 Docker 链路验证

---

## 1. 算法概述

本算法面向 Gorge Chase 任务，目标是在怪物追击环境下兼顾生存、捡宝箱和阶段切换决策。  
算法主体采用 `PPO Actor-Critic`，不改 PPO 基本优化框架，重点通过以下三个方向提升策略质量：

- 用结构化 observation 明确表达英雄状态、怪物威胁、资源机会、技能空间和局部拓扑。
- 用阶段化 reward 区分前期捡箱、中期双怪压力、后期怪物加速后的生存决策。
- 用课程学习逐步扩大环境压力，让策略先学会稳定拿资源，再学会高压存活。

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
- `agent_ppo/feature/preprocessor.py`
- `agent_ppo/feature/definition.py`
- `agent_ppo/model/model.py`
- `agent_ppo/workflow/train_workflow.py`
- `agent_ppo/conf/monitor_builder.py`

---

## 3. 观测与特征设计

### 3.1 总体设计目标

观测设计需要尽量直接回答四类问题：

- 我现在危险不危险
- 我现在有没有机会拿资源
- 我往哪里走更安全
- 我现在该继续拿分还是该准备保命

### 3.2 特征维度

当前总 observation 维度为 `919`：

| 模块 | 维度 | 说明 |
| --- | --- | --- |
| `hero_feat` | 12 | 英雄主状态 |
| `monster_1` | 10 | 第一只怪物特征 |
| `monster_2` | 10 | 第二只怪物特征 |
| `semantic_map` | 847 | `7 x 11 x 11` 局部语义地图 |
| `legal_action` | 16 | 合法动作掩码 |
| `progress_feat` | 24 | 阶段、资源、压力与决策辅助特征 |
| 总计 | 919 | 完整输入向量 |

### 3.3 英雄主特征

`hero_feat` 主要描述“我现在是什么状态”：

- 英雄位置 `x/z`
- 闪现冷却
- 闪现是否可用
- buff 剩余时间
- buff 是否激活
- 宝箱收集比例
- 当前步数进度
- 危险度 `danger_level`
- 卡住比例 `stagnation_ratio`
- 来回横跳比例 `oscillation_ratio`
- 重复区域强度 `revisit_intensity`

### 3.4 怪物特征

每只怪物用 `10` 维特征描述，主要回答“危险从哪里来”：

- 是否可见
- 估计位置
- 移动速度
- 当前距离
- 距离桶
- 相对方向 `sin/cos`
- 是否激活
- 威胁分数 `threat_score`

第二只怪物显式进入输入，用于帮助策略识别双怪压缩空间和包夹风险。

### 3.5 局部地图特征

局部地图使用 `7` 个通道：

1. `walkable`
2. `visit_heat`
3. `collectible`
4. `risk`
5. `openness`
6. `corridor_depth`
7. `dead_end_risk`

其中后三个通道用于表达局部拓扑：

- `openness`：当前位置周围是否开阔，越开阔越适合拉扯
- `corridor_depth`：多个方向的通路深度，越深表示更像长走廊
- `dead_end_risk`：当前位置是否接近死角或短胡同

### 3.6 进度与决策辅助特征

`progress_feat` 主要回答“现在该贪还是该保”：

- 剩余宝箱比例
- 闪现使用比例
- 是否已经进入怪物加速阶段
- 距离加速还有多久
- 是否仍是单怪阶段
- 第二只怪是否已激活
- 最近怪物距离
- 第二只怪距离
- 包夹风险 `pinch_risk`
- 当前脚下局部开阔度
- 当前脚下走廊强度
- 当前脚下死角风险
- 是否存在宝箱目标
- 当前目标宝箱是否可见
- 宝箱距离
- 宝箱方向 `sin/cos`
- 宝箱机会分数 `treasure_opportunity`
- 是否存在 buff 目标
- buff 距离
- buff 方向 `sin/cos`
- 生存压力 `survival_pressure`
- 贪分窗口 `greed_window`

### 3.7 合法动作掩码

动作空间固定为 `16` 维：

- `0 ~ 7`：移动
- `8 ~ 15`：闪现

合法动作由两部分共同约束：

- 环境原生 `legal_action`
- preprocessor 基于局部障碍和上一帧无效位移得到的额外屏蔽

其作用是减少撞墙、无效移动和反复卡住。

---

## 4. 模型结构

算法采用结构化编码 + 融合 + Actor/Critic 双头：

```text
hero_feat(12)         -> FC -> 32
monster_pair(20)      -> FC -> 64
control_feat(40)      -> FC -> 32
semantic_map(7x11x11) -> Conv -> Conv -> Conv -> Flatten -> FC -> 128

concat -> backbone -> actor_head(16)
                 -> critic_head(1)
```

结构说明：

- 英雄、怪物、控制特征分别用全连接编码。
- 局部语义地图用卷积编码。
- 融合后进入共享 backbone。
- actor 输出 `16` 维动作 logits。
- critic 输出 `1` 维状态价值。

---

## 5. 奖励设计

### 5.1 设计原则

奖励设计分为四类目标：

- 资源获取：让策略愿意主动捡宝箱
- 生存保命：让策略在高压阶段优先活下来
- 技能使用：让闪现更像“操作”而不是“随机按钮”
- 行为约束：减少撞墙、卡住、绕圈和原地发呆

### 5.2 宝箱与资源奖励

核心资源相关项如下：

- `TREASURE_REWARD = 1.2`
  - 捡到宝箱的直接奖励
- `TREASURE_DIST_COEF = 0.1`
  - 接近宝箱的距离 shaping
- `CLOSE_TREASURE_APPROACH_COEF = 0.08`
  - 近距离时鼓励把最后几步走完
- `TREASURE_MISS_PENALTY = 0.15`
  - 已经靠近宝箱却明显走开的惩罚
- `BUFF_REWARD = 0.3`
  - 拿到 buff 的奖励

### 5.3 前期单怪捡箱窗口

当前算法将“前期安全捡箱”显式建模为一个门控阶段。满足以下条件时进入捡箱窗口：

- 还未进入怪物加速阶段
- 当前仍是单怪阶段
- 最近怪物距离大于安全阈值

在该窗口内：

- 宝箱相关奖励会被增强
- 远离怪物 shaping 会降权
- 重复探索惩罚会降权
- 探索 bonus 会降低
- 若长时间盯着宝箱却没有接近，会触发停滞惩罚

相关参数：

- `EARLY_LOOT_SAFE_DISTANCE = 85.0`
- `EARLY_LOOT_TREASURE_PRIORITY_MULTIPLIER = 1.75`
- `EARLY_LOOT_DIST_SHAPING_MULTIPLIER = 0.45`
- `EARLY_LOOT_REVISIT_PENALTY_MULTIPLIER = 0.6`
- `EARLY_LOOT_EXPLORE_BONUS_MULTIPLIER = 0.0`
- `EARLY_LOOT_COLLECTION_BONUS = 0.25`
- `EARLY_LOOT_FIRST_TREASURE_BONUS = 0.4`
- `EARLY_LOOT_STALL_PENALTY = 0.012`

### 5.4 阶段化宝箱优先级

宝箱优先级不是固定常数，而是按局面动态调整：

- 单怪阶段：怪物已经贴近但还没到极限危险时，优先捡宝箱
- 双怪阶段：若未形成明显包夹，仍可优先捡宝箱
- 怪物加速阶段：降低宝箱优先级，抬高保命优先级

### 5.5 生存与压力奖励

核心生存项如下：

- `SURVIVE_REWARD = 0.005`
- `DIST_SHAPING_COEF = 0.05`
- `PRE_SPEEDUP_BUFFER_COEF = 0.04`
  - 怪物加速前的缓冲期安全距离奖励
- `SECOND_MONSTER_PRESSURE_COEF = 0.03`
  - 第二只怪压得太近时的额外惩罚

加速阶段会提高生存权重：

- `POST_SPEEDUP_SURVIVE_MULTIPLIER = 1.5`
- `POST_SPEEDUP_DIST_MULTIPLIER = 1.4`

### 5.6 闪现奖励

闪现相关信号分为四类：

- `FLASH_ESCAPE_REWARD_COEF = 0.05`
  - 危险距离下成功拉开怪物距离
- `FLASH_DIRECTION_REWARD_COEF = 0.04`
  - 面向怪物来向交闪现，方向合理时给奖励
- `FLASH_THROUGH_WALL_REWARD_COEF = 0.06`
  - 穿墙且位移有效时给奖励
- `FLASH_WASTE_PENALTY = 0.08`
  - 乱交闪现，没有脱险也没有拿资源时惩罚

穿墙闪现通过上一帧局部地图扫描来判断：

- 检查闪现方向路径上是否存在阻挡格
- 若普通移动会被墙挡住，但闪现后位移有效，则认定为有效穿墙

### 5.7 坏行为约束

为减少明显坏行为，加入以下项：

- `HIT_WALL_PENALTY = 0.05`
  - 撞墙 / 无效位移
- `STAGNATION_PENALTY_COEF = 0.05`
  - 原地卡住
- `OSCILLATION_PENALTY_COEF = 0.06`
  - 来回横跳
- `REVISIT_PENALTY_COEF = 0.02`
  - 老区域绕圈
- `NO_VISION_PATROL_BONUS_COEF = 0.02`
  - 没有怪、没有资源时做有效巡逻

### 5.8 终局奖励

- 死亡：`TERMINATED_PENALTY = -12.0`
- 存活到最大步数：`TRUNCATED_BONUS = 8.0`

---

## 6. 样本结构与训练逻辑

### 6.1 样本结构

训练样本定义在 `agent_ppo/feature/definition.py`：

- `ObsData`
  - `feature[919]`
  - `legal_action[16]`
- `ActData`
  - `action[1]`
  - `d_action[1]`
  - `prob[16]`
  - `value[1]`
- `SampleData`
  - `obs[919]`
  - `legal_action[16]`
  - `act[1]`
  - `reward[1]`
  - `reward_sum[1]`
  - `done[1]`
  - `value[1]`
  - `next_value[1]`
  - `advantage[1]`
  - `prob[16]`

### 6.2 GAE

优势函数使用 GAE：

```python
delta = -value + reward + gamma * next_value * (1 - done)
gae = gae * gamma * lamda * (1 - done) + delta
advantage = gae
reward_sum = gae + value
```

参数：

- `GAMMA = 0.995`
- `LAMDA = 0.95`

### 6.3 PPO 超参数

核心超参数如下：

- `INIT_LEARNING_RATE_START = 2e-4`
- `CLIP_PARAM = 0.15`
- `VF_COEF = 1.0`
- `GRAD_CLIP_RANGE = 0.5`
- `TARGET_KL = 0.015`
- `USE_ADVANTAGE_NORM = True`
- `BETA_START = 0.003`
- `BETA_END = 0.0005`
- `BETA_DECAY_STEPS = 4000`

---

## 7. 课程学习配置

训练采用四阶段课程学习：

| 阶段 | episode 范围 | 宝箱数 | buff 数 | 第二只怪出现时间 | 怪物加速时间 | 最大步数 |
| --- | --- | --- | --- | --- | --- | --- |
| `warmup_stable` | `0 ~ 149` | `9 ~ 10` | `2` | `220 ~ 300` | `360 ~ 460` | `2000` |
| `mid_pressure` | `150 ~ 499` | `8 ~ 10` | `1 ~ 2` | `160 ~ 280` | `240 ~ 420` | `2000` |
| `late_speedup_survival` | `500 ~ 899` | `7 ~ 10` | `1 ~ 2` | `120 ~ 220` | `180 ~ 320` | `2000` |
| `hard_generalization` | `900+` | `6 ~ 10` | `0 ~ 2` | `120 ~ 320` | `140 ~ 420` | `2000` |

地图配置：

- 训练地图：`1 ~ 8`
- 验证地图：`9 ~ 10`

训练时使用 `map_random = true`。

---

## 8. Checkpoint 与训练启动策略

系统配置位于 `conf/configure_app.toml`。

当前默认配置：

- `preload_model = false`
- `preload_model_dir = "agent_ppo/ckpt"`
- `preload_model_id = 9705`

默认行为：

- 当前默认从头训练

当满足下面条件时，可按 checkpoint 续训：

- `preload_model = true`
- `preload_model_dir` 下存在对应 `model.ckpt-{id}.pkl`

续训时课程阶段直接从：

- `hard_generalization`

兼容性要求：

- 仅可加载与当前 observation / 模型结构一致的 checkpoint

---

## 9. 训练监控指标

### 9.1 PPO 训练指标

用于判断 PPO 优化是否稳定：

- `CumReward`
  - 当前训练 batch 平均奖励
- `TotalLoss`
  - PPO 总损失
- `ValueLoss`
  - critic 损失
- `PolicyLoss`
  - actor 损失
- `EntropyLoss`
  - 策略熵
- `GradClipNorm`
  - 梯度裁剪前范数
- `ClipFrac`
  - PPO 被 clip 的比例
- `ExplainedVar`
  - critic 对 return 的解释程度
- `AdvMean`
  - 当前 batch advantage 均值
- `RetMean`
  - 当前 batch return 均值

### 9.2 训练进度指标

用于确认训练进行到哪里：

- `current_episode_id`
- `completed_episode_count`
- `current_episode_step`
- `current_episode_is_eval`
- `train_episode_total`

### 9.3 train / val 局级指标

train 和 val 采用同一套 episode 指标，重点关注：

- 基础结果
  - `reward`
  - `total_score`
  - `step_score`
  - `treasure_score`
  - `treasures_collected`
  - `episode_steps`
- 阶段拆分
  - `speedup_reached`
  - `phase_time_to_speedup`
  - `pre_speedup_steps`
  - `post_speedup_steps`
  - `pre_speedup_reward`
  - `post_speedup_reward`
  - `pre_speedup_shaped_reward`
  - `post_speedup_shaped_reward`
  - `pre_speedup_step_score_gain`
  - `post_speedup_step_score_gain`
  - `pre_speedup_treasure_gain`
  - `post_speedup_treasure_gain`
  - `pre_speedup_total_score_gain`
  - `post_speedup_total_score_gain`
  - `pre_speedup_treasures_collected`
  - `post_speedup_treasures_collected`
  - `pre_speedup_treasure_rate`
- 前期捡箱
  - `time_to_first_treasure`
  - `early_loot_collection_bonus`
  - `early_loot_stall_penalty`
- 行为质量
  - `flash_direction_reward`
  - `flash_through_wall_reward`
  - `flash_waste_penalty`
  - `hit_wall_penalty`
  - `stagnation_penalty`
  - `oscillation_penalty`
  - `treasure_miss_penalty`
  - `no_vision_patrol_bonus`
- 终局与风险
  - `post_speedup_terminated`
  - `terminated_flag`
  - `completed_flag`
  - `abnormal_truncated_flag`
  - `danger_level`
  - `nearest_treasure_dist`

---

## 10. 训练与诊断建议

训练时优先关注以下现象：

1. `val_treasures_collected` 是否稳定提升到目标区间
2. `time_to_first_treasure` 是否明显下降
3. `pre_speedup_treasure_rate` 是否提高
4. `flash_waste_penalty` 是否下降，`flash_through_wall_reward` 是否开始出现
5. `hit_wall_penalty / stagnation_penalty / oscillation_penalty` 是否下降
6. `post_speedup_terminated` 是否没有因为前期更贪箱子而明显恶化

若出现以下问题，可按方向排查：

- 看见宝箱不捡
  - 重点看 `time_to_first_treasure`、`pre_speedup_treasure_rate`
- 乱交闪现
  - 重点看 `flash_waste_penalty`、`flash_direction_reward`
- 撞墙来回走
  - 重点看 `hit_wall_penalty`、`stagnation_penalty`、`oscillation_penalty`
- 后期加速后暴毙
  - 重点看 `post_speedup_reward`、`post_speedup_terminated`

---

## 11. 验证状态

### 11.1 本地验证

已通过：

```bash
python -m py_compile agent_ppo/conf/conf.py agent_ppo/feature/preprocessor.py agent_ppo/feature/definition.py agent_ppo/model/model.py
```

本地最小链路验证结果：

- `Preprocessor.feature_process(...)` 输出维度为 `919`
- `Model.forward(...)` 输出形状正常
  - logits `(1, 16)`
  - value `(1, 1)`

### 11.2 Docker 验证

已通过：

```bash
docker exec kaiwu-dev-kaiwudrl-1 sh -lc "cd /data/projects/gorge_chase && python3 -m py_compile agent_ppo/conf/conf.py agent_ppo/feature/preprocessor.py agent_ppo/feature/definition.py agent_ppo/model/model.py"
```

容器内最小链路验证结果：

- `feature_len = 919`
- 模型前向正常

### 11.3 Docker smoke

已执行：

```bash
docker exec kaiwu-dev-kaiwudrl-1 sh -lc "cd /data/projects/gorge_chase && python3 train_test.py"
```

结果：

- learner 正常启动
- aisrv 正常启动
- workflow 正常启动
- 能进入训练 episode
- 能看到课程学习采样结果
- 未出现由当前实现引入的新 traceback

说明：

- `train_test.py` 最终退出码仍为 `1`
- 该现象与此前 smoke 行为一致

---

## 12. 风险与后续工作

当前需要注意的点：

1. 当前 observation 与模型结构要求使用同结构 checkpoint。
2. topology 通道属于启发式构造，是否稳定带来收益需要结合正式训练验证。
3. 前期捡箱与后期保命之间仍需根据实际训练结果继续平衡。

后续训练建议优先补充：

- 正式训练任务与起始 checkpoint
- 关键监控截图
- 最优模型信息
- 验证表现与官评结果
