---
name: kaiwu-algo-design
description: Design a concrete algorithm iteration plan for the Gorge Chase KaiWuDRL repository. The design must be grounded in development docs, environment configuration, source-code entry points, and tunable hyperparameters.
argument-hint: [algorithm-goal-or-idea]
allowed-tools: Read, Grep, Glob, Edit, Write
---

# KaiWu Algo Design

设计目标：$ARGUMENTS

## 目标

在进入代码实现前，把“想做什么”细化为“准备改什么、为什么改、需要设计哪些参数、这些参数落在哪些文件”。

这个 skill 不能只给抽象思路，必须结合项目源码和 `开发文档/` 输出可落地设计。

## 前置要求

- 当前是否在继续上一轮开发

- 当前 baseline 与正式算法文档是什么

- `DEV_MEMORY/NOW.md` 是否已有未完成任务

- 当前工作分支和 git 状态是否适合继续开发

- 当前是否已经位于本轮开发对应的 `feature/*` 分支

若未执行 `/kaiwu-dev-init`，先补做初始化，不直接进入设计。

若当前不在 `feature/*` 分支，停止当前 skill，并先创建或切换分支：

\- `git checkout -b feature/<topic>`

\- 或 `git checkout feature/<topic>`

## 必读文档

至少按下面顺序读取：

1. `开发文档/README.md`
2. `开发文档/开发指南/环境详述.md`
3. `开发文档/开发指南/数据协议.md`
4. `开发文档/开发指南/智能体详述.md`
5. `开发文档/腾讯开悟强化学习框架/智能体/特征处理.md`
6. `开发文档/腾讯开悟强化学习框架/智能体/模型开发.md`
7. `开发文档/腾讯开悟强化学习框架/智能体/算法开发.md`
8. `开发文档/腾讯开悟强化学习框架/智能体/工作流开发.md`

如果设计涉及训练调度或样本池，还要补读：

- `开发文档/腾讯开悟强化学习框架/分布式计算框架.md`
- `开发文档/腾讯开悟强化学习框架/监控与日志.md`

## 必读外部参考源码

如果本轮设计涉及参考外部调研算法（如 `hok_prelim`），必须同时查阅：

1. `GLOBAL_DOCS/算法调研.md` - 了解外部算法的整体说明
2. `reference_algos/<算法名>/README.md` - 该算法的详细说明
3. `reference_algos/<算法名>/code/` 下的核心源码文件：
   - `agent.py` - Agent 接口与动作处理
   - `feature/` 或 `feature/state_manager.py` - 特征处理与奖励设计
   - `model/model.py` - 网络结构定义
   - `algorithm/algorithm.py` - 训练逻辑
   - `workflow/train_workflow.py` - 训练流程

**设计要求**：

- 明确标注哪些思路来自外部参考源码
- 说明哪些组件可直接迁移、哪些需要适配、哪些不适合本项目
- 给出外部源码到本项目 `agent_ppo/` 的映射关系

## 必须确认的源码入口

在设计里至少定位到这些文件：

- `train_test.py`
- `conf/app_conf_gorge_chase.toml`
- `conf/algo_conf_gorge_chase.toml`
- `conf/configure_app.toml`
- `agent_ppo/conf/conf.py`
- `agent_ppo/conf/train_env_conf.toml`
- `agent_ppo/agent.py`
- `agent_ppo/feature/preprocessor.py`
- `agent_ppo/feature/definition.py`
- `agent_ppo/model/model.py`
- `agent_ppo/algorithm/algorithm.py`
- `agent_ppo/workflow/train_workflow.py`

## 设计时必须补全的参数

### 1. 环境配置参数

文件：`agent_ppo/conf/train_env_conf.toml`

设计时必须逐项判断是否需要改动，并说明目标值、取值理由、风险：

| 参数 | 默认值 | 范围/说明 |
| --- | --- | --- |
| `map` | `[1,2,3,4,5,6,7,8,9,10]` | 训练地图列表，范围 `1-10` |
| `map_random` | `false` | 是否随机抽图 |
| `treasure_count` | `10` | 范围 `0-10` |
| `buff_count` | `2` | 范围 `0-2` |
| `buff_cooldown` | `200` | 范围 `1-500` |
| `talent_cooldown` | `100` | 闪现冷却，范围 `50-2000` |
| `monster_interval` | `300` | 第二只怪出现时间，范围 `-1, 11-2000` |
| `monster_speedup` | `500` | 怪物加速时间，范围 `-1, 1-2000` |
| `max_step` | `1000` | 单局最大步数，范围 `1-2000` |

### 2. 系统训练配置参数

文件：`conf/configure_app.toml`

设计时至少评估以下参数是否需要联动修改：

