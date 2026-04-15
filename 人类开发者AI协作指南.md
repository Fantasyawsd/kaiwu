# 人类开发者 AI 协作指南

本文件面向使用 Codex、Claude Code 等 AI 开发工具的人类开发者。

它回答的不是算法细节本身，而是更实际的问题：

- 这个项目到底要做什么
- 项目结构是什么，应该先看哪里
- 人自己负责什么，AI 负责什么
- 想改奖励、特征、网络、超参数时该改哪些文件
- 应该用什么提示词和命令驱动 AI 去迭代算法
- Git 应该怎么协作
- 一轮完整算法迭代里，人和 AI 分别在什么阶段做什么


---

# **开发第一步：/kaiwu-dev-init !!!**

## 1. 项目在做什么

这是腾讯开悟 Gorge Chase / 峡谷追猎强化学习代码包。

当前项目目标是：训练一个智能体控制鲁班七号，在 `128x128` 栅格地图中躲避怪物、收集宝箱，并尽量存活到最大步数。

当前仓库里的正式算法基线是：

- 算法名：`ppo`
- 正式实现目录：`agent_ppo/`
- 当前完整算法名：`agent_ppo_20260409_1733`
- 当前状态：历史 smoke test 已通过，暂无正式训练得分

重要约束：

- 所有正式算法迭代默认都在 `agent_ppo/` 里做
- `agent_diy/` 只是模板参考，不是正式算法落库目录
- README 不维护细粒度算法实现，算法当前状态以 `GLOBAL_DOCS/算法总表.md` 和对应正式算法文档为准

---

## 2. 先看什么

如果你是第一次接手这个仓库，建议按下面顺序阅读：

1. [人类开发者前置知识.md](人类开发者前置知识.md)
2. [README.md](README.md)
3. [KAIWU-WORKFLOW.md](KAIWU-WORKFLOW.md)
4. [GLOBAL_DOCS/算法总表.md](GLOBAL_DOCS/算法总表.md)
5. [GLOBAL_DOCS/算法文档/agent_ppo_20260409_1733/README.md](GLOBAL_DOCS/算法文档/agent_ppo_20260409_1733/README.md)
6. [开发文档/README.md](开发文档/README.md)
7. [CONTRIBUTE.md](CONTRIBUTE.md)

说明：

- 本文第 7 节已经融合 `CONTRIBUTE.md` 的核心规则
- 如果你只想快速开工，可以直接读本文，不必把 `CONTRIBUTE.md` 当成前置必读

如果不是第一次接手，而是继续上一轮工作，额外先看：

1. [DEV_MEMORY/NOW.md](DEV_MEMORY/NOW.md)

简单理解：

- `GLOBAL_DOCS/` 看“长期稳定事实”
- `DEV_MEMORY/NOW.md` 看“当前这一轮做到哪了”
- `开发文档/` 看“官方环境规则、协议和框架接口”

### 2.1 开工前 checklist

在开始任何非微小改动前，至少完成下面这些动作：

1. `git pull`
2. `git status`
3. 如果当前在 `main`，优先切到 `feature/<topic>` 分支
4. 阅读 `README.md`、`KAIWU-WORKFLOW.md`、`GLOBAL_DOCS/算法总表.md`
5. 如果本轮是新方向，先看 `GLOBAL_DOCS/算法调研.md`
6. 如果本轮是继续已有工作，先看 `DEV_MEMORY/NOW.md`
7. 明确这轮只验证一个主方向，不要同时改太多东西

---

## 3. 目录结构和关键文件

### 3.1 最重要的目录

| 路径 | 作用 |
| --- | --- |
| `agent_ppo/` | 正式算法实现目录，真正要改的核心代码都在这里 |
| `agent_diy/` | 模板目录，只参考，不作为正式算法落库位置 |
| `conf/` | 平台算法选择、算法映射、系统训练配置 |
| `开发文档/` | 官方文档，回答环境规则、字段协议、框架接口问题 |
| `GLOBAL_DOCS/` | 全局稳定知识库 |
| `DEV_MEMORY/` | 当前轮次状态记忆，方便 AI 断线重连和快速接手 |

### 3.2 代码入口链路

```text
train_test.py
-> conf/app_conf_gorge_chase.toml
-> conf/algo_conf_gorge_chase.toml
-> agent_ppo/conf/conf.py
-> agent_ppo/conf/train_env_conf.toml
-> agent_ppo/agent.py
-> agent_ppo/feature/preprocessor.py
-> agent_ppo/feature/definition.py
-> agent_ppo/model/model.py
-> agent_ppo/algorithm/algorithm.py
-> agent_ppo/workflow/train_workflow.py
```

### 3.3 改什么去哪里改

| 目标 | 主要文件 |
| --- | --- |
| 改特征工程、合法动作、即时奖励 | `agent_ppo/feature/preprocessor.py` |
| 改样本结构、GAE、回报计算 | `agent_ppo/feature/definition.py` |
| 改网络结构 | `agent_ppo/model/model.py` |
| 改 PPO loss、优化流程 | `agent_ppo/algorithm/algorithm.py` |
| 改算法超参数 | `agent_ppo/conf/conf.py` |
| 改训练 workflow、终局奖励、模型保存 | `agent_ppo/workflow/train_workflow.py` |
| 改训练环境配置 | `agent_ppo/conf/train_env_conf.toml` |
| 改系统训练配置 | `conf/configure_app.toml` |
| 切换平台启用算法 | `conf/app_conf_gorge_chase.toml` + `conf/algo_conf_gorge_chase.toml` |

---

## 4. 人负责什么，AI 负责什么

### 4.1 人类开发者主要负责

- 决定本轮优化目标和主假设
- 做外部调研，决定要不要尝试新方向
- 当候选方向不止一个时，决定要比较哪些候选算法、参考实现或历史版本
- 决定是否继续当前方向，还是切换方向
- 启动平台真实训练，观察监控和日志
- 从官方训练监控导出训练全部曲线 HTML 文档，并放入对应算法文档目录的 `html/`
- 在官网上传模型；后续归档默认以 `html/` 中 HTML 文档文件名（去掉扩展名）作为上传到官网的模型全称
- 对开放 10 张地图执行 5 次官方评估，并把测试 HTML 文档也放入同一个 `html/` 目录
- 人不再额外补填模型名、HTML 文档位置或说明；AI 只检测 `html/` 里是否有 HTML 文档
- 记录正式实验结果
- 最终决定是否 commit、push、merge

