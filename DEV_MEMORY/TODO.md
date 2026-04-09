# DEV TODO

## 当前恢复状态

- [x] 恢复根目录治理文档：`README.md`、`KAIWU-WORKFLOW.md`、`CONTRIBUTE.md`
- [x] 恢复 `GLOBAL_DOCS/` 与 `DEV_MEMORY/` 基础结构
- [x] 恢复正式算法文档与算法总表，当前基线指向 `agent_ppo_20260409_1733`
- [x] 恢复 `.claude/skills/`、`.codex/skills/`、`.copilot/skills/` 下的核心 repo-local skills
- [x] 补齐兼容别名文件：`KAIWU_WORKFLOW.md`、`人类开发者前置知识.md`、`面向人类开发者的开发文档.md`
- [x] 检查 Markdown 本地链接是否断裂，当前结果：无断链

## 可选后续动作

- [ ] 若需要运行态确认，先恢复 Docker daemon，再在容器内执行 `python3 train_test.py`
- [ ] 若用户准备继续算法开发，先确认本轮新目标，再按 `KAIWU-WORKFLOW.md` 进入下一轮
- [ ] 若用户准备整理版本基线，可在恢复完成后做一次新的本地 commit

## 当前判断

- 当前没有明确需要继续的未完成算法改动
- 当前恢复重点已经从“补文件”转为“是否需要做运行态验证 / Git 收口”
