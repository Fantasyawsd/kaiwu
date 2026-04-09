# DEV CHANGELOG

## 当前记录

### 2026-04-09

- 变更类型：仓库治理层恢复
- 变更文件：
  - `README.md`
  - `KAIWU-WORKFLOW.md`
  - `CONTRIBUTE.md`
  - `GLOBAL_DOCS/*`
  - `开发文档/README.md`
  - `开发文档/EXPERIENCE.md`
- 说明：
  - 依据恢复方案重建较新的文档治理结构。
  - 恢复 `GLOBAL_DOCS/` 与 `DEV_MEMORY/` 双层知识体系。
  - 恢复当前 PPO 正式算法文档 `agent_ppo_20260409_1733.md` 与算法总表索引。
- 是否已验证：是；`compileall` 语法检查通过

### 2026-04-09

- 变更类型：repo-local skills 恢复
- 变更文件：
  - `.claude/skills/*`
  - `.codex/skills/*`
  - `.copilot/skills/*`
- 说明：
  - 恢复 7 个核心 KaiWu repo-local skills 的三套目录结构。
  - `kaiwu-full-iteration/SKILL.md` 以用户手动恢复版本为准，不覆盖。
- 是否已验证：是；目录结构已核对

### 2026-04-10

- 变更类型：兼容别名与文档一致性修复
- 变更文件：
  - `KAIWU_WORKFLOW.md`
  - `人类开发者前置知识.md`
  - `面向人类开发者的开发文档.md`
  - `DEV_MEMORY/算法文档.md`
  - `DEV_MEMORY/TODO.md`
  - `DEV_MEMORY/CHANGELOG.md`
  - `DEV_MEMORY/EXPERIENCE.md`
- 说明：
  - 补齐旧提示词/旧文档仍可能引用的兼容别名文件。
  - 修复 `人类开发者AI协作指南.md` 指向 `人类开发者前置知识.md` 的断链。
  - 将 `DEV_MEMORY` 从空模板更新为可直接接手的当前恢复状态说明。
- 是否已验证：是；Markdown 本地链接巡检结果为无断链

### 2026-04-10

- 变更类型：恢复后运行态验证尝试
- 变更文件：
  - `DEV_MEMORY/算法文档.md`
  - `DEV_MEMORY/TODO.md`
  - `DEV_MEMORY/EXPERIENCE.md`
- 说明：
  - 尝试按仓库约定执行 Docker 容器内 smoke test，但当前机器无法连接 Docker daemon。
  - 尝试本机执行 `python train_test.py`，在入口阶段因缺少平台依赖 `kaiwudrl` 失败。
  - 已将该验证边界写入当前状态文档，避免后续 AI 误判为“恢复后已跑通”。
- 是否已验证：是；已得到明确错误信息
