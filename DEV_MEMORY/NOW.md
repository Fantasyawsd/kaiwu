# NOW	

## 当前要实现的算法具体内容

## 本轮算法设计：agent_ppo_20260410_hok_memory_map_v1

### 1. 目标

- 本轮准备验证的主假设：
  将 `hok_prelim` 中可迁移的“目标记忆 + 局部语义地图 + 分层奖励 + 闪现动作利用”落到当前 Gorge Chase PPO 基线上，即使不改成 DDQN，也能显著提升当前只会基础生存的 40 维 PPO baseline。
- 明确不迁移的部分：
  不直接照搬 `hok_prelim` 的 DDQN / target network 主训练框架；本项目当前训练链路、样本结构和算法基线已经稳定在 PPO，上层框架、监控和文档也围绕 PPO 建立，直接切 DQN 改动面过大、验证链路更长。
- 本轮单一主方向：
  做一个 “HOK 风格记忆地图 PPO” 版本，而不是同时并行尝试多个独立方向。

### 2. 与当前 baseline 的差异

- 当前 baseline：
  40 维结构化特征 + 8 维移动动作 + 怪物距离 shaping + 轻量探索奖励。
- 新版本目标：
  - 从 8 动作扩展到 16 动作，接入闪现。
  - 从“仅局部 4x4 障碍物”升级为“多通道局部语义地图”。
  - 从“仅看当前可见物体”升级为“对宝箱 / buff / 终点做位置记忆与方向距离估计”。
  - 从“单一生存奖励”升级为“生存 / 收集 / 脱险 / 防绕圈 / 终局”的分层奖励。
  - 保持 PPO，不切换成 DDQN。

### 3. 文档依据

- 来源：`开发文档/开发指南/环境详述.md`
  - 环境观测原生提供 `map_info`（21x21 局部视野）、`legal_act`（16 维合法动作）、`organs`（宝箱/buff）、`monsters`（含相对方向和距离桶）。
  - 闪现是环境原生动作空间的一部分，动作 8-15 可合法执行时应可直接接入。
- 来源：`开发文档/开发指南/数据协议.md`
  - `MonsterState.hero_relative_direction`、`hero_l2_distance` 与 `OrganState` 同类字段足以支持“视野外方向+距离估计”。
  - `EnvInfo` 提供 `treasure_id`、`treasures_collected`、`flash_count` 等状态，可用于奖励与进度特征。
- 来源：`开发文档/开发指南/智能体详述.md`
  - 官方明确鼓励扩展宝箱特征、地图记忆、闪现奖励和动作空间。
  - 当前 40 维 PPO 只是最简 baseline，可扩展特征、奖励、模型结构。
- 来源：`开发文档/腾讯开悟强化学习框架/智能体/特征处理.md`
  - 允许在 `preprocessor.py` 中承接复杂观测处理和奖励设计。
  - 若样本结构调整，需要同步 `definition.py` 中的 SampleData 维度定义。
- 来源：`开发文档/腾讯开悟强化学习框架/智能体/模型开发.md`
  - 模型可自由定义为 `torch.nn.Module`，允许从纯 MLP 升级到“结构化特征 + CNN 地图编码”混合网络。
- 来源：`开发文档/腾讯开悟强化学习框架/智能体/算法开发.md`
  - `learn(list_sample_data)` 接口足以承接保持 PPO 的策略更新，不要求切换算法家族。
- 来源：`开发文档/腾讯开悟强化学习框架/智能体/工作流开发.md`
  - workflow 中可叠加终局奖励、监控项，且 episode 级样本整理流程可继续复用。

### 4. 代码改动定位

- `train_test.py`
  - 不改算法入口名，继续使用 `ppo` 做 smoke test。

- `conf/app_conf_gorge_chase.toml`
  - 不改，继续挂载 `ppo`。

- `conf/algo_conf_gorge_chase.toml`
  - 不改，继续指向 `agent_ppo/`。

- `conf/configure_app.toml`
  - 首轮不动，先隔离算法变化。

