---
name: kaiwu-doc-query
description: Query the Gorge Chase development documentation for environment rules, data protocols, framework interfaces, and workflow APIs. Route the question to the correct document and keep documentation-query experience in sync when helpful.
argument-hint: [question-or-topic]
allowed-tools: Read, Grep, Glob, Edit, Write
---

# KaiWu Doc Query

查询目标：$ARGUMENTS

## 目标

从 `开发文档/` 中定位最合适的文档来源，回答环境规则、字段协议、框架接口和 workflow 相关问题。

## 执行步骤

### Step 1：问题分类

先判断问题属于：

- 赛题规则
- 环境配置
- 数据协议
- Agent 接口
- 模型 / 算法 / workflow
- 监控与日志

### Step 2：从索引进入

优先读取：

1. `开发文档/README.md`
2. 对应的拆分文档

### Step 3：回答时标注来源

输出时尽量包含：

- 直接结论
- 关键字段 / 参数 / 接口
- 来源文档


## 规则

- 优先引用文档中的确定性信息。
- 文档未明确说明时，不要强行推断；可给出”合理推断”并明确标注。

---

## 下一步行动（执行后可选输出）

文档查询通常是一次性获取信息，但可根据问题类型建议：

| 场景 | 建议下一步 |
|------|-----------|
| 查询的是环境/数据协议问题 | 如需实现算法，使用 `/kaiwu-algo-design` 或 `/kaiwu-algo-implementation` |
| 查询的是训练监控问题 | 如需整理训练结果，优先查看官方训练监控，按 `算法完整名 + 训练步数` 上传模型做 5 次官方评估，并把训练 HTML 文档与评估结果 HTML 文档归档到算法文档目录的 `html/` |
| 查询后发现当前算法有问题 | 使用 `/kaiwu-current-algo-analysis` 全面分析 |
| 信息不足需要设计新算法 | 使用 `/kaiwu-algo-design` |
