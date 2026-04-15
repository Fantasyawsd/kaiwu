本文定义 Gorge Chase KaiWuDRL 仓库的标准工作流、Skills 使用顺序、文档维护规则和 Git 协作要求。

---

## 1. 总体工作流

完整工作流固定为：

```text
算法调研 -> 候选比较 -> 算法落地 -> 算法实现 -> 算法测试 -> 算法训练 -> 训练结果整理 -> 信息归档 -> 结束
````

其中：

- **算法调研**：形成人类主导的候选方向，主要沉淀到 `GLOBAL_DOCS/算法调研.md`

- **候选比较**：把调研方向、`reference_algos/`、历史算法版本或用户新提案与当前 baseline 放到同一坐标系下比较，判断值不值得进入设计阶段
    
- **算法落地**：把方向转成可以编码的实现方案，核心产物是 `DEV_MEMORY/NOW.md`
    
- **算法实现**：改代码、做最小验证、持续更新 `NOW.md`
    
- **算法测试**：以 `python3 train_test.py` 为主的 smoke test 与最小链路验证
    
- **算法训练**：由人发起平台真实训练
    
- **训练结果整理**：由人查看官方训练监控、按 `算法完整名 + 训练步数` 上传模型做 5 次官网评估、将 HTML 文档归档到 `html/`，并整理真实训练结论与 10 张地图得分
    
- **信息归档**：把稳定结论写入正式算法文档和算法总表，并完成 Git 收口
    

---

## 2. 强制前置动作与入口

进入任何非微小算法开发前，必须先完成下面这组 Git 前置动作：

```bash

git pull

git status

git checkout -b feature/<topic>