- `agent_ppo/conf/conf.py`
  - 增加新特征维度、16 动作、地图编码尺寸、奖励系数与记忆参数。

- `agent_ppo/conf/train_env_conf.toml`
  - 首轮不改环境配置，保持与当前 baseline 可比。

- `agent_ppo/agent.py`
  - 适配 16 动作推理、合法动作 mask、可能新增的 preprocessor 状态。

- `agent_ppo/feature/preprocessor.py`
  - 本轮核心改动文件。
  - 新增目标记忆器、视野外目标估计、语义地图构造、闪现相关奖励、重复访问惩罚、目标优先级逻辑。

- `agent_ppo/feature/definition.py`
  - 更新 obs / legal_action / prob 等维度，保持 PPO 样本链路兼容。

- `agent_ppo/model/model.py`
  - 从纯扁平 MLP 地图编码升级为“结构化特征分支 + 局部地图 CNN 编码”。

- `agent_ppo/algorithm/algorithm.py`
  - 保持 PPO 主体，但适配更大的动作空间和可能更稳定的熵系数/学习率设定。

- `agent_ppo/workflow/train_workflow.py`
  - 调整终局奖励尺度；新增 episode 级监控，如闪现次数、宝箱数、最终 score。

#### 4.1 可参考的 `hok_prelim` 源代码实现

  - 目标记忆与状态汇总
    - 参考：`hok_prelim/code/agent_target_dqn/feature/state_manager.py`
    - 可借鉴内容：
      - `OrganManager` 的“视野内精确坐标 / 视野外方向距离估计 / 一旦发现后持续记忆”机制
      - `StateManager.update()` 中对 monster / organ / map / hero 的统一状态更新组织方式
    - 迁移注意：
      - 本项目环境协议字段名与王者初赛并不完全相同，不能直接复制字段访问代码，需要按 Gorge Chase 的 `FrameState` / `EnvInfo` 重写。

  - 局部语义地图
    - 参考：`hok_prelim/code/agent_target_dqn/feature/state_manager.py`
    - 可借鉴内容：
      - `MapManager.update_obstacles`
      - `MapManager.update_treasure`
      - `MapManager.update_buff`
      - `MapManager.get_around_feature`
      - `MapManager.get_around_memory`
    - 可直接借鉴的思想：
      - 用多通道地图分别表示障碍、访问记忆、目标点和风险/终点
      - 对视野外目标做“压到局部边界”的投影表达
    - 迁移注意：
      - `hok_prelim` 原实现是 `51x51` 局部图，本项目首轮缩到 `11x11`，只保留思路不保留原尺寸。

  - 分层奖励
    - 参考：`hok_prelim/code/agent_target_dqn/feature/state_manager.py`
    - 可借鉴内容：
      - `StateManager.get_reward()`
    - 可借鉴的奖励项：
      - 宝箱优先距离奖励
      - buff 获取奖励
      - 闪现距离奖励
      - 重复访问惩罚
      - 终局奖励与遗漏目标惩罚
    - 迁移注意：
      - 奖励数值不能原样照抄，需要根据本项目 PPO 的稳定性重新缩放。

  - 撞墙检测与动作屏蔽
    - 参考：`hok_prelim/code/agent_target_dqn/feature/state_manager.py`
    - 可借鉴内容：
      - `StateManager.get_action_mask()`
    - 可借鉴的机制：
      - 根据上一帧动作和当前位置变化判断是否撞墙
      - 暂时屏蔽已验证会撞墙的方向动作
    - 迁移注意：
      - 本项目已有环境原生 `legal_act`，所以这里只做“增强屏蔽”，不能替代环境 mask。

  - 16 动作接入方式
    - 参考：`hok_prelim/code/agent_target_dqn/agent.py`
    - 可借鉴内容：
      - `action_process()` 中 “移动方向 + 是否使用闪现” 合成单个离散动作的思路
    - 迁移注意：
      - 本项目当前是单整数动作接口，更适合直接保持 `0-15` 整数动作，不必保留 `move_dir/use_talent` 二段式结构。

  - 地图编码模型
    - 参考：`hok_prelim/code/agent_target_dqn/model/model.py`
    - 可借鉴内容：
      - `q_cnn` 这类轻量 CNN 编码局部地图，再与结构化 hero 特征融合
    - 迁移注意：
      - 保留 CNN + 结构化特征融合的骨架即可，不直接照搬 Q 网络输出头。

  - 稳定化网络层
    - 参考：
      - `hok_prelim/code/agent_target_dqn/model/simbaV2/agents/networks.py`
      - `hok_prelim/code/agent_target_dqn/model/simbaV2/agents/layers.py`
    - 可借鉴内容：
      - `l2normalize_network`
      - `HyperLERPBlock` 的稳定残差思想
    - 迁移注意：
      - 首轮不整体迁入 SimbaV2；若基础 CNN-PPO 版本跑通且收益明显，再考虑把其中的归一化残差块引入。

  - 训练 workflow 组织
    - 参考：`hok_prelim/code/agent_target_dqn/workflow/train_workflow.py`
    - 可借鉴内容：
      - episode 末尾集中上报监控指标
      - reward / hit_wall / explored 等统计项组织方式
    - 迁移注意：
      - 本项目 workflow 仍走 PPO 样本链路，不改成单机 `agent.learn(g_data)` 风格。