### 4.2 AI 主要负责

- 阅读仓库文档和官方开发文档
- 分析当前基线实现和代码入口
- 比较候选算法、`reference_algos/` 或历史算法版本与当前 baseline 的差异、收益、风险和落地成本
- 完成代码修改
- 跑最小验证，比如 `python3 train_test.py`
- 把当前状态同步到 `DEV_MEMORY/NOW.md`
- 基于人提供的真实训练结果、10 张地图得分和 HTML 文档，在结论稳定后整理到 `GLOBAL_DOCS/算法总表.md` 与 `GLOBAL_DOCS/算法文档/*`
- 生成 commit 建议、整理变更说明

### 4.3 边界要说清

- 人提方向，AI 负责落地
- AI 不能虚构训练结果
- AI 不能跳过文档同步
- 正式训练结果以人跑出来的平台结果为准
- 正式 push / merge 之前必须有人确认

---

## 5. 怎么驱动 AI

这里分两种情况。

### 5.1 工具支持 repo-local skills 时

如果你的 AI 工具支持读取仓库里的 skills，优先使用这套顺序：

```text
/kaiwu-dev-init
/kaiwu-doc-query
/kaiwu-current-algo-analysis
/kaiwu-algo-compare
/kaiwu-algo-design
/kaiwu-algo-implementation
/kaiwu-memory-archive
```

推荐提示词示例：

#### 1. 初始化仓库状态

```text
/kaiwu-dev-init

目标：确认当前仓库状态、当前算法入口、当前是否有未完成任务。先不要改代码。
```

#### 2. 分析当前基线

```text
/kaiwu-current-algo-analysis ppo

重点告诉我：
1. 当前算法入口链路
2. 想改奖励/特征/网络/超参数分别改哪些文件
3. 当前实现有哪些已知限制
```

#### 3. 开始一轮实现

```text
/kaiwu-algo-compare

目标：把 `GLOBAL_DOCS/算法调研.md` / `reference_algos/` / 你口述的候选方案，与当前 baseline 做比较。

重点告诉我：
1. 候选方向和当前 baseline 的关键差异
2. 预期收益和主要风险
3. 主要改动文件和落地成本
4. 是否值得进入 /kaiwu-algo-design
```

#### 4. 把候选方向落成设计

```text
/kaiwu-algo-design

目标：把确认要做的候选方向写成可实现方案，并补齐环境配置、系统训练配置和算法超参数。
```

#### 5. 开始一轮实现

```text
/kaiwu-algo-implementation

目标：在 agent_ppo 中优化 xxx。

要求：
1. 先读 README、KAIWU-WORKFLOW、GLOBAL_DOCS/算法总表、DEV_MEMORY/NOW.md、开发文档/README
2. 只改 agent_ppo/ 里的正式实现，不要把正式改动做在 agent_diy/
3. 改完后运行 python3 train_test.py 做 smoke test
4. 同步 DEV_MEMORY/NOW.md
5. 暂时不要 push
```

#### 6. 收口和归档

```text
/kaiwu-memory-archive

请把本轮稳定结论归档到 GLOBAL_DOCS，并同步算法总表和正式算法文档
```

### 5.2 工具不支持 skills 时

如果你用的是通用型 Codex 或其他 AI 工具，没有 slash skills，也可以直接用下面的 prompt 模板。

#### 模板 A：先分析，不直接改代码

```text
先不要改代码。请先阅读以下文件：

README.md
KAIWU-WORKFLOW.md
人类开发者AI协作指南.md
GLOBAL_DOCS/算法总表.md
GLOBAL_DOCS/算法文档/agent_ppo_20260409_1733/README.md
开发文档/README.md
DEV_MEMORY/NOW.md

读完后只输出：
1. 当前项目目标
2. 当前算法入口链路
3. 如果我要改奖励/特征/网络/超参数，各该改哪些文件
4. 当前是否存在未完成的轮次任务
5. 建议的下一步
```

#### 模板 B：让 AI 开始改代码

```text
目标：在 agent_ppo 中尝试 xxx。

要求：
1. 正式实现只改 agent_ppo/，不要把正式实现放到 agent_diy/
2. 改代码前先复述将修改哪些文件、为什么改这些文件
3. 改完后运行最小验证命令
4. 同步 DEV_MEMORY/NOW.md
5. 如果结论已经稳定，再更新 GLOBAL_DOCS/算法总表.md 和正式算法文档
6. 不要编造训练分数
7. 不要 push，先给我 diff 摘要和验证结果
```

#### 模板 C：喂给 AI 一轮训练结果

```text
我已经跑完一轮正式训练，并把训练/测试 HTML 文档放到对应算法文档目录的 `html/` 里了。

补充约定：
1. HTML 文档文件名（去掉扩展名）就是上传到官网的模型全称
2. 只要检测到 `html/` 里有 HTML 文档，就按已有 HTML 文档整理文档
3. 不需要我再额外填写模型名、HTML 文档位置或真伪说明

如果需要，我再补充：
- 训练任务 ID：
- 地图/配置：
- 观察到的问题：

请你基于这些 HTML 文档和补充信息：
1. 更新当前算法文档
2. 更新 GLOBAL_DOCS/算法总表.md 中的训练状态
3. 给出下一轮迭代建议
4. 如有必要，同步 GLOBAL_DOCS/算法总表.md 和正式算法文档
```

---

## 6. 常用命令

### 6.1 Git 起手式

```bash
git pull
git status
git checkout -b feature/<topic>
```

示例：

```bash
git checkout -b feature/ppo-reward-shaping
```

### 6.2 最小验证

根据当前 README，默认在容器内做 smoke test：

```bash
docker exec -it kaiwu-dev-kaiwudrl-1 bash
python3 train_test.py
```

