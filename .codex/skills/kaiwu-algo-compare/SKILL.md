---
name: kaiwu-algo-compare
description: Compare a candidate algorithm or external reference with the current Gorge Chase baseline. Use when evaluating ideas from GLOBAL_DOCS/算法调研.md, reference_algos/, historical algorithm docs, or a user-described algorithm before deciding whether to design or implement it.
allowed-tools: Read, Grep, Glob
---

# KaiWu Algo Compare

比较目标：$ARGUMENTS

## 目标

把“候选算法值不值得做”回答清楚，而不只是罗列差异。

这个 skill 的职责是：

- 独立抽取当前 baseline 快照
- 读取候选算法来源
- 把两者放到同一坐标系下比较
- 给出收益、风险、改动范围和是否建议进入下一步设计

## 重要边界

- **不要把 `/kaiwu-current-algo-analysis` 当作前置依赖**
- 可以参考它的读取顺序、快照结构和输出风格
- 但本 skill 必须能单独完成 baseline 提取与比较
- 只做分析判断，不改代码，不写 `DEV_MEMORY/NOW.md`

## 适用输入

这个 skill 适合比较以下几类候选方案：

1. `GLOBAL_DOCS/算法调研.md` 中的人类调研方向
2. `reference_algos/<算法名>/` 中的外部参考实现
3. `GLOBAL_DOCS/算法文档/` 中的历史算法版本
4. 用户直接口述的算法想法，例如 “加 LSTM” “改成 DQN” “接入 attention memory”

若用户给出的候选方案信息不完整，也可以先做初步比较，但必须明确标出哪些结论是推断而不是仓库内已验证事实。

## 默认分析策略

先做“最小可用比较”，必要时再下钻源码。

默认顺序：

1. 先抽取当前 baseline 的身份、设计和关键配置
2. 再定位候选算法的主要思路、接口形态和工程实现
3. 再判断两者在本仓库中的适配成本、风险和潜在收益
4. 最后给出是否值得进入 `/kaiwu-algo-design`

## Step 1：抽取当前 baseline

至少按下面顺序读取：

1. `GLOBAL_DOCS/算法总表.md`
2. 当前 baseline 对应正式算法文档
3. `conf/app_conf_gorge_chase.toml`
4. `conf/algo_conf_gorge_chase.toml`
5. `agent_ppo/conf/conf.py`
6. `agent_ppo/conf/train_env_conf.toml`
7. `conf/configure_app.toml`

若需要补充实现细节，再读取：

8. `train_test.py`
9. `agent_ppo/agent.py`
10. `agent_ppo/feature/preprocessor.py`
11. `agent_ppo/feature/definition.py`
12. `agent_ppo/model/model.py`
13. `agent_ppo/algorithm/algorithm.py`
14. `agent_ppo/workflow/train_workflow.py`

## Step 2：读取候选算法来源

根据输入类型选择最小必要来源。

### A. 来自 `GLOBAL_DOCS/算法调研.md`

至少读取：

- `GLOBAL_DOCS/算法调研.md`
- 若文档中指向了具体参考目录，再补读对应 `reference_algos/<算法名>/README.md`

### B. 来自 `reference_algos/<算法名>/`

至少读取：

1. `reference_algos/<算法名>/README.md`
2. `reference_algos/<算法名>/code/agent.py`
3. `reference_algos/<算法名>/code/feature/` 下的核心特征处理文件
4. `reference_algos/<算法名>/code/model/model.py`
5. `reference_algos/<算法名>/code/algorithm/algorithm.py`
6. `reference_algos/<算法名>/code/workflow/train_workflow.py`

若目录结构不同，按“Agent / feature / model / algorithm / workflow”职责寻找等价文件。

### C. 来自历史正式算法文档

至少读取：

- 目标算法对应的 `GLOBAL_DOCS/算法文档/<算法完整名>/README.md`
- 必要时补充其归档时关联的实现说明

### D. 来自用户口述

先提炼出下面几个最基本的候选信息：

- 算法框架
- 预期改动点
- 是否改动作空间
- 是否改特征 / 记忆 / 模型
- 是否改奖励 / workflow / 训练配置

如果缺少这些信息，可以先按“最可能的实现形态”做比较，但必须标注假设。

## 必须比较的维度

默认至少覆盖以下维度：

### 1. 算法身份

- 当前 baseline 是什么
- 候选算法是什么
- 两者属于“调参级改动 / 结构级改动 / 算法范式切换”中的哪一类

### 2. 赛题匹配度

- 是否更适合 Gorge Chase 的生存 + 拿箱子目标
- 是否更适合当前观测协议、动作空间和奖励形态
- 是否依赖赛题中并不存在的额外信号

### 3. 特征与状态表示

- 当前 baseline 用什么特征
- 候选算法需要什么额外特征 / 记忆 / 序列状态
- 是否需要新增缓存、时序状态或全局地图表示

### 4. 动作空间与决策方式

- 是否保持当前动作空间
- 是否需要修改 `ACTION_NUM`
- 是否改变 legal action mask、闪现策略或采样方式

### 5. 奖励设计

