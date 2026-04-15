---
name: kaiwu-memory-archive
description: Finalize a completed development round by archiving NOW.md into the formal algorithm doc and the algorithm table, resetting NOW.md, creating the final commit, pushing the branch, and guiding the user to initiate merge.
argument-hint: [optional-algorithm-name]
allowed-tools: Bash(*), Read, Grep, Glob, Edit, Write
---

# KaiWu Memory Archive

归档目标：$ARGUMENTS

## 目标

作为完整开发流程的最后一步，把当前轮次已经稳定的信息正式归档到：

- `GLOBAL_DOCS/算法文档/`
- `GLOBAL_DOCS/算法总表.md`

然后重置 `DEV_MEMORY/NOW.md`，完成最终 `commit`、`push`，并告诉用户下一步如何发起 merge。

## 适用时机

只有在以下条件基本满足时才进入本 skill：

- 算法实现已完成
- `NOW.md` 已整理成算法文档初稿
- 已经拿到真实训练信息，或明确当前仅为“smoke test 通过、暂无正式训练结果”
- 归档内容已经稳定，准备收尾

## 执行步骤

### Step 1：读取归档输入

先读：

- `DEV_MEMORY/NOW.md`
- `GLOBAL_DOCS/算法总表.md`
- 当前算法对应的正式算法文档目录（若已存在）

确认：

- `NOW.md` 当前是否为算法文档初稿
- 需要归档的是新算法还是已有算法新版本
- 是否已经有真实训练结果
- 当前归档版本是否应成为新的“当前基线”，还是仅作为历史/候选版本保留

### Step 2：同步正式算法文档

将 `NOW.md` 中已经稳定的信息整理到 `GLOBAL_DOCS/算法文档/<算法完整名>/README.md`。

正式算法文档应包含：

- 算法概述
- 代码入口链路
- Agent 接口
- 特征处理
- 样本结构与 GAE
- 模型结构
- 算法训练逻辑
- 超参数汇总
- 环境配置
- 系统训练配置
- 训练 workflow
- 已知限制
- 真实训练信息（若已有）
- 官方训练监控 HTML 文档索引（HTML 文档由人放到 `GLOBAL_DOCS/算法文档/<算法完整名>/html/`）
- 官网模型评估记录：模型上传命名、5 次评估、10 张地图得分、最终结果 HTML 文档索引

### Step 3：同步算法总表

更新 `GLOBAL_DOCS/算法总表.md`，至少补齐：

- 算法完整名
- 当前状态
- 训练得分或“暂无正式训练结果”
- 对应正式算法文档入口路径
- 若本轮归档的是当前稳定主线版本，必须把该条目标为“当前基线”，并将旧基线降级为历史基线或已归档版本
- `GLOBAL_DOCS/算法总表.md` 中任意时刻只允许存在一个“当前基线”条目

### Step 4：重置 NOW.md

归档完成后，把 `DEV_MEMORY/NOW.md` 重置为新的轮次模板，只保留：

- 当前无进行中的实现，或新的下一轮计划
- 指向最新正式算法文档入口的引用

不要继续把上一轮详细实现留在 `NOW.md` 中。

推荐模板：

```markdown
# NOW

## 当前要实现的算法具体内容

- 暂无新的进行中实现；开始下一轮前先阅读 `GLOBAL_DOCS/算法总表.md` 与最新正式算法文档。

## 当前实现进度

- 当前处于归档完成后的初始化状态。
- 最近一次已归档算法文档：`GLOBAL_DOCS/算法文档/<算法完整名>/README.md`

## 下一步计划

- 若继续优化当前算法，先执行 `/kaiwu-dev-init`
- 若开启新方向，先查看 `GLOBAL_DOCS/算法调研.md`
```

### Step 5：检查收尾完整性

确认：

- [ ] `GLOBAL_DOCS/算法文档/<算法完整名>/README.md` 已创建或更新
- [ ] `GLOBAL_DOCS/算法文档/<算法完整名>/html/` 已预留，等待人工放入官方训练监控 HTML 文档与最终评估结果 HTML 文档
- [ ] `GLOBAL_DOCS/算法总表.md` 已更新
- [ ] 若本轮归档的是当前稳定主线版本，“当前基线”标记已切换到本轮算法，且旧基线角色已同步调整
- [ ] `DEV_MEMORY/NOW.md` 已重置
- [ ] 归档内容与真实训练信息一致
- [ ] 若已有官网评估结果，模型命名、5 次评估与 10 张地图得分已写入正式算法文档

### Step 6：最终 Git 收尾

执行：

1. `git status`
2. `git add` 归档相关文件
3. 创建最终 commit
4. `git push` 当前分支

推荐 commit message：

```text
feat(archive): 归档 <算法完整名>

- 将 NOW.md 归档到正式算法文档目录下的 `README.md`
- 更新 GLOBAL_DOCS/算法总表.md
- 重置 DEV_MEMORY/NOW.md
- 同步训练状态
```

### Step 7：指导用户发起 merge

push 完成后，明确告诉用户：

- 当前分支名
- 已推送远端
- 下一步去代码托管平台发起 merge / PR
- merge 前建议再检查哪些内容

## 规则

- 这是开发流程最后一步
- 不把过程性草稿原样复制进 `GLOBAL_DOCS`
- 不编造训练结果
- 归档完成后必须重置 `NOW.md`
- 归档时必须维护“当前基线”角色的一致性，不能让旧基线标记残留在算法总表中
- 归档完成后要完成最终 `commit` 与 `push`

---

## 下一步行动（执行后必须输出）

归档完成后，明确告诉用户：

```markdown
## 归档完成 - 下一步

### 已完成
- [x] 算法文档已归档到 `GLOBAL_DOCS/算法文档/<算法完整名>/README.md`
- [x] 官方训练监控与评估结果 HTML 文档目录 `html/` 已预留
- [x] 算法总表已更新
- [x] `DEV_MEMORY/NOW.md` 已重置
- [x] 代码已提交并推送到远端分支 `feature/<分支名>`

### 接下来请执行（用户操作）
1. 去代码托管平台（如 GitHub/GitLab）发起 Merge Request / Pull Request
2. 将 `feature/<分支名>` 合并到 `main`
3. Merge 前建议检查：
   - 算法文档是否完整
   - 训练结果是否真实
   - 是否影响其他正在进行的开发

### 合并后（回到 main 分支）
```bash
git checkout main
git pull
```

### 开启下一轮开发
合并完成后，如需继续：
- **优化当前算法**：使用 `/kaiwu-dev-init` 开始新一轮迭代
- **调研新方向**：查看 `GLOBAL_DOCS/算法调研.md` 和 `reference_algos/`
```
