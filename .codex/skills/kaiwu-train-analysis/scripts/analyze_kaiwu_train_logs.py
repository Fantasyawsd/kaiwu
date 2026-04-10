#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


LEARNER_START_RE = re.compile(r"learner train process start at pid is (?P<pid>\d+)")
LEARNER_TRAIN_RE = re.compile(
    r"\[train\] total_loss:(?P<total_loss>-?\d+(?:\.\d+)?) "
    r"policy_loss:(?P<policy_loss>-?\d+(?:\.\d+)?) "
    r"value_loss:(?P<value_loss>-?\d+(?:\.\d+)?) "
    r"entropy:(?P<entropy>-?\d+(?:\.\d+)?) "
    r"approx_kl:(?P<approx_kl>-?\d+(?:\.\d+)?) "
    r"beta:(?P<beta>-?\d+(?:\.\d+)?)"
)
LEARNER_STEP_RE = re.compile(
    r"train count is (?P<train_count>\d+), global step is (?P<global_step>\d+), "
    r"train once cost time is (?P<train_ms>-?\d+(?:\.\d+)?) ms "
    r"\(data_fetch: (?P<data_fetch_ms>-?\d+(?:\.\d+)?) ms, "
    r"real_train: (?P<real_train_ms>-?\d+(?:\.\d+)?) ms\), "
    r"filter sample count is (?P<filter_sample_count>\d+), "
    r"sample_production_and_consumption_ratio is "
    r"(?P<sample_ratio>-?\d+(?:\.\d+)?)"
)
BUFFER_UTIL_RE = re.compile(r"'buffer_utilization': '(\d+)/(\d+)'")
LEARNER_SKIP_RE = re.compile(
    r"skip update due to approx_kl=(?P<approx_kl>-?\d+(?:\.\d+)?) > "
    r"target_kl=(?P<target_kl>-?\d+(?:\.\d+)?)"
)
GAMEOVER_RE = re.compile(
    r"\[GAMEOVER\] episode:(?P<episode>\d+) "
    r"steps:(?P<steps>\d+) result:(?P<result>\w+) "
    r"sim_score:(?P<sim_score>-?\d+(?:\.\d+)?) "
    r"(?:treasures:(?P<treasures>\d+) "
    r"flash:(?P<flash>\d+) )?"
    r"total_reward:(?P<total_reward>-?\d+(?:\.\d+)?)"
)
ENV_FINISH_RE = re.compile(r"finish monitor_data is (?P<data>\{.*\})")


@dataclass(frozen=True)
class RunWindow:
    start_time: datetime | None
    learner_pid: int | None
    source_file: Path | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Parse KaiWu training logs, export structured CSV files, plot curves, "
            "and write a markdown/json summary."
        )
    )
    parser.add_argument(
        "--log-root",
        type=Path,
        default=default_log_root(),
        help="Root directory that contains learner/aisrv/kaiwu_env log folders.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write CSV/PNG/summary outputs. Defaults to train/analysis/<run-label>.",
    )
    parser.add_argument(
        "--start-time",
        type=str,
        default=None,
        help="Inclusive local start time, for example 2026-04-10T14:56:44.",
    )
    parser.add_argument(
        "--end-time",
        type=str,
        default=None,
        help="Inclusive local end time, for example 2026-04-10T15:27:15.",
    )
    parser.add_argument(
        "--all-history",
        action="store_true",
        help="Analyze all available log history instead of auto-detecting the latest learner run.",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Custom chart/report title.",
    )
    return parser.parse_args()


def default_log_root() -> Path:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[5]
    candidate = repo_root / "train" / "log"
    if candidate.exists():
        return candidate

    cwd_candidate = Path.cwd() / "train" / "log"
    return cwd_candidate


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def isoformat_or_none(value: datetime | None) -> str | None:
    return value.isoformat(sep=" ") if value else None


def ensure_log_root(log_root: Path) -> Path:
    log_root = log_root.resolve()
    if not log_root.exists():
        raise FileNotFoundError(f"log root does not exist: {log_root}")
    return log_root


def discover_log_files(log_root: Path) -> dict[str, list[Path]]:
    modules = {}
    for module in ("learner", "aisrv", "kaiwu_env"):
        module_dir = log_root / module
        modules[module] = sorted(module_dir.glob("*.log")) if module_dir.exists() else []
    return modules


def parse_json_line(line: str, source_file: Path) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None

    obj = json.loads(line)
    obj["_source_file"] = str(source_file)
    obj["_time"] = datetime.fromisoformat(obj["time"])
    return obj