### 5. 环境配置设计

| 参数               | 当前值                   | 目标值 | 是否修改 | 原因                                         |
| ------------------ | ------------------------ | ------ | -------- | -------------------------------------------- |
| `map`              | `[1,2,3,4,5,6,7,8,9,10]` | 不变   | 否       | 保持多图训练，不把收益混入地图筛选。         |
| `map_random`       | `false`                  | 不变   | 否       | 当前先做算法迁移，不叠加训练分布变化。       |
| `treasure_count`   | `10`                     | 不变   | 否       | 新奖励设计本就围绕宝箱展开，保留满宝箱场景。 |
| `buff_count`       | `2`                      | 不变   | 否       | HOK 风格设计需要学习 buff 利用，不应先删减。 |
| `buff_cooldown`    | `200`                    | 不变   | 否       | 先与当前正式基线保持一致。                   |
| `talent_cooldown`  | `100`                    | 不变   | 否       | 接入闪现动作后直接学习标准冷却。             |
| `monster_interval` | `300`                    | 不变   | 否       | 不把环境难度调度与算法改动耦合。             |
| `monster_speedup`  | `500`                    | 不变   | 否       | 同上。                                       |
| `max_step`         | `1000`                   | 不变   | 否       | 与得分定义、正式评估一致。                   |

### 6. 系统训练配置设计

| 参数                             | 当前值                | 目标值 | 是否修改 | 原因                                       |
| -------------------------------- | --------------------- | ------ | -------- | ------------------------------------------ |
| `replay_buffer_capacity`         | `10000`               | 不变   | 否       | PPO 样本链路沿用，先不改系统容量。         |
| `preload_ratio`                  | `1.0`                 | 不变   | 否       | 不引入训练启动条件变量。                   |
| `reverb_remover`                 | `Fifo`                | 不变   | 否       | 当前训练框架已稳定。                       |
| `reverb_sampler`                 | `Uniform`             | 不变   | 否       | 首轮保持一致，避免把采样策略当成额外变量。 |
| `reverb_rate_limiter`            | `MinSize`             | 不变   | 否       | 先不改系统侧数据流。                       |
| `reverb_samples_per_insert`      | `5`                   | 不变   | 否       | 仅在切 limiter 策略时再重评。              |
| `reverb_error_buffer`            | `5`                   | 不变   | 否       | 同上。                                     |
| `train_batch_size`               | `2048`                | 不变   | 否       | 首轮优先验证可训练性，不先动批大小。       |
| `dump_model_freq`                | `100`                 | 不变   | 否       | 不影响算法对比。                           |
| `model_file_sync_per_minutes`    | `1`                   | 不变   | 否       | 不变更 Actor 拉模频率。                    |
| `modelpool_max_save_model_count` | `1`                   | 不变   | 否       | 无新增需要。                               |
| `preload_model`                  | `false`               | 不变   | 否       | 首轮不使用预训练。                         |
| `preload_model_dir`              | `"{agent_name}/ckpt"` | 不变   | 否       | 随 preload 配置一起保持。                  |
| `preload_model_id`               | `1000`                | 不变   | 否       | 同上。                                     |