如果你的容器名不是这个，就替换成你自己的容器名。

### 6.3 查看改动和提交

```bash
git status
git diff
git add <files>
git commit -m "feat(ppo): tune reward shaping"
```

如果这是一次“完整算法实现”的正式提交，commit 信息里必须显式带上完整算法名，例如：

```bash
git commit -m "feat(ppo): finalize agent_ppo_20260409_1733"
```

### 6.4 推送分支

```bash
git push origin feature/<topic>
```

注意：push 和 merge 默认放在“人确认之后”。

---

## 7. Git 与文档协作规则

### 7.1 分支规则

- `main` 只接收已经完整实现、完成验证、文档同步完毕的版本
- 非微小改动不要直接在 `main` 上开发
- 默认在 `feature/<topic>` 分支上完成算法实现、优化和文档治理

推荐分支名示例：

- `feature/agent-ppo-docs`
- `feature/ppo-reward-shaping`
- `feature/repo-skills-bootstrap`

### 7.2 开发规范

要实现新算法或做有意义的算法改动，至少遵循这些规则：

1. 先分析当前 baseline
2. 再查询开发文档与接口约束
3. 一次只验证一个主方向或主假设
4. 代码修改后先做最小验证
5. 文档与代码同步更新
6. 正式算法实现默认始终在 `agent_ppo/` 中进行，`agent_diy/` 只作为模板参考

### 7.3 文档同步规则

默认需要同步检查的文件：

- `DEV_MEMORY/NOW.md`
- `GLOBAL_DOCS/算法总表.md`
- `GLOBAL_DOCS/算法文档/*`
- `GLOBAL_DOCS/算法调研.md`

怎么判断该写哪里：

- 改动只影响当前轮次、结论还不稳定，先写 `DEV_MEMORY/NOW.md`
- 结论已经稳定、对后续轮次有复用价值，再归档到 `GLOBAL_DOCS/算法总表.md` 与 `GLOBAL_DOCS/算法文档/*`
- `GLOBAL_DOCS/算法总表.md` 只记录已实现算法
- `GLOBAL_DOCS/算法调研.md` 只记录外部调研得到、但尚未实现的候选方向

### 7.4 commit 规范

**语言要求：所有 commit message 必须使用中文**。

小步 commit 适用场景：

- 单个问题修复
- 单个模块重构
- 阶段性文档同步
- 算法实现中的一个可独立验证步骤

小步 commit 格式：
```
<type>(<scope>): <简短描述>

- 改动目的：<为什么改>
- 改动文件：<改了哪些文件>
- 关键接口或配置变化：<如有>
- 最小验证状态：<通过 / 失败>
```

示例：
```bash
git commit -m “feat(preprocessor): 添加宝箱距离奖励

- 改动目的：优化奖励 shaping，鼓励智能体主动收集宝箱
- 改动文件：agent_ppo/feature/preprocessor.py
- 关键接口或配置变化：新增 TREASURE_DIST_COEF 参数
- 最小验证状态：通过”
```

完整算法 commit 适用场景：

- 一个算法已经完整实现
- 当前阶段算法文档、算法总表已同步
- 最小验证已通过

完整算法 commit 格式：
```
feat(<scope>): <算法完整名>

- 实现内容：<本轮完成的全部功能>
- 关键超参数设计：<核心参数取值>
- 当前可确认的训练得分或验证状态：<具体得分或验证状态>
- 对应算法文档路径：<文档位置>
- 对应的全局 / 当前轮次文档同步情况：<已同步 / 待同步>
```

示例：
```bash
git commit -m “feat(ppo): agent_ppo_20260410_hok_memory_map_v1

- 实现内容：接入 HOK 风格记忆地图、16 维动作空间、分层奖励设计
- 关键超参数设计：GAMMA=0.995, CLIP_PARAM=0.15, MAP_ENCODER_DIM=128
- 当前可确认的训练得分或验证状态：仅完成 smoke 验证，暂无正式训练得分
- 对应算法文档路径：GLOBAL_DOCS/算法文档/agent_ppo_20260410_hok_memory_map_v1/README.md
- 对应的全局 / 当前轮次文档同步情况：已同步”
```

关于训练得分：

- 有真实结果时，写真实结果
- 没有正式训练结果时，明确写”暂无正式训练得分”或”仅完成 smoke 验证”
- 不允许为了让提交更完整而编造结果

### 7.5 完整改动的收口标准

一个“完整改动”至少满足下面这些条件：

1. 代码已经完成本轮目标
2. 最小验证通过
3. `DEV_MEMORY/NOW.md` 已同步
4. 当前算法正式文档已更新
5. `GLOBAL_DOCS/算法总表.md` 已更新对应条目
6. 若状态已稳定，`GLOBAL_DOCS/算法总表.md` 与正式算法文档已同步

### 7.6 push / merge 规则

推荐流程：

1. 开发完成后先做本地验证
2. 再做 commit
3. 人确认后再 push
4. 算法完整实现并验证完毕之前，不允许合并到 `main`

额外注意：

- `push` 和 `merge` 属于收口动作，不应在需求尚未确认或结果尚未验证时提前执行
- 如果工作区里还有与当前任务无关的改动，先清理或拆分，再进行版本管理

### 7.7 禁止事项和推荐实践

默认禁止：

- 不读 README / workflow 就直接大改代码
- 不分析当前 baseline 就直接重构算法主链路
- 未验证就宣称算法“完整实现”
- 未同步文档就做“完整改动”提交
- 完整算法 commit 不写本轮算法完整名
- 在 `main` 上直接做非微小改动
- 编造训练得分、实验结论或归档内容

推荐实践：

- 优先小步提交，避免一次性混入多个方向
- 实现过程中持续维护 `DEV_MEMORY/NOW.md`
- 归档时只整理稳定算法信息，不再向 `GLOBAL_DOCS` 追加过程型记忆文件
- 正式算法文档统一使用 `GLOBAL_DOCS/算法文档/<算法完整名>/README.md` 作为入口，并在同目录 `html/` 存放训练/测试 HTML 文档；默认以 HTML 文档文件名（去掉扩展名）记录官网模型全称，AI 归档时只检测是否有 HTML 文档