def iter_json_records(
    files: Iterable[Path],
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> Iterable[dict[str, Any]]:
    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                record = parse_json_line(raw_line, path)
                if record is None:
                    continue

                record_time = record["_time"]
                if start_time and record_time < start_time:
                    continue
                if end_time and record_time > end_time:
                    continue
                yield record


def detect_latest_run_window(learner_files: Iterable[Path]) -> RunWindow:
    latest_time: datetime | None = None
    latest_pid: int | None = None
    latest_file: Path | None = None

    for record in iter_json_records(learner_files):
        match = LEARNER_START_RE.search(record.get("message", ""))
        if not match:
            continue
        record_time = record["_time"]
        if latest_time is None or record_time > latest_time:
            latest_time = record_time
            latest_pid = int(match.group("pid"))
            latest_file = Path(record["_source_file"])

    return RunWindow(start_time=latest_time, learner_pid=latest_pid, source_file=latest_file)


def to_dataframe(rows: list[dict[str, Any]], sort_by: str) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(sort_by).reset_index(drop=True)


def parse_buffer_utilization(message: str) -> tuple[int | None, int | None]:
    match = BUFFER_UTIL_RE.search(message)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def parse_learner(records: Iterable[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_rows: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []
    skip_rows: list[dict[str, Any]] = []

    for record in records:
        message = record.get("message", "")
        base = {
            "time": record["_time"],
            "pid": record.get("pid"),
            "source_file": record["_source_file"],
            "level": record.get("level"),
        }

        train_match = LEARNER_TRAIN_RE.search(message)
        if train_match:
            row = dict(base)
            for key, value in train_match.groupdict().items():
                row[key] = float(value)
            train_rows.append(row)
            continue

        step_match = LEARNER_STEP_RE.search(message)
        if step_match:
            row = dict(base)
            for key, value in step_match.groupdict().items():
                row[key] = float(value) if "." in value else int(value)
            used, capacity = parse_buffer_utilization(message)
            row["buffer_used"] = used
            row["buffer_capacity"] = capacity
            step_rows.append(row)
            continue

        skip_match = LEARNER_SKIP_RE.search(message)
        if skip_match:
            row = dict(base)
            row["approx_kl"] = float(skip_match.group("approx_kl"))
            row["target_kl"] = float(skip_match.group("target_kl"))
            skip_rows.append(row)

    return (
        to_dataframe(train_rows, "time"),
        to_dataframe(step_rows, "time"),
        to_dataframe(skip_rows, "time"),
    )


def parse_aisrv(records: Iterable[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for record in records:
        message = record.get("message", "")
        match = GAMEOVER_RE.search(message)
        if not match:
            continue

        row: dict[str, Any] = {
            "time": record["_time"],
            "pid": record.get("pid"),
            "source_file": record["_source_file"],
            "episode": int(match.group("episode")),
            "steps": int(match.group("steps")),
            "result": match.group("result"),
            "sim_score": float(match.group("sim_score")),
            "treasures": int(match.group("treasures")) if match.group("treasures") else None,
            "flash": int(match.group("flash")) if match.group("flash") else None,
            "total_reward": float(match.group("total_reward")),
        }
        rows.append(row)

    df = to_dataframe(rows, "time")
    if not df.empty:
        df["is_win"] = (df["result"] == "WIN").astype(int)
        df["rolling_win_rate_100"] = df["is_win"].rolling(window=100, min_periods=1).mean()
        df["rolling_sim_score_100"] = df["sim_score"].rolling(window=100, min_periods=1).mean()
        df["rolling_total_reward_100"] = df["total_reward"].rolling(window=100, min_periods=1).mean()
        if "treasures" in df.columns:
            df["rolling_treasures_100"] = df["treasures"].rolling(window=100, min_periods=1).mean()
        if "flash" in df.columns:
            df["rolling_flash_100"] = df["flash"].rolling(window=100, min_periods=1).mean()
    return df


def parse_env(records: Iterable[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for record in records:
        message = record.get("message", "")
        match = ENV_FINISH_RE.search(message)
        if not match:
            continue

        payload = ast.literal_eval(match.group("data"))
        row: dict[str, Any] = {
            "time": record["_time"],
            "pid": record.get("pid"),
            "source_file": record["_source_file"],
        }
        row.update(payload)
        rows.append(row)

    df = to_dataframe(rows, "time")
    if not df.empty:
        df["record_index"] = range(1, len(df) + 1)
    return df


def build_output_dir(
    requested_output_dir: Path | None,
    log_root: Path,
    run_window: RunWindow,
    start_time: datetime | None,
) -> Path:
    if requested_output_dir is not None:
        return requested_output_dir.resolve()

    label = "all-history"
    if run_window.start_time:
        pid_part = f"_pid{run_window.learner_pid}" if run_window.learner_pid is not None else ""
        label = run_window.start_time.strftime("%Y%m%d_%H%M%S") + pid_part
    elif start_time:
        label = start_time.strftime("%Y%m%d_%H%M%S")

    return (log_root.parent / "analysis" / label).resolve()


def numeric_last(df: pd.DataFrame, column: str) -> float | None:
    if df.empty or column not in df.columns:
        return None
    value = df.iloc[-1][column]
    return float(value) if pd.notna(value) else None


def numeric_max(df: pd.DataFrame, column: str) -> float | None:
    if df.empty or column not in df.columns:
        return None
    value = df[column].max()
    return float(value) if pd.notna(value) else None


def numeric_min(df: pd.DataFrame, column: str) -> float | None:
    if df.empty or column not in df.columns:
        return None
    value = df[column].min()
    return float(value) if pd.notna(value) else None


def numeric_mean(df: pd.DataFrame, column: str) -> float | None:
    if df.empty or column not in df.columns:
        return None
    value = df[column].mean()
    return float(value) if pd.notna(value) else None


def collect_end_time(*frames: pd.DataFrame) -> datetime | None:
    candidates: list[datetime] = []
    for frame in frames:
        if not frame.empty and "time" in frame.columns:
            candidates.append(frame["time"].max())
    return max(candidates) if candidates else None


def write_csvs(
    output_dir: Path,
    learner_train_df: pd.DataFrame,
    learner_step_df: pd.DataFrame,
    learner_skip_df: pd.DataFrame,
    aisrv_df: pd.DataFrame,
    env_df: pd.DataFrame,
) -> dict[str, str]:
    outputs: dict[str, str] = {}
    dataframes = {
        "learner_train_metrics.csv": learner_train_df,
        "learner_step_metrics.csv": learner_step_df,
        "learner_skip_updates.csv": learner_skip_df,
        "aisrv_episode_metrics.csv": aisrv_df,
        "env_episode_metrics.csv": env_df,
    }

    for filename, frame in dataframes.items():
        if frame.empty:
            continue
        path = output_dir / filename
        serializable = frame.copy()
        if "time" in serializable.columns:
            serializable["time"] = serializable["time"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        serializable.to_csv(path, index=False, encoding="utf-8")
        outputs[filename] = str(path)

    return outputs


def build_summary(
    log_root: Path,
    output_dir: Path,
    files: dict[str, list[Path]],
    run_window: RunWindow,
    start_time: datetime | None,
    end_time: datetime | None,
    learner_train_df: pd.DataFrame,
    learner_step_df: pd.DataFrame,
    learner_skip_df: pd.DataFrame,
    aisrv_df: pd.DataFrame,
    env_df: pd.DataFrame,
    csv_outputs: dict[str, str],
    chart_path: Path,
) -> dict[str, Any]:
    effective_end_time = end_time or collect_end_time(
        learner_train_df, learner_step_df, learner_skip_df, aisrv_df, env_df
    )
    duration_seconds = None
    if start_time and effective_end_time:
        duration_seconds = round((effective_end_time - start_time).total_seconds(), 3)

    best_sim_score = None
    if not aisrv_df.empty:
        best_row = aisrv_df.loc[aisrv_df["sim_score"].idxmax()]
        best_sim_score = {
            "episode": int(best_row["episode"]),
            "sim_score": float(best_row["sim_score"]),
            "time": isoformat_or_none(best_row["time"]),
        }

    summary = {
        "log_root": str(log_root),
        "output_dir": str(output_dir),
        "time_window": {
            "start_time": isoformat_or_none(start_time),
            "end_time": isoformat_or_none(effective_end_time),
            "duration_seconds": duration_seconds,
        },
        "latest_run": {
            "learner_pid": run_window.learner_pid,
            "start_time": isoformat_or_none(run_window.start_time),
            "source_file": str(run_window.source_file) if run_window.source_file else None,
        },
        "source_files": {module: [str(path) for path in paths] for module, paths in files.items()},
        "artifacts": {
            "chart": str(chart_path),
            "csv": csv_outputs,
            "summary_markdown": str(output_dir / "summary.md"),
            "summary_json": str(output_dir / "summary.json"),
        },
        "learner": {
            "train_points": len(learner_train_df),
            "step_points": len(learner_step_df),
            "skip_updates": len(learner_skip_df),
            "last_total_loss": numeric_last(learner_train_df, "total_loss"),
            "min_total_loss": numeric_min(learner_train_df, "total_loss"),
            "last_value_loss": numeric_last(learner_train_df, "value_loss"),
            "last_policy_loss": numeric_last(learner_train_df, "policy_loss"),
            "last_entropy": numeric_last(learner_train_df, "entropy"),
            "last_approx_kl": numeric_last(learner_train_df, "approx_kl"),
            "last_global_step": numeric_last(learner_step_df, "global_step"),
            "last_train_count": numeric_last(learner_step_df, "train_count"),
            "mean_train_ms": numeric_mean(learner_step_df, "train_ms"),
            "mean_sample_ratio": numeric_mean(learner_step_df, "sample_ratio"),
        },
        "aisrv": {
            "episodes": len(aisrv_df),
            "wins": int(aisrv_df["is_win"].sum()) if "is_win" in aisrv_df.columns else 0,
            "win_rate": numeric_mean(aisrv_df, "is_win"),
            "last_sim_score": numeric_last(aisrv_df, "sim_score"),
            "mean_sim_score": numeric_mean(aisrv_df, "sim_score"),
            "max_sim_score": numeric_max(aisrv_df, "sim_score"),
            "last_total_reward": numeric_last(aisrv_df, "total_reward"),
            "mean_total_reward": numeric_mean(aisrv_df, "total_reward"),
            "max_total_reward": numeric_max(aisrv_df, "total_reward"),
            "mean_treasures": numeric_mean(aisrv_df, "treasures"),
            "max_treasures": numeric_max(aisrv_df, "treasures"),
            "mean_flash": numeric_mean(aisrv_df, "flash"),
            "max_flash": numeric_max(aisrv_df, "flash"),
            "last_steps": numeric_last(aisrv_df, "steps"),
            "mean_steps": numeric_mean(aisrv_df, "steps"),
            "max_steps": numeric_max(aisrv_df, "steps"),
            "best_sim_score_episode": best_sim_score,
        },
        "env": {
            "records": len(env_df),
            "last_total_score": numeric_last(env_df, "total_score"),
            "mean_total_score": numeric_mean(env_df, "total_score"),
            "max_total_score": numeric_max(env_df, "total_score"),
            "last_finished_steps": numeric_last(env_df, "finished_steps"),
            "mean_finished_steps": numeric_mean(env_df, "finished_steps"),
            "max_finished_steps": numeric_max(env_df, "finished_steps"),
            "mean_treasures_collected": numeric_mean(env_df, "treasures_collected"),
        },
    }
    return summary


def plot_or_note(ax: Any, has_data: bool, title: str) -> None:
    ax.set_title(title)
    if not has_data:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        ax.grid(False)


def plot_training_overview(
    output_path: Path,
    title: str,
    learner_train_df: pd.DataFrame,
    learner_step_df: pd.DataFrame,
    learner_skip_df: pd.DataFrame,
    aisrv_df: pd.DataFrame,
    env_df: pd.DataFrame,
) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(3, 2, figsize=(18, 14))
    fig.suptitle(title, fontsize=16)

    ax = axes[0, 0]
    has_data = not learner_train_df.empty
    plot_or_note(ax, has_data, "Learner Losses")
    if has_data:
        ax.plot(learner_train_df["time"], learner_train_df["total_loss"], label="total_loss")
        ax.plot(learner_train_df["time"], learner_train_df["value_loss"], label="value_loss")
        ax.set_xlabel("time")
        ax.legend()

    ax = axes[0, 1]
    has_data = not learner_train_df.empty or not learner_skip_df.empty
    plot_or_note(ax, has_data, "Learner Policy / KL")
    if not learner_train_df.empty:
        ax.plot(learner_train_df["time"], learner_train_df["policy_loss"], label="policy_loss")
        ax.plot(learner_train_df["time"], learner_train_df["entropy"], label="entropy")
        ax.plot(learner_train_df["time"], learner_train_df["approx_kl"], label="approx_kl")
    if not learner_skip_df.empty:
        ax.scatter(
            learner_skip_df["time"],
            learner_skip_df["approx_kl"],
            s=18,
            alpha=0.6,
            label="skip_update_approx_kl",
        )
    if has_data:
        ax.set_xlabel("time")
        ax.legend()

    ax = axes[1, 0]
    has_data = not learner_step_df.empty
    plot_or_note(ax, has_data, "Learner Train Cost")
    if has_data:
        x = learner_step_df["global_step"]
        ax.plot(x, learner_step_df["train_ms"], label="train_ms")
        ax.plot(x, learner_step_df["data_fetch_ms"], label="data_fetch_ms")
        ax.plot(x, learner_step_df["real_train_ms"], label="real_train_ms")
        ax.set_xlabel("global_step")
        ax.legend()

    ax = axes[1, 1]
    has_data = not aisrv_df.empty
    plot_or_note(ax, has_data, "Episode Sim Score / Reward")
    if has_data:
        ax.plot(aisrv_df["episode"], aisrv_df["sim_score"], label="sim_score", alpha=0.45)
        ax.plot(
            aisrv_df["episode"],
            aisrv_df["rolling_sim_score_100"],
            label="rolling_sim_score_100",
            linewidth=2.0,
        )
        reward_ax = ax.twinx()
        reward_ax.plot(
            aisrv_df["episode"],
            aisrv_df["rolling_total_reward_100"],
            color="tab:red",
            label="rolling_total_reward_100",
            linewidth=1.5,
        )
        ax.set_xlabel("episode")
        ax.legend(loc="upper left")
        reward_ax.legend(loc="upper right")

    ax = axes[2, 0]
    has_data = not aisrv_df.empty
    plot_or_note(ax, has_data, "Episode Steps / Win Rate")
    if has_data:
        ax.plot(aisrv_df["episode"], aisrv_df["steps"], label="steps", alpha=0.45)
        steps_roll = aisrv_df["steps"].rolling(window=100, min_periods=1).mean()
        ax.plot(aisrv_df["episode"], steps_roll, label="rolling_steps_100", linewidth=2.0)
        win_ax = ax.twinx()
        win_ax.plot(
            aisrv_df["episode"],
            aisrv_df["rolling_win_rate_100"],
            color="tab:green",
            label="rolling_win_rate_100",
            linewidth=1.5,
        )
        ax.set_xlabel("episode")
        ax.legend(loc="upper left")
        win_ax.legend(loc="upper right")

    ax = axes[2, 1]
    has_data = not env_df.empty
    plot_or_note(ax, has_data, "Env Scores / Steps")
    if has_data:
        x = env_df["record_index"] if "record_index" in env_df.columns else range(1, len(env_df) + 1)
        ax.plot(x, env_df["total_score"], label="total_score", alpha=0.5)
        score_roll = env_df["total_score"].rolling(window=100, min_periods=1).mean()
        ax.plot(x, score_roll, label="rolling_total_score_100", linewidth=2.0)

        if "finished_steps" in env_df.columns:
            env_ax = ax.twinx()
            env_ax.plot(
                x,
                env_df["finished_steps"].rolling(window=100, min_periods=1).mean(),
                color="tab:purple",
                label="rolling_finished_steps_100",
                linewidth=1.5,
            )
            env_ax.legend(loc="upper right")

        ax.set_xlabel("env_record_index")
        ax.legend(loc="upper left")

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def write_summary_files(output_dir: Path, summary: dict[str, Any]) -> None:
    summary_json_path = output_dir / "summary.json"
    with summary_json_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    learner = summary["learner"]
    aisrv = summary["aisrv"]
    env = summary["env"]
    time_window = summary["time_window"]
    latest_run = summary["latest_run"]
    artifacts = summary["artifacts"]

    markdown = f"""# KaiWu 训练日志分析摘要

## 运行范围
- 日志根目录: `{summary["log_root"]}`
- 输出目录: `{summary["output_dir"]}`
- 开始时间: `{time_window["start_time"]}`
- 结束时间: `{time_window["end_time"]}`
- 持续秒数: `{time_window["duration_seconds"]}`
- 最新 learner PID: `{latest_run["learner_pid"]}`
- 最新 learner 启动日志: `{latest_run["source_file"]}`

## Learner
- 训练指标点数: `{learner["train_points"]}`
- 训练步统计点数: `{learner["step_points"]}`
- skip update 次数: `{learner["skip_updates"]}`
- 最新 total_loss: `{learner["last_total_loss"]}`
- 最低 total_loss: `{learner["min_total_loss"]}`
- 最新 value_loss: `{learner["last_value_loss"]}`
- 最新 policy_loss: `{learner["last_policy_loss"]}`
- 最新 entropy: `{learner["last_entropy"]}`
- 最新 approx_kl: `{learner["last_approx_kl"]}`
- 最新 global_step: `{learner["last_global_step"]}`
- 平均 train_ms: `{learner["mean_train_ms"]}`
- 平均 sample_ratio: `{learner["mean_sample_ratio"]}`

## AISrv
- 对局数: `{aisrv["episodes"]}`
- 胜局数: `{aisrv["wins"]}`
- 胜率: `{aisrv["win_rate"]}`
- 最新 sim_score: `{aisrv["last_sim_score"]}`
- 平均 sim_score: `{aisrv["mean_sim_score"]}`
- 最大 sim_score: `{aisrv["max_sim_score"]}`
- 最新 total_reward: `{aisrv["last_total_reward"]}`
- 平均 total_reward: `{aisrv["mean_total_reward"]}`
- 最大 total_reward: `{aisrv["max_total_reward"]}`
- 平均 treasures: `{aisrv["mean_treasures"]}`
- 最大 treasures: `{aisrv["max_treasures"]}`
- 平均 flash: `{aisrv["mean_flash"]}`
- 最大 flash: `{aisrv["max_flash"]}`
- 平均 steps: `{aisrv["mean_steps"]}`
- 最大 steps: `{aisrv["max_steps"]}`
- 最佳 sim_score 对局: `{aisrv["best_sim_score_episode"]}`

## Env
- 记录数: `{env["records"]}`
- 最新 total_score: `{env["last_total_score"]}`
- 平均 total_score: `{env["mean_total_score"]}`
- 最大 total_score: `{env["max_total_score"]}`
- 最新 finished_steps: `{env["last_finished_steps"]}`
- 平均 finished_steps: `{env["mean_finished_steps"]}`
- 平均 treasures_collected: `{env["mean_treasures_collected"]}`

## 产物
- 总览图: `{artifacts["chart"]}`
- CSV: `{artifacts["csv"]}`
- JSON 摘要: `{artifacts["summary_json"]}`
"""

    summary_md_path = output_dir / "summary.md"
    summary_md_path.write_text(markdown, encoding="utf-8")


def main() -> int:
    args = parse_args()
    log_root = ensure_log_root(args.log_root)
    files = discover_log_files(log_root)
    if not any(files.values()):
        raise FileNotFoundError(f"no log files found under: {log_root}")

    run_window = detect_latest_run_window(files["learner"])
    start_time = parse_time(args.start_time)
    end_time = parse_time(args.end_time)

    if start_time is None and not args.all_history:
        start_time = run_window.start_time

    output_dir = build_output_dir(args.output_dir, log_root, run_window, start_time)
    output_dir.mkdir(parents=True, exist_ok=True)

    learner_records = list(iter_json_records(files["learner"], start_time, end_time))
    aisrv_records = list(iter_json_records(files["aisrv"], start_time, end_time))
    env_records = list(iter_json_records(files["kaiwu_env"], start_time, end_time))

    learner_train_df, learner_step_df, learner_skip_df = parse_learner(learner_records)
    aisrv_df = parse_aisrv(aisrv_records)
    env_df = parse_env(env_records)

    csv_outputs = write_csvs(
        output_dir,
        learner_train_df,
        learner_step_df,
        learner_skip_df,
        aisrv_df,
        env_df,
    )

    title = args.title or (
        f"KaiWu Train Analysis"
        + (f" from {start_time.strftime('%Y-%m-%d %H:%M:%S')}" if start_time else "")
    )
    chart_path = output_dir / "training_overview.png"
    plot_training_overview(
        chart_path,
        title,
        learner_train_df,
        learner_step_df,
        learner_skip_df,
        aisrv_df,
        env_df,
    )

    summary = build_summary(
        log_root=log_root,
        output_dir=output_dir,
        files=files,
        run_window=run_window,
        start_time=start_time,
        end_time=end_time,
        learner_train_df=learner_train_df,
        learner_step_df=learner_step_df,
        learner_skip_df=learner_skip_df,
        aisrv_df=aisrv_df,
        env_df=env_df,
        csv_outputs=csv_outputs,
        chart_path=chart_path,
    )
    write_summary_files(output_dir, summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"[kaiwu-train-analysis] {exc}", file=sys.stderr)
        raise
