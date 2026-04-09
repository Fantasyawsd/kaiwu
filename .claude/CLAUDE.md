# Repo Agent Instructions



This repository expects coding agents such as Codex to begin every new context by reading the core project guidance files before doing other repository work.



## Default startup rule



At the start of each new context in this repository, read these files first:



1. `README.md`
2. `KAIWU-WORKFLOW.md`



## When resuming or continuing development



After reading the two files above, read the current-state memory files before deciding what to do next:



1. `GLOBAL_DOCS/算法总表.md`
2. `DEV_MEMORY/TODO.md`
3. `DEV_MEMORY/算法文档.md`



## Purpose



- `README.md` gives the stable project entry and navigation.

- `KAIWU-WORKFLOW.md` defines the standard collaboration and development flow.

- `GLOBAL_DOCS/算法总表.md` and `DEV_MEMORY/*` provide the current development state so the agent can resume work even without prior conversation context.



## Behavioral expectation



- Do not start code changes before reading the startup files above.

- Treat `DEV_MEMORY/*` as the primary source of current development-state memory.

- If `GLOBAL_DOCS/算法总表.md` and `DEV_MEMORY/*` disagree, surface the conflict before proceeding.