### 7. 算法超参数设计

#### 7.1 现有参数改动

| 参数                       | 当前值           | 目标值             | 是否修改 | 原因                                                         |
| -------------------------- | ---------------- | ------------------ | -------- | ------------------------------------------------------------ |
| `FEATURES`                 | `[4,5,5,16,8,2]` | `[6,8,8,484,16,6]` | 是       | 扩展 hero/monster/progress，局部语义地图改为 `4x11x11=484`，动作 mask 扩到 16。 |
| `FEATURE_SPLIT_SHAPE`      | 同 `FEATURES`    | 同上               | 是       | 与新观测布局保持一致。                                       |
| `FEATURE_LEN`              | `40`             | `528`              | 是       | 新特征总维度。                                               |
| `DIM_OF_OBSERVATION`       | `40`             | `528`              | 是       | 与 `FEATURE_LEN` 对齐。                                      |
| `ACTION_NUM`               | `8`              | `16`               | 是       | 接入环境原生闪现动作。                                       |
| `VALUE_NUM`                | `1`              | `1`                | 否       | 先不引入多价值头，保持 PPO 简洁。                            |
| `GAMMA`                    | `0.99`           | `0.995`            | 是       | 更重视长时生存与寻宝收益。                                   |
| `LAMDA`                    | `0.95`           | `0.95`             | 否       | GAE 先保持稳定值。                                           |
| `INIT_LEARNING_RATE_START` | `3e-4`           | `2e-4`             | 是       | 更大模型 + 更密奖励下略降学习率。                            |
| `CLIP_PARAM`               | `0.2`            | `0.15`             | 是       | 更复杂动作空间下略收紧 PPO 更新。                            |
| `VF_COEF`                  | `1.0`            | `1.0`              | 否       | 保持基线。                                                   |
| `GRAD_CLIP_RANGE`          | `0.5`            | `0.5`              | 否       | 当前值已稳。                                                 |
| `TARGET_KL`                | `0.02`           | `0.015`            | 是       | 防止大模型初期策略震荡。                                     |
| `USE_ADVANTAGE_NORM`       | `True`           | `True`             | 否       | 保持。                                                       |
| `ADVANTAGE_NORM_EPS`       | `1e-8`           | `1e-8`             | 否       | 保持。                                                       |
| `BETA_START`               | `0.001`          | `0.003`            | 是       | 16 动作早期需要更强探索。                                    |
| `BETA_END`                 | `0.0002`         | `0.0005`           | 是       | 保持后期一定探索度。                                         |
| `BETA_DECAY_STEPS`         | `2000`           | `4000`             | 是       | 延长探索衰减过程。                                           |
| `SURVIVE_REWARD`           | `0.01`           | `0.005`            | 是       | 让奖励重心从纯存活转向任务目标。                             |
| `DIST_SHAPING_COEF`        | `0.1`            | `0.05`             | 是       | 降低“只远离怪物”单一偏好。                                   |
| `ENABLE_EXPLORE_BONUS`     | `True`           | `True`             | 否       | 保留探索激励。                                               |
| `EXPLORE_BONUS_SCALE`      | `0.02`           | `0.01`             | 是       | 语义地图 + 新奖励加入后，探索项适当降权。                    |
| `EXPLORE_BONUS_GRID_SIZE`  | `16`             | `16`               | 否       | 保持粗粒度探索计数。                                         |
| `EXPLORE_BONUS_MIN_RATIO`  | `0.25`           | `0.25`             | 否       | 保持。                                                       |
| `HERO_ENCODER_DIM`         | `16`             | `32`               | 是       | 承接更多 hero 状态。                                         |
| `MONSTER_ENCODER_DIM`      | `32`             | `64`               | 是       | 怪物特征包含估计位置/方向后信息量更大。                      |
| `MAP_ENCODER_DIM`          | `32`             | `128`              | 是       | 语义地图由 CNN 压缩到更高维表达。                            |
| `CONTROL_ENCODER_DIM`      | `16`             | `32`               | 是       | 16 动作 mask + 进度信息需要更大控制分支。                    |
| `FUSION_HIDDEN_DIM`        | `64`             | `128`              | 是       | 支撑更复杂融合表示。                                         |

