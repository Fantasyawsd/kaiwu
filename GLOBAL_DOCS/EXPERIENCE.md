# GLOBAL EXPERIENCE

## 可复用经验

### 1. 正式算法实现统一放在 `agent_ppo/`

- `agent_diy/` 只保留为模板，不作为正式算法演进目录。
- 这样可以避免算法总表、代码目录和正式算法文档长期漂移。

### 2. Reward 必须同时看两层

- 即时奖励在 `agent_ppo/feature/preprocessor.py`
- 终局奖励在 `agent_ppo/workflow/train_workflow.py`

只改其中一个文件，很容易误判 reward 整体设计。

### 3. 当前动作空间不是环境原生全量动作

- 环境原生是 16 维动作。
- 当前基线只使用 8 维移动动作。

如果要接入闪现，需要同步修改配置、preprocessor、模型输出和数据定义，不是单点改动。
