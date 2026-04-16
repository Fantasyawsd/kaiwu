# NOW

## 当前要实现的算法具体内容

- 补齐训练启动时的 ckpt 续训逻辑，并整理对应的监控与文档说明。
- 当前 Gorge Chase 仓库已改为优先使用 `conf/configure_app.toml` 中的 `preload_model_path` 作为续训入口。
- 若 `preload_model_path` 指向真实 `.zip` / `.pkl` 文件，则直接从该 ckpt 恢复模型；若为空或目标文件不存在，则自动回退为从头训练。
- 若从 ckpt 恢复，则 episode / curriculum / eval 节奏也要尽量沿用 ckpt 中保存的进度，而不是重新从 0 开始。

## 当前实现进度

- 已完成的代码改动：
- `conf/configure_app.toml` 现已直接提供 `preload_model_path`，并保持 `preload_model = false`，避免触发框架旧的 `preload_model_dir + preload_model_id` 入口。
- 新增 `agent_ppo/resume_utils.py`，统一处理 ckpt 解析、resume 元数据提取、共享进度快照读写。
- `resume_utils.py` 已支持直接解析 KaiWu 导出的 `.zip` checkpoint，并自动从压缩包里定位 `ckpt/model.ckpt-*.pkl`。
- 对于平台导出的 `.zip`，若压缩包内部没有业务侧 `resume_metadata`，当前实现会读取同名 `.zip.json` 中的 `train_step`，按近似 episode 进度恢复训练节奏。
- `Agent.save_model()` 会把 resume 元数据和模型权重一起写入 ckpt，并额外写 sidecar json。
- `Agent.load_model()` 支持加载新 ckpt 格式，也兼容旧的纯 `state_dict` ckpt；当 `latest` 不存在时会回退到配置 ckpt 或 fresh init。
- `EpisodeRunner` 会持续同步 `episode_cnt`、`completed_episode_count`、`train_episode_total`、`train_episode_since_last_eval`，并在检测到 resume ckpt 时恢复 episode / curriculum / eval 计数。
- `resume_progress.json` 的写盘路径已改为按仓库根目录解析，并使用唯一临时文件 + 原子替换，修复了 `resume_progress.json.tmp -> resume_progress.json` 的路径与并发写问题。
- `Progress` 组监控已增加按 episode 抽样，当前默认每 `10` 局才上报一次进度监控，且仅在该抽样局的开局、结算、以及每 `50` 步上报一次，用于减少 `monitor_proxy` 的限流丢弃。
- 已完成的文档同步：
- 已在 `开发文档/开发文档.md` 与 `开发文档/腾讯开悟强化学习框架/分布式计算框架.md` 中补充 Gorge Chase 仓库当前适配说明，明确 `preload_model_path` 的实际用法与 `.zip` ckpt 的恢复行为。
- 已完成的验证：
- Docker 中多次执行 `python3 train_test.py`，确认可从 `ckpt/gorge_chase-ppo-11289-2026_04_15_00_09_54-15.0.1.zip` 恢复。
- 训练日志确认从 `Episode 11290`、`Episode 11291` 开始继续运行，stage 为 `hard_generalization`。
- 已确认不再出现以下历史问题：
- 框架旧入口报错：`preload model file failed, preload_model_dir ... preload_model_id ... not valid`
- 路径写盘报错：`No such file or directory: 'agent_ppo/ckpt/resume_progress.json.tmp'`
- 监控高频丢弃在短烟测中已明显收敛，短测未再观察到 `monitor_proxy ... will drop`
- 当前代码状态：
- 相关改动已提交并推送：
- commit: `030f472`
- message: `feat(resume): support direct checkpoint path resume`
- branch: `dev`

## 下一步计划

- 正式训练时继续使用 `preload_model_path` 作为唯一续训入口，不再依赖 `preload_model_dir + preload_model_id`。
- 若后续平台侧要正式使用“精确续接 episode / eval / curriculum”的能力，优先使用包含业务侧 `resume_metadata` 的新格式 ckpt；平台导出的纯权重 `.zip` 目前仍是按 `train_step` 近似恢复。
- 若正式长训中仍偶发 `monitor_proxy ... will drop`，优先再观察 `Progress` 组抽样后的实际频率，必要时再评估是否提升框架 `max_report_monitor_count_per_minutes`。
- 若本轮续训能力已稳定可用，可在后续阶段进入归档整理，并由 `/kaiwu-memory-archive` 继续收尾。