#### 7.2 计划新增参数

- `LOCAL_MAP_SIZE = 11`
- `LOCAL_MAP_CHANNEL = 4`
- `TREASURE_REWARD = 1.0`
- `BUFF_REWARD = 0.3`
- `TREASURE_DIST_COEF = 0.08`
- `EXIT_DIST_COEF = 0.04`
- `FLASH_ESCAPE_REWARD_COEF = 0.05`
- `HIT_WALL_PENALTY = 0.05`
- `REVISIT_PENALTY_COEF = 0.02`
- `REVISIT_WINDOW_SIZE = 3`
- `TERMINATED_PENALTY = -12.0`
- `TRUNCATED_BONUS = 8.0`

新增参数原因：

- 现有配置不足以表达 HOK 风格的“宝箱优先、终点兜底、闪现脱险、局部防绕圈”奖励体系。
- 现有 `MAP_ENCODER_DIM` 只覆盖扁平 MLP，不足以表达新地图分支需要的卷积编码尺寸。

### 8. 特征设计细化

- `hero_feat (6D)`
  - `hero_x_norm`
  - `hero_z_norm`
  - `flash_cd_norm`
  - `buff_remain_norm`
  - `treasure_collected_ratio`
  - `step_norm`
- `monster_1 / monster_2 (8D x 2)`
  - `is_visible`
  - `est_x_norm`
  - `est_z_norm`
  - `speed_norm`
  - `dist_bucket_norm`
  - `dir_sin`
  - `dir_cos`
  - `active_flag`
- `semantic_map (4 x 11 x 11 = 484D)`
  - 通道 0：障碍物/可通行
  - 通道 1：访问记忆热度
  - 通道 2：宝箱/buff 目标图
  - 通道 3：怪物风险/终点引导图
- `legal_action (16D)`
  - 全动作合法掩码。
- `progress_feat (6D)`
  - `survival_ratio`
  - `remaining_treasure_ratio`
  - `buff_collected_ratio`
  - `flash_used_ratio`
  - `target_treasure_available`
  - `target_buff_available`

### 9. 模型结构设计

- 保持 Actor-Critic + PPO。
- 模型改为三路融合：
  - 结构化 hero / monster / progress 分支：MLP。
  - 语义地图分支：小型 CNN 编码 `4x11x11` 地图，再映射到 `MAP_ENCODER_DIM=128`。
  - 动作控制分支：`legal_action + progress` 编码。
- 融合后输出：
  - Actor head: `128 -> 16`
  - Critic head: `128 -> 1`

### 10. 奖励设计

- 即时奖励由以下部分组成：
  - 基础生存奖励：弱化但保留。
  - 怪物距离 shaping：保留，权重降低。
  - 宝箱接近奖励：优先鼓励接近最近可收集宝箱。
  - buff 获取奖励：次级正奖励。
  - 闪现脱险奖励：只有在高风险状态下拉开怪物距离才给正反馈。
  - 撞墙/无效位移惩罚：惩罚卡墙和原地抖动。
  - 重复访问惩罚：惩罚局部 3x3 邻域反复打转。
  - 探索奖励：保留但降权。
- 终局奖励：
  - 被怪物抓到：更强负奖励。
  - 存活到上限：正奖励，但弱于完整宝箱路线的累计收益。

### 11. 代码实现计划