---

## 8. 一轮完整算法迭代怎么做

下面是推荐的人机协作闭环。

### Stage 0：确定目标

人负责：

- 决定本轮主方向，例如“优化奖励 shaping”或“接入 16 维动作空间”
- 如果有多个候选方向，先决定要比较哪些方案

AI 负责：

- 复述目标
- 如果这是新方向，先比较候选方案与当前 baseline 是否值得做
- 映射到需要改动的代码文件
- 检查是否和当前 `DEV_MEMORY/NOW.md` 冲突

### Stage 1：初始化和看现状

人负责：

- 确认是否继续当前轮次，还是开启新方向

AI 负责：

- 读 README、KAIWU-WORKFLOW、当前指南
- 读 `GLOBAL_DOCS/算法总表.md`
- 读 `DEV_MEMORY/NOW.md`
- 输出“当前做到哪一步、下一步建议”

### Stage 2：查文档、分析基线与比较候选方案

人负责：

- 指出自己关注的问题，比如 reward、动作空间、环境协议
- 如果方向还没定，明确要让 AI 比较哪些候选算法或参考实现

AI 负责：

- 去 `开发文档/` 查官方说明
- 梳理当前基线入口、接口、超参数和已知限制
- 必要时把候选方案与当前 baseline 做同坐标系比较，再决定是否进入设计和实现

### Stage 3：代码实现

人负责：

- 确认这轮主要尝试点，不让 AI 同时改太多方向

AI 负责：

- 在 `agent_ppo/` 中实现改动
- 写必要但简短的注释
- 维护 `DEV_MEMORY/NOW.md`

### Stage 4：最小验证

人负责：

- 确认验证范围是否足够

AI 负责：

- 执行 `python3 train_test.py`
- 说明 smoke test 是否通过
- 如果失败，定位原因并修复

### Stage 5：真实训练、官网评估与 HTML 文档准备

人负责：

- 在平台或正式环境启动训练
- 观察监控、日志、得分
- 从官方训练监控导出训练全部曲线 HTML 文档，并放入对应算法文档目录的 `html/`
- 在官网上传模型；后续归档默认以 `html/` 中 HTML 文档文件名（去掉扩展名）作为上传到官网的模型全称
- 对开放 10 张地图执行 5 次官方评估
- 将测试 HTML 文档放入同一个 `html/` 目录
- 不再额外补填模型名、HTML 文档位置或说明
- 记录真实实验结果

AI 负责：

- 给出训练前检查清单
- 基于你放入 `html/` 的 HTML 文档整理文档素材
- 基于结果提出下一轮建议

### Stage 6：文档同步

人负责：

- 确认哪些结论是稳定的，哪些还只是尝试

AI 负责：

- 当前轮次信息写入 `DEV_MEMORY/NOW.md`
- 稳定结论整理进 `GLOBAL_DOCS/算法总表.md` 与 `GLOBAL_DOCS/算法文档/*`
- 在正式算法文档里补充训练/测试 HTML 文档索引
- 通过 `html/` 中 HTML 文档文件名提取官网模型全称
- 归档时只检测是否有 HTML 文档，不核验 HTML 文档真伪
- 必要时更新正式算法文档和算法总表

### Stage 7：Git 收口

人负责：

- 决定是否 commit、push、merge

AI 负责：

- 整理 diff 摘要
- 生成 commit message 建议
- 核对第 7.5 节的收口清单是否全部满足

---

## 9. 常见误区

### 误区 1：一上来就让 AI 改代码

正确做法：先让 AI 读文档、看 `DEV_MEMORY/NOW.md`、确认当前任务状态，再动手。

### 误区 2：把正式实现做进 `agent_diy/`

正确做法：正式算法迭代默认改 `agent_ppo/`，`agent_diy/` 只当模板。

### 误区 3：让 AI 一次改奖励、特征、网络、workflow 四个方向

正确做法：一轮只验证一个主假设，否则很难知道结果是哪个改动带来的。

### 误区 4：只改代码，不更新记忆和文档

正确做法：每轮都维护 `DEV_MEMORY/NOW.md`；结论稳定后再归档到 `GLOBAL_DOCS/算法总表.md` 与正式算法文档。

### 误区 5：没有正式训练结果，却写成“效果提升”

正确做法：没有正式训练结果就写清楚“仅 smoke test 通过，暂无正式训练得分”。

### 误区 6：代码写完就急着 push / merge

正确做法：先过最小验证，再同步文档，再检查收口清单，最后由人决定是否 push / merge。

---

## 10. 最短可执行版本

如果你只想记住最短流程，可以直接照这个顺序走：

1. `git pull`
2. `git status`
3. `git checkout -b feature/<topic>`
4. 让 AI 先读 `README.md`、`KAIWU-WORKFLOW.md`、`人类开发者AI协作指南.md`、`GLOBAL_DOCS/算法总表.md`、`DEV_MEMORY/NOW.md`
5. 让 AI 输出当前入口链路和改动文件定位
6. 让 AI 在 `agent_ppo/` 中实现单一方向改动
7. 跑 `python3 train_test.py`
8. 让 AI 更新 `DEV_MEMORY/NOW.md`
9. 人跑正式训练
10. 人先把训练全部曲线 HTML 文档和测试 HTML 文档放入 `GLOBAL_DOCS/算法文档/<算法完整名>/html/`，并保证 HTML 文档文件名（去掉扩展名）就是上传到官网的模型全称
11. 再让 AI 只要检测到目录里有 HTML 文档，就基于 HTML 文档更新 `GLOBAL_DOCS/算法总表.md` 和正式算法文档
12. 人确认后再 commit / push / merge

这就是这个仓库里“人做决策，AI 做实现与整理”的标准协作闭环。

---

## 11. Workflow Update (2026-04-10)

当前推荐的完整工作流是：

```text
算法调研 -> 候选比较 -> 算法落地 -> 算法实现 -> 算法测试 -> 算法训练 -> 训练结果整理 -> 信息归档 -> 结束
```