| 参数 | 默认值 | 设计关注点 |
| --- | --- | --- |
| `replay_buffer_capacity` | `10000` | 样本池容量 |
| `preload_ratio` | `1.0` | 触发训练的装载比例 |
| `reverb_remover` | `reverb.selectors.Fifo` | 旧样本淘汰策略 |
| `reverb_sampler` | `reverb.selectors.Uniform` | Learner 采样策略 |
| `reverb_rate_limiter` | `MinSize` | 样本插入/采样节流策略 |
| `reverb_samples_per_insert` | `5` | 仅 `SampleToInsertRatio` 生效 |
| `reverb_error_buffer` | `5` | 仅 `SampleToInsertRatio` 生效 |
| `train_batch_size` | `2048` | 训练 batch 大小 |
| `dump_model_freq` | `100` | 模型导出频率 |
| `model_file_sync_per_minutes` | `1` | Actor 拉取模型频率 |
| `modelpool_max_save_model_count` | `1` | 每次推送/拉取模型数 |
| `preload_model` | `false` | 是否加载预训练模型 |
| `preload_model_dir` | `"{agent_name}/ckpt"` | 预加载模型目录 |
| `preload_model_id` | `1000` | 预加载模型 step id |

### 3. 算法超参数

文件：`agent_ppo/conf/conf.py`

至少要明确哪些参数保持不变、哪些要改：

| 类别 | 参数 |
| --- | --- |
| 观测/动作 | `FEATURES`, `FEATURE_SPLIT_SHAPE`, `FEATURE_LEN`, `DIM_OF_OBSERVATION`, `ACTION_NUM`, `VALUE_NUM` |
| RL 核心超参 | `GAMMA`, `LAMDA`, `INIT_LEARNING_RATE_START`, `CLIP_PARAM`, `VF_COEF`, `GRAD_CLIP_RANGE`, `TARGET_KL` 等 |
| 稳定化 | `USE_ADVANTAGE_NORM`, `ADVANTAGE_NORM_EPS` |
| 熵系数 | `BETA_START`, `BETA_END`, `BETA_DECAY_STEPS` |
| 奖励 | `SURVIVE_REWARD`, `DIST_SHAPING_COEF`, `ENABLE_EXPLORE_BONUS`, `EXPLORE_BONUS_SCALE`, `EXPLORE_BONUS_GRID_SIZE`, `EXPLORE_BONUS_MIN_RATIO` |
| 编码结构 | `HERO_ENCODER_DIM`, `MONSTER_ENCODER_DIM`, `MAP_ENCODER_DIM`, `CONTROL_ENCODER_DIM`, `FUSION_HIDDEN_DIM` |

### 4. 代码改动定位参数

设计中要把参数映射到对应源码文件：

| 设计内容 | 主要文件 |
| --- | --- |
| 观测特征、合法动作、即时奖励 | `agent_ppo/feature/preprocessor.py` |
| 样本结构、GAE、回报计算 | `agent_ppo/feature/definition.py` |
| 模型结构 | `agent_ppo/model/model.py` |
| 算法 loss 与优化 | `agent_ppo/algorithm/algorithm.py` |
| Agent 接口与推理/训练调用 | `agent_ppo/agent.py` |
| 训练流程、终局奖励、监控上报 | `agent_ppo/workflow/train_workflow.py` |

## 输出要求

输出的设计结果必须包含：

1. 本轮目标与要验证的主假设
2. 与当前 baseline 的差异
3. 需要查询的开发文档依据
4. 需要改动的源码文件清单
5. 环境配置参数设计表
6. 系统训练配置参数设计表
7. 算法超参数设计表
8. 风险与验证方案

## 推荐输出模板

```markdown
## 本轮算法设计：<名称>

### 1. 目标
- 这轮准备验证什么主假设

### 2. 文档依据
- 来源：`开发文档/...`
- 关键约束：

### 3. 代码改动定位
- `agent_ppo/...`
- `conf/...`

### 4. 环境配置设计
| 参数 | 当前值 | 目标值 | 是否修改 | 原因 |
| --- | --- | --- | --- | --- |

### 5. 系统训练配置设计
| 参数 | 当前值 | 目标值 | 是否修改 | 原因 |
| --- | --- | --- | --- | --- |

### 6. 算法超参数设计
| 参数 | 当前值 | 目标值 | 是否修改 | 原因 |
| --- | --- | --- | --- | --- |

### 7. 代码实现计划
1. 先改哪些文件
2. 再改哪些文件
3. 如何做 smoke test

### 8. 风险
- 可能影响什么

### 9. 验证方案
- smoke test：
- 正式训练关注指标：
```

## 规则

- 不跳过开发文档依据
- 不给”只改奖励/只调超参”这类空泛建议，必须落到参数名和文件路径
- 一轮设计默认只验证一个主方向
- 若设计会改 `ACTION_NUM`、特征维度或样本结构，必须显式说明联动修改链路

---

## 下一步行动（执行后必须输出）

设计完成后，明确告诉用户：

```markdown
## 设计完成 - 下一步

设计已记录到 `DEV_MEMORY/NOW.md`。

接下来请执行：

1. **检查设计完整性**：确认所有参数表、改动文件清单、风险项已填写
2. **切到 feature 分支**（如尚未）：`git checkout -b feature/<算法名>`
3. **开始实现**：使用 `/kaiwu-algo-implementation`

如果设计涉及参考 `reference_algos/` 中的外部算法，实现阶段会引导你查阅具体源码。
```