1. 先改 `agent_ppo/conf/conf.py`
   - 补全新特征尺寸、动作数、地图参数、奖励参数。
2. 再改 `agent_ppo/feature/preprocessor.py`
   - 加入目标记忆器、方向距离估计、局部语义地图构造、16 维 legal action、分层奖励。
3. 同步改 `agent_ppo/model/model.py`
   - 引入 CNN 地图编码器并调整融合头。
4. 再改 `agent_ppo/feature/definition.py`
   - 更新样本维度，保证 `obs / legal_action / prob` 与新模型一致。
5. 视需要微调 `agent_ppo/agent.py`
   - 确保 16 动作采样、mask 和 exploit 路径正确。
6. 最后改 `agent_ppo/workflow/train_workflow.py`
   - 调整终局奖励、补监控项。
7. smoke test
   - 先跑 `python train_test.py`
   - 若通过，再进入平台正式训练。

### 12. 风险

- `ACTION_NUM` 从 8 改到 16 后，动作分布会明显变稀，若熵系数过低会早期塌缩。
- 语义地图和目标记忆若构造错误，最容易直接导致 smoke test 失败或 reward 爆炸。
- 视野外目标估计依赖 `hero_relative_direction` 与距离桶转换，若方向映射搞错，会产生系统性错误导航。
- 奖励项变多后，如果系数量级不平衡，PPO 可能学成“刷奖励但不提分”的策略。
- 局部地图用 11x11 而不是 `hok_prelim` 的 51x51，是出于本赛题原生视野只有 21x21 的约束；不能生搬更大地图窗口。

### 13. 验证方案

- smoke test：
  - `python train_test.py`
  - 重点确认：
    - 观测维度、模型前向和 PPO 更新无 shape 错误
    - 16 动作 legal mask 正常
    - reward 数值范围没有异常爆炸
    - 模型能成功保存/加载
- 正式训练关注指标：
  - `total_score`
  - `treasures_collected`
  - `flash_count`
  - `reward`
  - `episode_steps`
  - 新增监控中的 `treasure_reward`、`flash_escape_reward`、`revisit_penalty`
- 与当前 baseline 的对比标准：
  - 是否更早开始稳定收集宝箱
  - 是否出现可观察的闪现利用
  - 是否减少原地绕圈和贴墙抖动
  - 在不降低生存步数的前提下抬高总得分

## 当前实现进度

- 已完成 `hok_prelim` 调研方向到 Gorge Chase PPO 的落地设计。
- 已补充查阅 `hok_prelim` 真实源码：
  - `agent.py`
  - `algorithm/algorithm.py`
  - `feature/state_manager.py`
  - `model/model.py`
  - `model/simbaV2/*`
  - `workflow/train_workflow.py`
- 已确认本轮不切换算法家族，保留 `agent_ppo/` 与 `ppo` 入口，先迁移“记忆地图 + 分层奖励 + 闪现接入”。
- 经过源码核对后的进一步判断：
  - 应保留：`StateManager` 式目标记忆、局部语义地图、局部重复访问惩罚、闪现动作接入、撞墙动作屏蔽、分层奖励。
  - 不应直接照搬：DDQN + target network、epsilon-greedy 主探索、完整 SimbaV2 critic、`51x51` 大窗口全量局部图、王者赛道特有的起点/终点协议实现。
  - 可做轻量借鉴：CNN 地图编码骨架，以及 SimbaV2 中 “L2 归一化 + 稳定残差块” 的思想，但首轮实现不把整个 SimbaV2 包整体迁入本项目。
- 已完成源码落点、文档依据、参数设计和 smoke test 路径规划。
- 尚未开始代码实现。

## 下一步计划

- 直接进入 `/kaiwu-algo-implementation`。
- 第一实现批次优先改：
  - `agent_ppo/conf/conf.py`
  - `agent_ppo/feature/preprocessor.py`
  - `agent_ppo/model/model.py`
- 第一轮实现后立即跑 `python train_test.py` 做烟测，再补 `definition.py` / `workflow.py` 的联动修正。
