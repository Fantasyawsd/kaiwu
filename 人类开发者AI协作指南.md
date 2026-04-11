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
- 决定是否继续当前方向，还是切换方向
- 启动平台真实训练，观察监控和日志
- 从官方训练监控截图并放入对应算法文档目录的 `screenshots/`
- 在官网上传模型，命名严格遵循 `算法完整名 + 训练步数`，建议写成 `<算法完整名>_<训练步数>`
- 对开放 10 张地图执行 5 次官方评估
- 记录 5 次评估里的 10 张地图得分，并把最终结果截图放入同一个 `screenshots/` 目录
- 记录正式实验结果
- 最终决定是否 commit、push、merge

### 4.2 AI 主要负责

- 阅读仓库文档和官方开发文档
- 分析当前基线实现和代码入口
- 完成代码修改
- 跑最小验证，比如 `python3 train_test.py`
- 把当前状态同步到 `DEV_MEMORY/NOW.md`
- 基于人提供的真实训练结果、10 张地图得分和截图，在结论稳定后整理到 `GLOBAL_DOCS/算法总表.md` 与 `GLOBAL_DOCS/算法文档/*`
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
/kaiwu-algo-implementation
/kaiwu-version-control
/kaiwu-memory-archive
/kaiwu-version-control
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
/kaiwu-algo-implementation

目标：在 agent_ppo 中优化 xxx。

要求：
1. 先读 README、KAIWU-WORKFLOW、GLOBAL_DOCS/算法总表、DEV_MEMORY/NOW.md、开发文档/README
2. 只改 agent_ppo/ 里的正式实现，不要把正式改动做在 agent_diy/
3. 改完后运行 python3 train_test.py 做 smoke test
4. 同步 DEV_MEMORY/NOW.md
5. 暂时不要 push
```

#### 4. 收口和归档

```text
/kaiwu-version-control

请检查本轮改动范围，给出建议 commit message，暂时不要 push
```

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
我已经跑完一轮正式训练，下面是结果和日志摘要：

1. 训练任务 ID：
2. 地图/配置：
3. 关键监控指标：
4. 最终表现：
5. 官网评估模型名（算法完整名 + 训练步数）：
6. 5 次官方评估的 10 张地图得分：
7. 训练监控截图 / 最终评估结果截图位置：
8. 观察到的问题：

请你基于这些结果：
1. 更新当前算法文档
2. 更新 GLOBAL_DOCS/算法总表.md 中的训练状态
3. 在正式算法文档里补充官方评估的 10 张地图得分与截图索引
4. 给出下一轮迭代建议
5. 如有必要，同步 GLOBAL_DOCS/算法总表.md 和正式算法文档
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
- 正式算法文档统一使用 `GLOBAL_DOCS/算法文档/<算法完整名>/README.md` 作为入口，并在同目录 `screenshots/` 存放官方训练监控截图与官方评估结果截图

---

## 8. 一轮完整算法迭代怎么做

下面是推荐的人机协作闭环。

### Stage 0：确定目标

人负责：

- 决定本轮主方向，例如“优化奖励 shaping”或“接入 16 维动作空间”

AI 负责：

- 复述目标
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

### Stage 2：查文档和分析基线

人负责：

- 指出自己关注的问题，比如 reward、动作空间、环境协议

AI 负责：

- 去 `开发文档/` 查官方说明
- 梳理当前基线入口、接口、超参数和已知限制

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

### Stage 5：真实训练、官网评估与截图准备

人负责：

- 在平台或正式环境启动训练
- 观察监控、日志、得分
- 从官方训练监控截图并放入对应算法文档目录的 `screenshots/`
- 在官网上传模型，名称严格遵循 `算法完整名 + 训练步数`，建议写成 `<算法完整名>_<训练步数>`
- 对开放 10 张地图执行 5 次官方评估
- 记录 5 次评估中的 10 张地图得分
- 将最终评估结果截图放入同一个 `screenshots/` 目录
- 记录真实实验结果

AI 负责：

- 给出训练前检查清单
- 基于你提供的真实训练结果、10 张地图得分和截图整理文档素材
- 基于结果提出下一轮建议

### Stage 6：文档同步

人负责：

- 确认哪些结论是稳定的，哪些还只是尝试

AI 负责：

- 当前轮次信息写入 `DEV_MEMORY/NOW.md`
- 稳定结论整理进 `GLOBAL_DOCS/算法总表.md` 与 `GLOBAL_DOCS/算法文档/*`
- 在正式算法文档里补充官方训练监控截图索引
- 在正式算法文档里补充官网评估的模型命名、5 次评估记录、10 张地图得分和最终结果截图索引
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
10. 人先从官方训练监控截图，并按 `算法完整名 + 训练步数` 上传模型做 5 次官方评估，把最终结果截图也放入 `GLOBAL_DOCS/算法文档/<算法完整名>/screenshots/`
11. 再让 AI 基于真实结果、10 张地图得分和截图更新 `GLOBAL_DOCS/算法总表.md` 和正式算法文档
12. 人确认后再 commit / push / merge

这就是这个仓库里“人做决策，AI 做实现与整理”的标准协作闭环。

---

## 11. Workflow Update (2026-04-10)

当前推荐的完整工作流是：

```text
算法调研 -> 算法落地 -> 算法实现 -> 算法测试 -> 算法训练 -> 训练结果整理 -> 信息归档 -> 结束
```

需要额外强调的规则：

1. 任何算法开发轮次的第一步，必须先执行 `/kaiwu-dev-init`。
2. `/kaiwu-algo-design` 不能只写抽象方案，必须结合开发文档补齐环境配置和超参数。
3. `/kaiwu-algo-implementation` 必须先理解源码和改动文件落点，再进行实现；实现的最后一步是把 `NOW.md` 整理成正式算法文档初稿。
4. `/kaiwu-memory-archive` 是开发流程的最后一步，负责正式归档、重置 `NOW.md`、完成最终 `commit`、`push`，并指导用户发起 merge。
5. 训练结果整理由人主导完成：官方训练监控截图和最终评估结果截图都由人手动放入 `GLOBAL_DOCS/算法文档/<算法完整名>/screenshots/`；官网上传模型时名称严格遵循 `算法完整名 + 训练步数`，并对开放 10 图完成 5 次官方评估；AI 不再依赖仓库内训练分析 skill / 脚本。

推荐的 skill 顺序：

```text
/kaiwu-dev-init
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
6. 实现收尾时，把 NOW.md 整理成 `GLOBAL_DOCS/算法文档/<算法完整名>/README.md` 的初稿，并预留 `screenshots/` 目录给人工放训练监控截图和官方评估结果截图
7. 暂时不要 push
```

归档阶段可以直接使用下面这个版本：

```text
/kaiwu-memory-archive

请把本轮稳定结论归档到 GLOBAL_DOCS，并同步算法总表和正式算法文档；归档完成后重置 NOW.md，完成最终 commit、push，并告诉我接下来应该怎样发起 merge。
```

---