需要额外强调的规则：

1. 任何算法开发轮次的第一步，必须先执行 `/kaiwu-dev-init`。
2. 当方向来自 `GLOBAL_DOCS/算法调研.md`、`reference_algos/`、历史算法版本或用户新提案时，优先使用 `/kaiwu-algo-compare` 判断是否值得做，再进入 `/kaiwu-algo-design`。
3. `/kaiwu-algo-design` 不能只写抽象方案，必须结合开发文档补齐环境配置和超参数。
4. `/kaiwu-algo-implementation` 必须先理解源码和改动文件落点，再进行实现；实现的最后一步是把 `NOW.md` 整理成正式算法文档初稿。
5. `/kaiwu-memory-archive` 是开发流程的最后一步，负责正式归档、重置 `NOW.md`、完成最终 `commit`、`push`，并指导用户发起 merge。
6. 训练结果整理由人主导完成：人只需要把训练/测试 HTML 文档放入 `GLOBAL_DOCS/算法文档/<算法完整名>/html/`；HTML 文档文件名（去掉扩展名）视作上传到官网的模型全称；AI 只检测是否有 HTML 文档，不校验真伪，也不再要求人额外填写模型名或 HTML 文档说明。

推荐的 skill 顺序：

```text
/kaiwu-dev-init
/kaiwu-algo-compare
/kaiwu-algo-design
/kaiwu-algo-implementation
/kaiwu-memory-archive
```

如果要给 AI 一个更明确的实现提示，可以直接使用下面这个版本：

```text
/kaiwu-algo-implementation

目标：在 agent_ppo 中实现 xxx。

要求：
1. 先执行 /kaiwu-dev-init，并阅读 README、KAIWU-WORKFLOW、GLOBAL_DOCS/算法总表、DEV_MEMORY/NOW.md、开发文档 README
2. 改代码前先说清准备修改哪些文件，以及为什么改这些文件
3. 正式实现只改 agent_ppo/，不要把正式改动放到 agent_diy/
4. 改完后运行 python3 train_test.py 做 smoke test
5. 同步 DEV_MEMORY/NOW.md
6. 实现收尾时，把 NOW.md 整理成 `GLOBAL_DOCS/算法文档/<算法完整名>/README.md` 的初稿，并预留 `html/` 目录给人工放训练/测试 HTML 文档；归档时默认从 HTML 文档文件名读取官网模型全称
7. 暂时不要 push
```

归档阶段可以直接使用下面这个版本：

```text
/kaiwu-memory-archive

请把本轮稳定结论归档到 GLOBAL_DOCS，并同步算法总表和正式算法文档；归档完成后重置 NOW.md，完成最终 commit、push，并告诉我接下来应该怎样发起 merge。
```

---

## 12. 当前训练指标、超参数与环境参数速查

### 12.1 先看哪几个文件

| 内容 | 文件 |
| --- | --- |
| 当前 monitor 面板配置 | `agent_ppo/conf/monitor_builder.py` |
| Train / Val 指标上报 | `agent_ppo/workflow/train_workflow.py` |
| PPO loss 指标上报 | `agent_ppo/algorithm/algorithm.py` |
| 算法、奖励、结构超参数 | `agent_ppo/conf/conf.py` |
| 训练环境参数 | `agent_ppo/conf/train_env_conf.toml` |
| 验证环境参数 | `agent_ppo/conf/eval_env_conf.toml` |
| 系统训练参数 | `conf/configure_app.toml` |

### 12.2 当前训练指标说明

当前 monitor 以代码实现为准，分成 `Train`、`环境指标`、`训练损失`、`Val` 四组。

需要先记住两件事：
- `Train` 是训练单局指标，单局结束就上报。
- `Val` 是验证聚合指标，不是单局值；当前实现默认每训练 `50` 局切一次 eval，eval 跑 `10` 局后求均值再上报。

#### Train 组

| 指标 | 面板名 | 含义 |
| --- | --- | --- |
| `train_reward` | `Reward` | 单局总训练奖励，等于 pre/post shaped reward 与 pre/post terminal bonus 的总和。 |
| `train_total_score` | `TotalScore` | 单局结束时环境侧 `total_score`。 |
| `train_step_score` | `StepScore` | 单局结束时环境侧步数得分。 |
| `train_treasure_score` | `TreasureScore` | 单局结束时环境侧宝箱得分。 |
| `train_treasures_collected` | `Treasures` | 单局最终收集到的宝箱数量。 |
| `train_episode_steps` | `Steps` | 单局完成步数。 |
| `train_speedup_reached` | `SpeedupReached` | 本局是否至少拿到过一次 buff，取值 `0/1`。 |
| `train_pre_speedup_steps` | `Pre_Steps` | 首次拿到 buff 之前累计步数。 |
| `train_post_speedup_steps` | `Post_Steps` | 首次拿到 buff 之后累计步数。 |
| `train_pre_speedup_reward` | `Pre_TotalR` | buff 前总 reward，等于 `pre_speedup_shaped_reward + pre_speedup_terminal_bonus`。 |
| `train_post_speedup_reward` | `Post_TotalR` | buff 后总 reward，等于 `post_speedup_shaped_reward + post_speedup_terminal_bonus`。 |
| `train_pre_speedup_shaped_reward` | `Pre_ShapedR` | buff 前 shaped reward，不含终局 bonus / penalty。 |
| `train_post_speedup_shaped_reward` | `Post_ShapedR` | buff 后 shaped reward，不含终局 bonus / penalty。 |
| `train_pre_speedup_step_score_gain` | `Pre_StepGain` | buff 前 `step_score` 增量。 |
| `train_post_speedup_step_score_gain` | `Post_StepGain` | buff 后 `step_score` 增量。 |
| `train_pre_speedup_treasure_gain` | `Pre_TreaGain` | buff 前 `treasure_score` 增量。 |
| `train_post_speedup_treasure_gain` | `Post_TreaGain` | buff 后 `treasure_score` 增量。 |
| `train_pre_speedup_total_score_gain` | `Pre_TotalGain` | buff 前 `total_score` 增量。 |