- 是否继续沿用现有 reward shaping
- 是否需要新增奖励项
- 是否会让 reward credit assignment 变得更难

### 6. 模型结构

- MLP / CNN / LSTM / attention / memory module 有何差异
- 对当前 `agent_ppo/model/model.py` 的侵入性多大

### 7. 训练与样本链路

- 是否仍兼容当前 `SampleData`、GAE、PPO 更新流程
- 是否需要重写 `algorithm.py` 或 `workflow/train_workflow.py`
- 是否需要改 `conf/configure_app.toml` 的系统训练参数

### 8. 工程落地成本

- 主要改哪些文件
- 改动是局部还是全链路
- smoke test 风险高不高

### 9. 风险与收益

- 预期收益是什么：更高存活、更稳定拿箱子、更合理使用闪现、更强泛化
- 主要风险是什么：不稳定、样本效率低、超参敏感、实现复杂、难排障

## 对 `reference_algos/` 的额外要求

如果候选方案来自外部参考实现，必须显式说明：

1. 哪些思路可以迁移
2. 哪些实现只能借鉴，不能直接照搬
3. 外部实现到本仓库 `agent_ppo/` 的映射关系

推荐补一个映射表：

| 外部组件 | 当前仓库落点 | 迁移判断 |
| --- | --- | --- |
| `agent.py` | `agent_ppo/agent.py` | 可直接迁移 / 需适配 / 不建议 |
| `feature/...` | `agent_ppo/feature/...` | 可直接迁移 / 需适配 / 不建议 |
| `model/model.py` | `agent_ppo/model/model.py` | 可直接迁移 / 需适配 / 不建议 |
| `algorithm/algorithm.py` | `agent_ppo/algorithm/algorithm.py` | 可直接迁移 / 需适配 / 不建议 |
| `workflow/train_workflow.py` | `agent_ppo/workflow/train_workflow.py` | 可直接迁移 / 需适配 / 不建议 |

## 输出要求

输出时必须优先回答下面这些问题：

### 1. 当前 baseline 快照

- 当前启用算法 key
- 当前正式算法完整名
- 当前状态：baseline / 已实现 / smoke test / 是否有正式训练结果

### 2. 候选算法快照

- 候选算法核心思路
- 来源：调研 / 外部参考 / 历史版本 / 用户口述
- 候选方案最可能影响哪些模块

### 3. 差异比较

至少对比：

- 算法框架
- 特征设计
- 动作空间
- 奖励设计
- 模型结构
- 训练链路
- 环境 / 系统配置联动

### 4. 落地成本评估

至少说明：

- 主要改动文件
- 改动规模：低 / 中 / 高
- 与当前 baseline 的兼容性：高 / 中 / 低

### 5. 最终建议

必须明确给出结论，而不是停在“可以试试”：

- **建议立即进入设计**
- **建议先做小范围原型验证**
- **暂不建议投入实现**

并说明理由。

## 推荐输出模板

```markdown
## 算法比较结论

### 1. 当前 baseline
- 启用算法：
- 正式算法完整名：
- 当前状态：

### 2. 候选算法
- 来源：
- 核心思路：
- 预期收益：

### 3. 关键差异对比
| 维度 | 当前 baseline | 候选算法 | 判断 |
| --- | --- | --- | --- |
| 算法框架 | | | |
| 特征设计 | | | |
| 动作空间 | | | |
| 奖励设计 | | | |
| 模型结构 | | | |
| 训练链路 | | | |

### 4. 落地成本
| 项目 | 评估 |
| --- | --- |
| 主要改动文件 | |
| 改动规模 | 低 / 中 / 高 |
| 接口兼容性 | 高 / 中 / 低 |
| smoke test 风险 | 低 / 中 / 高 |

### 5. 风险与收益
- 收益：
- 风险：

### 6. 结论
- 是否建议继续：
- 推荐下一步：
```

## 规则

- 默认优先使用“正式算法文档 + 配置文件 + 候选来源文档”完成比较
- 只有在信息不足时，才下钻源码
- 若候选方案信息不完整，必须明确哪些结论是推断
- 若 baseline 文档、配置和源码不一致，必须明确指出
- 不把“理论上更先进”直接等同于“更适合当前仓库”
- 分析结论必须落到当前仓库的现实约束：`agent_ppo/` 接口、KaiWu workflow、Gorge Chase 环境协议、现有 528 维 / 16 动作主线

---

## 下一步行动（执行后必须输出）

比较完成后，明确告诉用户下一步该做什么：

```markdown
## 比较完成 - 建议下一步

| 场景 | 推荐行动 |
|------|---------|
| 候选方向明显优于当前 baseline，且落地成本可控 | 使用 `/kaiwu-algo-design` 把方案写入 `DEV_MEMORY/NOW.md` |
| 候选方向有潜力，但不确定收益是否覆盖复杂度 | 先做小范围原型设计，再决定是否进入 `/kaiwu-algo-design` |
| 只需要进一步理解当前 baseline | 使用 `/kaiwu-current-algo-analysis` |
| 发现候选方案与当前仓库约束不兼容 | 暂不进入实现，继续调研或更换方向 |
```