```

如果目标分支已经存在，则切换到已有的 `feature/<topic>`。

规则：

- 只要准备进入算法设计、算法实现、算法测试、训练结果整理或信息归档，就不能继续停留在 `main`

- 允许在 `main` 上做只读分析或极小的纯文本修订，但一旦进入实质算法开发，必须先切到 `feature/*`

- 未位于合适的 `feature/*` 分支时，不进入 `/kaiwu-algo-design` 或 `/kaiwu-algo-implementation`

---

## 3. 文档维护规范

### 3.1 DEV_MEMORY（开发状态记忆）

**文件**：`DEV_MEMORY/NOW.md`

**目的**：保存当前开发状态，使 AI 或人在断线重连、会话中断、任务转交后能仅凭仓库文件快速恢复并继续。

**作用**：

- 保存当前轮次的设计、实现进度和下一步计划
    
- 让 AI 或人重新接手时能快速恢复上下文
    
- 在算法实现收尾阶段，支持整理为正式算法文档初稿
    

**必须包含的三部分**：

1. **当前要实现算法的具体内容**：本轮目标、假设、预期改动
    
2. **当前的实现进度**：已完成什么、遇到什么问题、解决方案
    
3. **下一步计划**：接下来要做什么、优先级、依赖条件
    

**维护时机**：

- 确定本轮目标时
    
- 改动代码后
    
- 跑完验证后
    
- 遇到问题或解决问题时
    
- 任何可能导致会话中断的节点
    

---

### 3.2 GLOBAL_DOCS（全局稳定知识库）

**目的**：长期沉淀已验证的算法知识，供后续轮次查阅参考。

**核心文件**：

|文件/目录|作用|维护者|
|---|---|---|
|`GLOBAL_DOCS/算法总表.md`|算法清单总入口：算法名、完整名、训练得分、状态、文档路径|AI|
|`GLOBAL_DOCS/算法调研.md`|候选方向记录：尚未实现的外部调研、论文方向、优化思路|人|
|`GLOBAL_DOCS/算法文档/`|正式算法文档目录。每个算法使用 `算法完整名/README.md` 作为主文档，并在同目录 `html/` 存放训练监控 HTML 文档与官方评估结果 HTML 文档|AI|

**维护时机**：

- 算法从“未实现”变为“已实现”
    
- 训练得分得到真实平台结果确认
    
- 算法实现细节已稳定、可跨轮次复用
    

**维护方法**：

```text
/kaiwu-memory-archive
```

**原则**：

- 不把 `DEV_MEMORY/NOW.md` 原样复制到正式文档
    
- 只归档已验证的稳定信息
    
- 训练结果必须来自真实平台
- `GLOBAL_DOCS/算法总表.md` 中必须始终保持且仅保持一个“当前基线”；若本轮归档的是当前稳定主线版本，归档时必须把该版本提升为“当前基线”，并将旧基线降级为历史基线或已归档版本
    

---

## 4. Skills 体系

### 4.1 Skills 列表

|Skill|核心功能|使用阶段|
|---|---|---|
|`/kaiwu-dev-init`|开发轮次初始化，强制入口|所有轮次的第一步|
|`/kaiwu-doc-query`|查询开发文档与接口规则|任意阶段按需调用|
|`/kaiwu-current-algo-analysis`|分析当前算法实现与入口链|实现前、排障前、仅查看现状时|
|`/kaiwu-algo-compare`|比较候选算法与当前 baseline，评估收益、风险和落地成本|新方向筛选、调研转设计前|
|`/kaiwu-algo-design`|把调研方向落成可实现方案，补齐环境配置和超参数，写入 `NOW.md`|算法落地|
|`/kaiwu-algo-implementation`|基于源码理解完成实现、测试、`NOW.md` 更新，并产出算法文档初稿|算法实现 + 算法测试|
|`/kaiwu-memory-archive`|最终归档、重置 `NOW.md`、commit、push、merge 指引|信息归档|

---

### 4.2 标准调用流程

#### 新方向完整流程

```text
/kaiwu-dev-init
-> /kaiwu-algo-compare
-> /kaiwu-algo-design
-> /kaiwu-algo-implementation
-> 人执行真实训练
-> 人工整理训练监控、官网评估与 HTML 文档归档
-> /kaiwu-memory-archive
```

#### 继续已有方向

```text
/kaiwu-dev-init
-> /kaiwu-algo-implementation
```

#### 仅查看现状

```text
/kaiwu-dev-init
-> /kaiwu-current-algo-analysis
```

#### 候选方向比较

```text
/kaiwu-dev-init
-> /kaiwu-algo-compare
```

---

### 4.3 Skill 调用规则

- 任何非微小改动前，必须先调 `/kaiwu-dev-init`
    
- 当需要在 `GLOBAL_DOCS/算法调研.md`、`reference_algos/`、历史算法文档或用户口述方案之间判断“值不值得做”时，先用 `/kaiwu-algo-compare`
    
- 新方向不得跳过 `/kaiwu-algo-design`
    
- `/kaiwu-algo-compare` 只做比较与判断，不改代码，不写 `NOW.md`
    
- `/kaiwu-algo-design` 只产出方案并写入 `NOW.md`，不直接改代码
    
- `/kaiwu-algo-design` 必须基于开发文档补齐环境配置和超参数
    
- `/kaiwu-algo-implementation` 必须先理解源码落点，再改文件
    
- `/kaiwu-algo-implementation` 应采用小步迭代：实现 → 烟测 → 更新 `NOW.md` → 小步 commit
    
- `/kaiwu-algo-implementation` 的最后一步是创建算法文档目录结构（含 `README.md` 初稿 + `html/` 空目录，用于存放 HTML 文档）
    
- 训练完成后必须单独做人主导的训练结果整理与官网评估，不直接把训练结果混入实现过程
    
- `/kaiwu-memory-archive` 是最终收口步骤，负责归档、重置 `NOW.md`、commit、push 和 merge 指引
- `/kaiwu-memory-archive` 在更新 `GLOBAL_DOCS/算法总表.md` 时，必须显式判断“当前基线”是否需要切换；若当前源码主线已经演进到新版本，不得继续保留旧版本为“当前基线”
    
- 不自动 push，所有 push 需用户确认后执行
    

---

## 5. Git 协作规范

### 5.1 分支策略

|分支|用途|
|---|---|
|`main`|只接收完成验证并归档完毕的版本|
|`feature/<topic>`|算法实现、优化、文档治理与工作流更新|

**命名示例**：

- `feature/ppo-reward-shaping`
    
- `feature/add-lstm-network`
    
- `feature/update-workflow-docs`
    

---

### 5.2 开发前检查

1. `git pull`
    
2. `git status`
    
3. 如当前在 `main` 且准备做非微小改动，切换到 `feature/*`
    
4. 阅读 `README.md`、`KAIWU-WORKFLOW.md`、`GLOBAL_DOCS/算法总表.md`
    
5. 检查 `DEV_MEMORY/NOW.md`，确认是否有未完成轮次
    
6. 执行 `/kaiwu-dev-init`
    

---

### 5.3 Commit 规范

**语言要求：所有 commit message 必须使用中文**。

#### 小步提交（阶段性、可独立验证的步骤）

```text
<type>(<scope>): <简短描述>

- 改动内容：<具体改了什么>
- 涉及文件：<文件列表>
- 接口变化：<如有>
- 烟测状态：通过
```

**示例**：
```text
feat(preprocessor): 添加宝箱距离奖励

- 改动内容：在 reward_shaping 中添加最近宝箱距离奖励
- 涉及文件：agent_ppo/feature/preprocessor.py
- 接口变化：无
- 烟测状态：通过
```

#### 完整算法提交（算法完整实现并稳定）

```text
feat(<scope>): <算法完整名>

- 实现内容：<本轮完成的全部功能>
- 关键设计：<超参数、网络结构、奖励设计等>
- 涉及文件：<主要改动文件列表>
- 烟测状态：通过
- 训练状态：<待训练 / 训练中 / 得分 xxx>
- 算法文档：<对应文档路径>
```

**示例**：
```text
feat(ppo): agent_ppo_20260410_hok_memory_map_v1

- 实现内容：接入 HOK 风格记忆地图、16 维动作空间、分层奖励
- 关键设计：CNN 地图编码、目标记忆器、闪现脱险奖励
- 涉及文件：agent_ppo/conf/conf.py, agent_ppo/feature/preprocessor.py, agent_ppo/model/model.py
- 烟测状态：通过
- 训练状态：暂无正式训练得分
- 算法文档：GLOBAL_DOCS/算法文档/agent_ppo_20260410_hok_memory_map_v1/README.md
```

**禁止事项**：

- 不编造训练得分
    
- 不跳过文档同步做完整提交
    
- 不在 `main` 直接做非微小改动
    

---

### 5.4 Push / Merge 规则

1. 本地验证通过
    
2. 文档已同步
    
3. 用户确认后再 push
    
4. 完整验证前不合并到 `main`
    

---

## 6. 人机协作边界

### 6.1 人负责

- 决定本轮优化目标和主假设
    
- 外部调研算法、论文、改进方向，并写入 `GLOBAL_DOCS/算法调研.md`
    
- 与 AI 讨论并确认算法设计方案
    
- 启动真实平台训练，提供训练结果
    
- 决定是否继续、切换、合并、push
    

---

### 6.2 AI 负责

- 读取仓库文档和开发文档
    
- 分析基线与当前算法实现
    
- 将调研方向转化为设计方案
    
- 完成代码修改与最小验证
    
- 维护 `DEV_MEMORY/NOW.md`
    
- 分析训练结果并给出建议
    
- 稳定后归档到 `GLOBAL_DOCS`
    

**约束**：

- 实现阶段允许做本地 commit
    
- 不虚构训练结果
    
- 不自动 push / merge
    
- merge 前必须确认算法文档与算法总表已同步
    

---

### 6.3 协作原则

- 人提方向，AI 负责落地
    
- AI 不虚构训练结果
    
- AI 不自动 push / merge
    
- 所有归档内容必须经过验证
    

---

## 7. 快速参考

### 7.1 最小验证命令

```bash
docker exec -it kaiwu-dev-kaiwudrl-1 bash
python3 train_test.py
```

---

### 7.2 代码入口链

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

---

### 7.3 常见修改定位

|目标|文件|
|---|---|
|奖励 / 特征 / 合法动作|`agent_ppo/feature/preprocessor.py`|
|样本结构 / GAE|`agent_ppo/feature/definition.py`|
|网络结构|`agent_ppo/model/model.py`|
|PPO 损失|`agent_ppo/algorithm/algorithm.py`|
|超参数|`agent_ppo/conf/conf.py`|
|训练循环 / workflow / 监控|`agent_ppo/workflow/train_workflow.py`|

---

## 8. 完整工作流示例

**场景：从调研到训练结果整理的完整周期**

```text
# 阶段 1：设计
/kaiwu-dev-init
# -> 确认当前分支，NOW.md 为空

/kaiwu-algo-compare "添加LSTM网络"
# -> 对比当前 baseline 和候选方向，判断收益 / 风险 / 改动范围
# -> 若结论成立，再进入设计阶段

/kaiwu-algo-design "添加LSTM网络"
# -> 读取算法调研.md，了解基线
# -> 与用户讨论：LSTM 维度、seq_len、学习率调整
# -> 生成算法完整名：agent_ppo_20260410_lstm_v1
# -> 写入 NOW.md

# 阶段 2：实现（多轮小步迭代）
/kaiwu-algo-implementation
# -> 第 1 步：修改 model.py 添加 LSTM 层
#    烟测 -> 更新 NOW -> 小步 commit
# -> 第 2 步：调整 conf.py 超参数
#    烟测 -> 更新 NOW -> 小步 commit
# -> 第 3 步：修改 workflow 支持序列输入
#    烟测 -> 更新 NOW -> 小步 commit
# -> 最终烟测 -> 最终 commit
# -> 创建算法文档目录结构：
#    GLOBAL_DOCS/算法文档/agent_ppo_20260410_lstm_v1/
#    ├── README.md      # 算法文档初稿（不含训练结果）
#    └── html/   # 空目录，等待训练完成后放入 HTML 文档

# 阶段 3：训练（人执行）
人：在平台启动训练，记录任务 ID 和结果

# 阶段 4：训练结果整理（人主导）
# -> 人工查看官方训练监控并导出 HTML 文档
# -> 在官网上传模型，命名严格遵循 <算法完整名>_<训练步数>
# -> 对开放 10 图做 5 次官方评估
# -> 将训练监控 HTML 文档与最终评估结果 HTML 文档放入对应算法文档目录的 html/
# -> 在正式算法文档中补充 10 张地图得分与评估结论；如需文档同步，再让 AI 更新算法总表与正式算法文档

# 阶段 5：归档
/kaiwu-memory-archive
# -> 更新正式算法文档（补充训练结果到已有 README.md）
# -> 更新算法总表
# -> 重置 NOW.md
```

---

## 9. 最简流程速查

```text
算法调研
-> /kaiwu-dev-init
-> /kaiwu-algo-compare
-> /kaiwu-algo-design
-> /kaiwu-algo-implementation
-> 本地 smoke test
-> 人执行平台训练
-> 人工查看官方训练监控、完成 5 次官网评估并归档 HTML 文档
-> /kaiwu-memory-archive
-> 结束
```