当前实现说明：
- Train 组当前没有 `train_post_speedup_total_score_gain`，这是当前代码的真实状态。
- Train 组数据来自 `EpisodeMetrics.as_train_monitor_dict()`。

#### 环境指标组

| 指标 | 面板名 | 含义 |
| --- | --- | --- |
| `total_score` | `得分` | 环境侧总得分。 |
| `treasure_score` | `得分` | 环境侧宝箱得分。 |
| `step_score` | `得分` | 环境侧步数得分。 |
| `total_map` | `地图` | 环境上报的地图配置摘要值，用来观察当前地图池设置。 |
| `map_random` | `地图` | 是否随机抽图，通常 `0/1`。 |
| `max_step` | `步数` | 当前环境最大步数配置；面板展示名是 `max_steps`，但表达式实际读取 `max_step`。 |
| `finished_steps` | `步数` | 当前局实际完成步数。 |
| `total_treasure` | `宝箱` | 当前环境宝箱总数配置。 |
| `treasures_collected` | `宝箱` | 当前局已收集宝箱数。 |
| `flash_count` | `闪现` | 当前局已使用闪现次数。 |
| `flash_cooldown` | `闪现` | 闪现冷却配置步数。 |
| `total_buff` | `加速增益` | 当前环境 buff 总数配置。 |
| `collected_buff` | `加速增益` | 当前局已拾取 buff 数。 |
| `buff_refresh_time` | `加速增益` | buff 刷新/重生相关时间指标。 |
| `monster_speed` | `怪物移动速度` | 当前怪物移动速度。 |
| `monster_interval` | `怪物出现间隔` | 第二只怪物出现的配置步数。 |

#### 训练损失组

这一组不是按单局上报，而是 `Algorithm.learn()` 每约 `60` 秒节流上报一次。

| 指标 | 面板名 | 含义 |
| --- | --- | --- |
| `reward` | `CumReward` | Learner 当前 batch 的样本 reward 均值，不是单局 score。 |
| `total_loss` | `TotalLoss` | PPO 总损失：`vf_coef * value_loss + policy_loss - beta * entropy_loss`。 |
| `value_loss` | `ValueLoss` | value head 拟合 `reward_sum` 的损失。 |
| `policy_loss` | `PolicyLoss` | PPO clipped surrogate policy loss。 |
| `entropy_loss` | `EntropyLoss` | 策略熵项，值越大说明分布越分散。 |
| `grad_clip_norm` | `GradClipNorm` | 梯度总范数统计，由 `clip_grad_norm_` 返回。 |
| `clip_frac` | `ClipFrac` | batch 中被 PPO clip 的样本比例。 |
| `explained_var` | `ExplainedVar` | value 对 return 的解释度，越接近 `1` 越好。 |
| `adv_mean` | `AdvMean` | advantage 标准化之前的 batch 均值。 |
| `ret_mean` | `RetMean` | `reward_sum` 的 batch 均值，可理解为当前 return target 的平均水平。 |

补充说明：
- `approx_kl` 当前只写日志，没有做成 monitor 面板。
- 当 `approx_kl > TARGET_KL` 时，当前 update 会被直接跳过。

#### Val 组

Val 组来自 `EpisodeRunner._build_val_monitor_data()`，是 eval 多局平均值。

| 指标 | 面板名 | 含义 |
| --- | --- | --- |
| `val_reward` | `Reward` | 验证阶段总 reward 均值。 |
| `val_total_score` | `TotalScore` | 验证阶段 `total_score` 均值。 |
| `val_step_score` | `StepScore` | 验证阶段步数得分均值。 |
| `val_treasure_score` | `TreasureScore` | 验证阶段宝箱得分均值。 |
| `val_treasures_collected` | `Treasures` | 验证阶段收集宝箱数均值。 |
| `val_episode_steps` | `Steps` | 验证阶段完成步数均值。 |
| `val_speedup_reached` | `SpeedupReached` | 验证阶段拿到过 buff 的比例。 |
| `val_pre_speedup_steps` | `Pre_Steps` | buff 前步数均值。 |
| `val_post_speedup_steps` | `Post_Steps` | buff 后步数均值。 |
| `val_pre_speedup_reward` | `Pre_TotalR` | buff 前总 reward 均值。 |
| `val_post_speedup_reward` | `Post_TotalR` | buff 后总 reward 均值。 |
| `val_pre_speedup_shaped_reward` | `Pre_ShapedR` | buff 前 shaped reward 均值。 |
| `val_post_speedup_shaped_reward` | `Post_ShapedR` | buff 后 shaped reward 均值。 |
| `val_pre_speedup_step_score_gain` | `Pre_StepGain` | buff 前 `step_score` 增量均值。 |
| `val_post_speedup_step_score_gain` | `Post_StepGain` | buff 后 `step_score` 增量均值。 |
| `val_pre_speedup_treasure_gain` | `Pre_TreaGain` | buff 前 `treasure_score` 增量均值。 |
| `val_post_speedup_treasure_gain` | `Post_TreaGain` | buff 后 `treasure_score` 增量均值。 |
| `val_pre_speedup_total_score_gain` | `Pre_TotalGain` | buff 前 `total_score` 增量均值。 |
| `val_post_speedup_total_score_gain` | `Post_TotalGain` | buff 后 `total_score` 增量均值。 |
| `val_pre_speedup_terminal_bonus` | `Pre_Terminal` | buff 前终局 bonus / penalty 均值。 |
| `val_post_speedup_terminal_bonus` | `Post_Terminal` | buff 后终局 bonus / penalty 均值。 |
| `val_post_speedup_terminated` | `Post_Terminated` | 拿到 buff 后仍然终止的比例。 |
| `val_terminated_rate` | `TerminatedRate` | 被怪物抓到导致终止的比例。 |
| `val_completed_rate` | `CompletedRate` | 存活到最大步数的比例。 |
| `val_abnormal_truncated_rate` | `AbnormalTrunc` | 非终止但未达到 `max_step` 就被截断的比例。 |
| `val_danger_level` | `Final_Danger` | 终局危险度均值，按终局时离最近怪物的距离归一化到 `[0,1]`。 |
| `val_nearest_treasure_dist` | `Final_TreaDist` | 终局时最近宝箱距离均值，没有可用宝箱时记为 `-1`。 |

