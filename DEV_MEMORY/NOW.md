# NOW

## 当前要实现的算法具体内容

- 补齐训练启动时的 ckpt 续训逻辑：
- 若 `conf/configure_app.toml` 中配置出的 `preload_model_path` 指向真实 `.zip` / `.pkl` 文件，则直接从该 ckpt 恢复模型。
- 若 `preload_model_path` 为空，或目标文件不存在，则自动回退为从头训练。
- 若从 ckpt 恢复，则 episode / curriculum / eval 节奏也要尽量沿用 ckpt 中保存的进度，而不是重新从 0 开始。

## 当前实现进度

- 已定位到当前续训链路落点：
- `conf/configure_app.toml` 直接提供 ckpt 文件地址。
- `agent_ppo/agent.py` 负责模型 ckpt 的读写。
- `agent_ppo/workflow/train_workflow.py` 维护 `episode_cnt`、`completed_episode_count`、`train_episode_total`、`train_episode_since_last_eval`。
- 已实现方案：
- 新增 `agent_ppo/resume_utils.py` 统一处理 ckpt 解析、resume 元数据提取、共享进度快照读写。
- `resume_utils.py` 现已支持直接解析 KaiWu 导出的 `.zip` checkpoint，并自动从压缩包里定位 `ckpt/model.ckpt-*.pkl`。
- `Agent.save_model()` 会把 resume 元数据和模型权重一起写入 ckpt，并额外写 sidecar json。
- `Agent.load_model()` 支持加载新 ckpt 格式，也兼容旧的纯 `state_dict` ckpt；当 `latest` 不存在时会回退到配置 ckpt 或 fresh init。
- `EpisodeRunner` 会把训练 episode 进度持续同步到共享快照，并在检测到 resume ckpt 时恢复 episode / curriculum / eval 计数。

## 下一步计划

- 做语法级验证，确认新增 resume 工具与训练 workflow 没有引入 Python 语法错误。
- 若环境允许，再补一次最小 smoke，验证“有 ckpt / 无 ckpt”两种入口都能正常起训。
- 若后续平台侧要正式用该能力，优先使用包含 resume 元数据的新格式 ckpt 作为续训入口。
