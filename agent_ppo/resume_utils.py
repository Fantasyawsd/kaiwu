#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Checkpoint resume helpers for Gorge Chase PPO."""

import json
import os
import time
import tomllib


RESUME_PROGRESS_SNAPSHOT_FILE = os.path.join("agent_ppo", "ckpt", "resume_progress.json")
RESUME_METADATA_KEYS = (
    "episode_cnt",
    "completed_episode_count",
    "train_episode_total",
    "train_episode_since_last_eval",
)
CHECKPOINT_WRAPPER_KEYS = {
    "model_state_dict",
    "state_dict",
    "model",
    "resume_metadata",
    "resume_state",
    "meta",
}


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_resume_metadata(metadata):
    if not isinstance(metadata, dict):
        return {}

    normalized = {
        key: _safe_int(metadata.get(key), 0)
        for key in RESUME_METADATA_KEYS
        if key in metadata
    }
    if not normalized:
        return {}

    normalized.setdefault("episode_cnt", normalized.get("completed_episode_count", 0))
    normalized.setdefault("completed_episode_count", normalized.get("episode_cnt", 0))
    normalized.setdefault("train_episode_total", normalized.get("completed_episode_count", 0))
    normalized.setdefault("train_episode_since_last_eval", 0)
    normalized["updated_at"] = _safe_int(metadata.get("updated_at"), int(time.time()))
    return normalized


def resolve_model_checkpoint_file(checkpoint_dir, checkpoint_id):
    if not checkpoint_dir or checkpoint_id in (None, ""):
        return None
    model_file = os.path.join(str(checkpoint_dir), f"model.ckpt-{str(checkpoint_id)}.pkl")
    return os.path.abspath(model_file)


def resolve_checkpoint_resume_sidecar(model_file):
    if not model_file:
        return None
    root, _ = os.path.splitext(model_file)
    return f"{root}.resume.json"


def _read_json_file(file_path):
    if not file_path or not os.path.isfile(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as file_obj:
            return json.load(file_obj)
    except (OSError, ValueError, TypeError):
        return {}


def _write_json_file(file_path, payload):
    if not file_path:
        return
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    tmp_file = f"{file_path}.tmp"
    with open(tmp_file, "w", encoding="utf-8") as file_obj:
        json.dump(payload, file_obj, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp_file, file_path)


def read_resume_progress_snapshot(snapshot_path=RESUME_PROGRESS_SNAPSHOT_FILE):
    return normalize_resume_metadata(_read_json_file(snapshot_path))


def write_resume_progress_snapshot(metadata, snapshot_path=RESUME_PROGRESS_SNAPSHOT_FILE):
    normalized = normalize_resume_metadata(metadata)
    if not normalized:
        return {}
    _write_json_file(snapshot_path, normalized)
    return normalized


def read_resume_metadata_sidecar(model_file):
    return normalize_resume_metadata(_read_json_file(resolve_checkpoint_resume_sidecar(model_file)))


def write_resume_metadata_sidecar(model_file, metadata):
    normalized = normalize_resume_metadata(metadata)
    if not normalized:
        return {}
    sidecar_file = resolve_checkpoint_resume_sidecar(model_file)
    _write_json_file(sidecar_file, normalized)
    return normalized


def _looks_like_state_dict(candidate):
    if not isinstance(candidate, dict) or not candidate:
        return False
    if any(key in CHECKPOINT_WRAPPER_KEYS for key in candidate):
        return False
    scalar_types = (str, bytes, int, float, bool, type(None))
    nested_types = (dict, list, tuple, set)
    return all(not isinstance(value, scalar_types + nested_types) for value in candidate.values())


def extract_model_state_dict(checkpoint_obj):
    if _looks_like_state_dict(checkpoint_obj):
        return checkpoint_obj
    if isinstance(checkpoint_obj, dict):
        for key in ("model_state_dict", "state_dict", "model"):
            state_dict = checkpoint_obj.get(key)
            if _looks_like_state_dict(state_dict):
                return state_dict
    return checkpoint_obj


def extract_resume_metadata_from_checkpoint(checkpoint_obj):
    if not isinstance(checkpoint_obj, dict):
        return {}

    for key in ("resume_metadata", "resume_state"):
        metadata = normalize_resume_metadata(checkpoint_obj.get(key))
        if metadata:
            return metadata

    meta = checkpoint_obj.get("meta")
    if isinstance(meta, dict):
        for key in ("resume_metadata", "resume_state"):
            metadata = normalize_resume_metadata(meta.get(key))
            if metadata:
                return metadata

    return {}


def load_checkpoint_object(model_file, map_location="cpu"):
    import torch

    return torch.load(model_file, map_location=map_location)


def load_resume_metadata_from_checkpoint_file(model_file):
    if not model_file or not os.path.isfile(model_file):
        return {}

    try:
        checkpoint_obj = load_checkpoint_object(model_file, map_location="cpu")
    except Exception:
        checkpoint_obj = None

    metadata = extract_resume_metadata_from_checkpoint(checkpoint_obj)
    if metadata:
        return metadata
    return read_resume_metadata_sidecar(model_file)


def read_configured_resume_checkpoint(config_path="conf/configure_app.toml"):
    state = {
        "configured": False,
        "enabled": False,
        "preload_model": False,
        "preload_model_dir": None,
        "preload_model_id": None,
        "model_file": None,
        "metadata": {},
    }

    try:
        with open(config_path, "rb") as file_obj:
            app_conf = tomllib.load(file_obj).get("app", {})
    except (OSError, tomllib.TOMLDecodeError):
        return state

    preload_model_dir = app_conf.get("preload_model_dir")
    preload_model_id = app_conf.get("preload_model_id")
    model_file = resolve_model_checkpoint_file(preload_model_dir, preload_model_id)
    configured = bool(preload_model_dir and preload_model_id not in (None, ""))
    enabled = bool(configured and model_file and os.path.isfile(model_file))

    state.update(
        {
            "configured": configured,
            "enabled": enabled,
            "preload_model": bool(app_conf.get("preload_model", False)),
            "preload_model_dir": preload_model_dir,
            "preload_model_id": preload_model_id,
            "model_file": model_file,
            "metadata": load_resume_metadata_from_checkpoint_file(model_file) if enabled else {},
        }
    )
    return state