如果你在平台里看不到 Val 曲线，优先检查：
- 训练是否已经累计到 `50` 个 train episode。
- eval 是否已经完整跑完 `10` 局。
- `monitor.put_data(...)` 是否正常执行。

### 12.3 算法与奖励超参数

当前算法超参数定义在 `agent_ppo/conf/conf.py`。

#### PPO / 优化相关

| 参数 | 当前值 | 作用 | 调整建议 |
| --- | --- | --- | --- |
| `GAMMA` | `0.995` | 折扣因子，影响 return 与 GAE 的时间跨度。 | 想更看重长期存活可调大；训练抖动大、信用分配过长可略降。 |
| `LAMDA` | `0.95` | GAE 系数，控制 bias / variance 权衡。 | 高一些更平滑但方差更大；低一些更稳定但偏差更大。 |
| `INIT_LEARNING_RATE_START` | `0.0002` | Adam 学习率。 | loss 波动大或策略崩溃可先降；收敛太慢可谨慎升。 |
| `BETA_START` | `0.003` | 初始熵系数。 | 开局探索不足可升；动作太随机可降。 |
| `BETA_END` | `0.0005` | 熵系数衰减终点。 | 后期想保留更多探索可升；想更快收敛可降。 |
| `BETA_DECAY_STEPS` | `4000` | 熵系数从 start 衰减到 end 的步数。 | 太快会过早贪心，太慢会长期随机。 |
| `CLIP_PARAM` | `0.15` | PPO ratio clip 范围。 | 大一些更新更猛但更不稳；小一些更稳但学习慢。 |
| `VF_COEF` | `1.0` | value loss 权重。 | value 学不动可升；value 压制 policy 可降。 |
| `GRAD_CLIP_RANGE` | `0.5` | 梯度裁剪阈值。 | 梯度爆炸可降；更新过弱可略升。 |
| `USE_ADVANTAGE_NORM` | `True` | 是否对 advantage 做标准化。 | 一般保持开启，更稳定。 |
| `ADVANTAGE_NORM_EPS` | `1e-8` | advantage 标准化数值稳定项。 | 一般不需要改。 |
| `TARGET_KL` | `0.015` | 超过该 KL 时直接跳过本次 update。 | 经常跳过说明步子过大，可降学习率或减小 clip；完全不触发可视情况略升。 |

#### Reward shaping 相关

| 参数 | 当前值 | 作用 | 调整建议 |
| --- | --- | --- | --- |
| `SURVIVE_REWARD` | `0.005` | 每步基础生存奖励。 | 太小会不重视存活，太大可能只学会苟活。 |
| `DIST_SHAPING_COEF` | `0.05` | 远离最近怪物的 shaping 系数。 | 提高会更保守躲怪，过大可能不愿意追宝箱。 |
| `TREASURE_REWARD` | `1.0` | 每拿到一个宝箱的即时奖励。 | 提高会更激进拿宝箱。 |
| `BUFF_REWARD` | `0.3` | 每拿到一个 buff 的即时奖励。 | 想强化拿 buff 行为可升。 |
| `TREASURE_DIST_COEF` | `0.08` | 朝当前目标宝箱靠近时的 shaping 系数。 | 提高会更主动走向宝箱。 |
| `EXIT_DIST_COEF` | `0.04` | 当前没有宝箱目标时，朝 buff 目标靠近的引导系数。 | 想更积极拿 buff 可升。 |
| `FLASH_ESCAPE_REWARD_COEF` | `0.05` | 在危险区使用闪现并拉开距离时的奖励系数。 | 闪现利用率低可升；滥用闪现可降。 |
| `HIT_WALL_PENALTY` | `0.05` | 撞墙/无效移动惩罚。 | 卡墙严重可升。 |
| `REVISIT_PENALTY_COEF` | `0.02` | 重访区域惩罚系数。 | 原地绕圈严重可升；探索过散可降。 |
| `REVISIT_WINDOW_SIZE` | `3` | 计算重访强度时使用的局部窗口大小。 | 想让“重复走位”惩罚覆盖更广可升。 |
| `TERMINATED_PENALTY` | `-12.0` | 被怪物抓到时的终局惩罚。 | 想更强压制送死行为可调得更负。 |
| `TRUNCATED_BONUS` | `8.0` | 存活到 `max_step` 的终局奖励。 | 想更强调“活满全程”可升。 |

#### 轻量探索奖励相关

| 参数 | 当前值 | 作用 | 调整建议 |
| --- | --- | --- | --- |
| `ENABLE_EXPLORE_BONUS` | `True` | 是否启用基于网格新颖度的探索奖励。 | 探索逻辑明显干扰主目标时可先关掉。 |
| `EXPLORE_BONUS_SCALE` | `0.01` | 探索 bonus 的整体缩放。 | 太小几乎没效果，太大可能压过主奖励。 |
| `EXPLORE_BONUS_GRID_SIZE` | `16` | 把地图划分成多少网格来统计新颖度。 | 更大更细粒度，更小更粗粒度。 |
| `EXPLORE_BONUS_MIN_RATIO` | `0.25` | 新颖度低于该阈值时不给 bonus。 | 想更严格只奖励新区域可升。 |

#### 结构超参数

| 参数 | 当前值 | 作用 | 调整建议 |
| --- | --- | --- | --- |
| `LOCAL_MAP_SIZE` | `11` | 局部语义地图边长。 | 想扩大局部观察范围可升，但会直接增大输入维度。 |
| `LOCAL_MAP_CHANNEL` | `4` | 局部语义地图通道数。 | 只有在你真的改了语义地图编码时才需要改。 |
| `HERO_ENCODER_DIM` | `32` | hero 特征编码维度。 | hero 信息表达不足可升。 |
| `MONSTER_ENCODER_DIM` | `64` | 两只怪物联合编码维度。 | 需要更强避怪建模可升。 |
| `MAP_ENCODER_DIM` | `128` | 局部地图 CNN 编码输出维度。 | 地图策略不足可升，但成本会上去。 |
| `CONTROL_ENCODER_DIM` | `32` | legal action + progress 编码维度。 | 控制相关信息表达不足可升。 |
| `FUSION_HIDDEN_DIM` | `128` | 最终融合 backbone 隐层宽度。 | 模型容量不足可升，过拟合或太慢可降。 |

结构改动时一定注意：
- `LOCAL_MAP_SIZE * LOCAL_MAP_SIZE * LOCAL_MAP_CHANNEL` 必须和 `FEATURES` 里的地图段维度保持一致；当前 `11 * 11 * 4 = 484`。
- 如果你改了局部地图尺寸或通道，必须同步检查 `FEATURES`、preprocessor 输出和 `model.py` 中的 `map_shape`。

### 12.4 系统训练参数

系统训练参数在 `conf/configure_app.toml`，它们不是 PPO 公式的一部分，但会直接影响训练节奏。

| 参数 | 当前值 | 作用 | 设置建议 |
| --- | --- | --- | --- |
| `replay_buffer_capacity` | `10000` | 样本池容量。 | 太小样本太新、相关性高；太大则刷新慢。 |
| `preload_ratio` | `1.0` | 样本池装到多少比例后开始训练。 | 想更早启动训练可降，但初期会更噪。 |
| `reverb_remover` | `reverb.selectors.Fifo` | 样本池淘汰策略。 | 一般保留 `Fifo`，让老样本自然淘汰。 |
| `reverb_sampler` | `reverb.selectors.Uniform` | Learner 采样策略。 | `Uniform` 通常更稳；想按时间顺序采样才考虑 `Fifo`。 |
| `reverb_rate_limiter` | `MinSize` | 插入/采样限流策略。 | 采样速度明显快于产样时才考虑 `SampleToInsertRatio`。 |
| `reverb_samples_per_insert` | `5` | 每条样本最多复用次数，仅 `SampleToInsertRatio` 生效。 | 想严格控制复用率时再调。 |
| `reverb_error_buffer` | `5` | 复用率约束缓冲区，仅 `SampleToInsertRatio` 生效。 | 一般配合上一个参数一起调。 |
| `train_batch_size` | `2048` | Learner 单次训练 batch 大小。 | 显存/吞吐允许时可升；不稳定或资源不够可降。 |
| `dump_model_freq` | `100` | 模型导出频率。 | 太频繁会增加 I/O，太低则中间检查点少。 |
| `model_file_sync_per_minutes` | `1` | Actor 拉取最新模型的分钟级频率。 | 太慢会用旧策略，太快会增加同步开销。 |
| `modelpool_max_save_model_count` | `1` | 模型池保留的模型份数。 | 想保留更多中间版本可升。 |
| `preload_model` | `false` | 是否从已有 checkpoint 热启动。 | 做迁移/续训时开启。 |
| `preload_model_dir` | `"{agent_name}/ckpt"` | 预加载模型目录。 | 通常不改目录结构就保持默认。 |
| `preload_model_id` | `1000` | 预加载 checkpoint 的 step id。 | 热启动时改成目标 checkpoint 对应 step。 |

### 12.5 环境参数

环境参数分别在 `agent_ppo/conf/train_env_conf.toml` 与 `agent_ppo/conf/eval_env_conf.toml`。

#### 当前训练/验证配置

| 参数 | 训练值 | 验证值 | 含义与设置建议 |
| --- | --- | --- | --- |
| `map` | `[1,2,3,4,5,6,7,8]` | `[9,10]` | 训练图和验证图要尽量分离，验证图不要与训练图重叠。 |
| `map_random` | `false` | `true` | 是否随机抽图。训练想更可控可关，想增强随机性可开；验证通常建议开。 |
| `treasure_count` | `10` | `10` | 宝箱数量。高一些奖励更密，低一些探索更难。 |
| `buff_count` | `2` | `2` | buff 数量。高一些更容易拿到加速。 |
| `buff_cooldown` | `200` | `200` | buff 被拾取后的刷新步数。越小越容易重复拿 buff。 |
| `talent_cooldown` | `100` | `100` | 闪现冷却步数。越小环境越宽松。 |
| `monster_interval` | `300` | `300` | 第二只怪物出现步数。越大前期越简单。 |
| `monster_speedup` | `500` | `500` | 怪物加速生效步数。越大中后期越简单。 |
| `max_step` | `1000` | `1000` | 单局最大步数。越大 horizon 越长，训练也更慢。 |

环境参数调节经验：
- 先固定训练图和验证图，不要一边改算法一边改地图划分。
- 如果你在做 reward / feature / network 迭代，优先保持 `max_step`、`monster_interval`、`monster_speedup` 不变。
- 想做 curriculum，可以先改训练环境，不要先改验证环境。
- 评估配置最好比训练配置更稳定，避免把“环境波动”误判成“算法波动”。

### 12.6 HTML 文档驱动的训练/测试归档规范

正式训练和测试结束后，人不需要再额外填写模型名或 HTML 文档说明，只需要把 HTML 文档放到对应算法文档目录的 `html/`：

| 项目 | 规范 |
| --- | --- |
| 训练/测试 HTML 文档 | 统一放在 `GLOBAL_DOCS/算法文档/<算法完整名>/html/`。训练全部曲线 HTML 文档和测试 HTML 文档都放这里。 |
| HTML 文档文件名 | HTML 文档文件名（去掉扩展名）视作上传到官网的模型全称。 |
| AI 归档检查 | AI 只检测 `html/` 中是否存在 HTML 文档，不核验 HTML 文档真伪，也不要求人再额外补填模型名、HTML 文档位置或说明。 |

推荐直接对 AI 说：
- `我已经把训练/测试 HTML 文档放到 GLOBAL_DOCS/算法文档/<算法完整名>/html/ 了`
- `HTML 文档文件名（去掉扩展名）就是上传到官网的模型全称`
- `你只要检测到目录里有 HTML 文档就继续归档`

---
