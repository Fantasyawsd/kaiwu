#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
###########################################################################
# Copyright 漏 1998 - 2026 Tencent. All Rights Reserved.
###########################################################################
"""
Author: Tencent AI Arena Authors

Training workflow for Gorge Chase PPO.
"""

import os
import time
from dataclasses import dataclass, field

import numpy as np

from agent_ppo.conf.conf import Config
from agent_ppo.feature.definition import SampleData, sample_process
from common_python.utils.workflow_disaster_recovery import handle_disaster_recovery
from tools.metrics_utils import get_training_metrics
from tools.train_env_conf_validate import read_usr_conf


DIST_BUCKET_TO_DISTANCE = {
    0: 15.0,
    1: 45.0,
    2: 75.0,
    3: 105.0,
    4: 135.0,
    5: 165.0,
}
MAX_DISTANCE = 180.0


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_position(obj):
    if isinstance(obj, dict):
        if "pos" in obj and isinstance(obj["pos"], dict):
            obj = obj["pos"]
        if "x" in obj and "z" in obj:
            return np.array(
                [_safe_float(obj.get("x", 0.0)), _safe_float(obj.get("z", 0.0))],
                dtype=np.float32,
            )
    return None


def _distance_from_bucket(dist_bucket):
    return DIST_BUCKET_TO_DISTANCE.get(_safe_int(dist_bucket, 5), DIST_BUCKET_TO_DISTANCE[5])


def _extract_observation_parts(env_obs):
    observation = env_obs.get("observation", {})
    return observation, observation.get("frame_state", {}), observation.get("env_info", {})


def _extract_hero(frame_state):
    heroes = frame_state.get("heroes", {})
    if isinstance(heroes, list):
        return heroes[0] if heroes else {}
    return heroes if isinstance(heroes, dict) else {}


def _score_snapshot(frame_state, env_info):
    hero = _extract_hero(frame_state)
    step_score = _safe_float(env_info.get("step_score", hero.get("step_score", 0.0)))
    treasure_score = _safe_float(env_info.get("treasure_score", hero.get("treasure_score", 0.0)))
    total_score = _safe_float(env_info.get("total_score", step_score + treasure_score))
    treasures_collected = _safe_int(
        env_info.get("treasures_collected", hero.get("treasure_collected_count", 0))
    )
    return total_score, step_score, treasure_score, treasures_collected


def _entity_distance(entity, hero_pos):
    pos = _extract_position(entity)
    if pos is not None and hero_pos is not None:
        return float(np.linalg.norm(pos - hero_pos))
    return float(_distance_from_bucket(entity.get("hero_l2_distance", entity.get("distance_bucket", 5))))


def _nearest_treasure_distance(frame_state, hero_pos):
    distances = []
    for organ in frame_state.get("organs", []) or []:
        if _safe_int(organ.get("sub_type", 0)) != 1:
            continue
        if _safe_int(organ.get("status", 1)) == 0:
            continue
        distances.append(_entity_distance(organ, hero_pos))
    if not distances:
        return -1.0
    return float(min(distances))


def _danger_level(frame_state, hero_pos):
    distances = [_entity_distance(monster, hero_pos) for monster in (frame_state.get("monsters", []) or [])]
    if not distances:
        return 0.0
    min_distance = min(distances)
    return float(np.clip(1.0 - min_distance / MAX_DISTANCE, 0.0, 1.0))


def _round_metric_dict(metric_dict):
    rounded = {}
    for key, value in metric_dict.items():
        if isinstance(value, (int, np.integer)):
            rounded[key] = int(value)
        else:
            rounded[key] = round(float(value), 4)
    return rounded


def _mean_metric_dict(metric_dicts):
    if not metric_dicts:
        return {}
    keys = sorted({key for metric_dict in metric_dicts for key in metric_dict})
    return {
        key: float(np.mean([_safe_float(metric_dict.get(key, 0.0)) for metric_dict in metric_dicts]))
        for key in keys
    }


def _describe_maps(conf):
    if not isinstance(conf, dict):
        return "unknown"
    env_conf = conf.get("env_conf", conf)
    return env_conf.get("map", "unknown")


@dataclass
class EpisodeMetrics:
    speedup_reached: float = 0.0
    pre_speedup_steps: float = 0.0
    post_speedup_steps: float = 0.0
    pre_speedup_shaped_reward: float = 0.0
    post_speedup_shaped_reward: float = 0.0
    pre_speedup_step_score_gain: float = 0.0
    post_speedup_step_score_gain: float = 0.0
    pre_speedup_treasure_gain: float = 0.0
    post_speedup_treasure_gain: float = 0.0
    pre_speedup_total_score_gain: float = 0.0
    post_speedup_total_score_gain: float = 0.0
    pre_speedup_terminal_bonus: float = 0.0
    post_speedup_terminal_bonus: float = 0.0
    reward: float = 0.0
    total_score: float = 0.0
    step_score: float = 0.0
    treasure_score: float = 0.0
    treasures_collected: float = 0.0
    episode_steps: float = 0.0
    post_speedup_terminated: float = 0.0
    terminated_flag: float = 0.0
    completed_flag: float = 0.0
    abnormal_truncated_flag: float = 0.0
    danger_level: float = 0.0
    nearest_treasure_dist: float = -1.0
    _last_step_score: float = field(default=0.0, repr=False)
    _last_treasure_score: float = field(default=0.0, repr=False)
    _last_total_score: float = field(default=0.0, repr=False)

    def observe_step(self, env_obs, shaped_reward, step_idx):
        observation, frame_state, env_info = _extract_observation_parts(env_obs)
        if not self.speedup_reached and _safe_int(env_info.get("collected_buff", 0)) > 0:
            self.speedup_reached = 1.0

        phase = "post" if self.speedup_reached else "pre"
        setattr(self, f"{phase}_speedup_steps", getattr(self, f"{phase}_speedup_steps") + 1.0)
        setattr(
            self,
            f"{phase}_speedup_shaped_reward",
            getattr(self, f"{phase}_speedup_shaped_reward") + float(shaped_reward),
        )

        total_score, step_score, treasure_score, treasures_collected = _score_snapshot(
            frame_state,
            env_info,
        )
        setattr(
            self,
            f"{phase}_speedup_step_score_gain",
            getattr(self, f"{phase}_speedup_step_score_gain") + (step_score - self._last_step_score),
        )
        setattr(
            self,
            f"{phase}_speedup_treasure_gain",
            getattr(self, f"{phase}_speedup_treasure_gain") + (treasure_score - self._last_treasure_score),
        )
        setattr(
            self,
            f"{phase}_speedup_total_score_gain",
            getattr(self, f"{phase}_speedup_total_score_gain") + (total_score - self._last_total_score),
        )

        self._last_step_score = step_score
        self._last_treasure_score = treasure_score
        self._last_total_score = total_score

        self.total_score = total_score
        self.step_score = step_score
        self.treasure_score = treasure_score
        self.treasures_collected = float(treasures_collected)
        self.episode_steps = float(_safe_int(env_info.get("finished_steps", observation.get("step_no", step_idx))))

    def finalize(self, env_obs, final_bonus, terminated, truncated, step_idx):
        observation, frame_state, env_info = _extract_observation_parts(env_obs)
        phase = "post" if self.speedup_reached else "pre"
        setattr(
            self,
            f"{phase}_speedup_terminal_bonus",
            getattr(self, f"{phase}_speedup_terminal_bonus") + float(final_bonus),
        )

        total_score, step_score, treasure_score, treasures_collected = _score_snapshot(
            frame_state,
            env_info,
        )
        finished_steps = _safe_int(env_info.get("finished_steps", observation.get("step_no", step_idx)))
        finished_steps = finished_steps if finished_steps > 0 else step_idx
        max_step = max(1, _safe_int(env_info.get("max_step", finished_steps)))

        hero_pos = _extract_position(env_info.get("pos"))
        if hero_pos is None:
            hero_pos = _extract_position(_extract_hero(frame_state))

        self.total_score = total_score
        self.step_score = step_score
        self.treasure_score = treasure_score
        self.treasures_collected = float(treasures_collected)
        self.episode_steps = float(finished_steps)
        self.reward = (
            self.pre_speedup_shaped_reward
            + self.post_speedup_shaped_reward
            + self.pre_speedup_terminal_bonus
            + self.post_speedup_terminal_bonus
        )
        self.terminated_flag = 1.0 if terminated else 0.0
        self.completed_flag = 1.0 if (not terminated and finished_steps >= max_step) else 0.0
        self.abnormal_truncated_flag = 1.0 if (truncated and not terminated and finished_steps < max_step) else 0.0
        self.post_speedup_terminated = 1.0 if (terminated and self.speedup_reached) else 0.0
        self.danger_level = _danger_level(frame_state, hero_pos)
        self.nearest_treasure_dist = _nearest_treasure_distance(frame_state, hero_pos)

    def as_train_monitor_dict(self):
        return {
            "train_reward": self.reward,
            "train_total_score": self.total_score,
            "train_step_score": self.step_score,
            "train_treasure_score": self.treasure_score,
            "train_treasures_collected": self.treasures_collected,
            "train_episode_steps": self.episode_steps,
            "train_speedup_reached": self.speedup_reached,
            "train_pre_speedup_steps": self.pre_speedup_steps,
            "train_post_speedup_steps": self.post_speedup_steps,
            "train_pre_speedup_reward": self.pre_speedup_shaped_reward + self.pre_speedup_terminal_bonus,
            "train_post_speedup_reward": self.post_speedup_shaped_reward + self.post_speedup_terminal_bonus,
            "train_pre_speedup_shaped_reward": self.pre_speedup_shaped_reward,
            "train_post_speedup_shaped_reward": self.post_speedup_shaped_reward,
            "train_pre_speedup_step_score_gain": self.pre_speedup_step_score_gain,
            "train_post_speedup_step_score_gain": self.post_speedup_step_score_gain,
            "train_pre_speedup_treasure_gain": self.pre_speedup_treasure_gain,
            "train_post_speedup_treasure_gain": self.post_speedup_treasure_gain,
            "train_pre_speedup_total_score_gain": self.pre_speedup_total_score_gain,
        }

    def as_val_episode_dict(self):
        return {
            "reward": self.reward,
            "total_score": self.total_score,
            "step_score": self.step_score,
            "treasure_score": self.treasure_score,
            "treasures_collected": self.treasures_collected,
            "episode_steps": self.episode_steps,
            "speedup_reached": self.speedup_reached,
            "pre_speedup_steps": self.pre_speedup_steps,
            "post_speedup_steps": self.post_speedup_steps,
            "pre_speedup_reward": self.pre_speedup_shaped_reward + self.pre_speedup_terminal_bonus,
            "post_speedup_reward": self.post_speedup_shaped_reward + self.post_speedup_terminal_bonus,
            "pre_speedup_shaped_reward": self.pre_speedup_shaped_reward,
            "post_speedup_shaped_reward": self.post_speedup_shaped_reward,
            "pre_speedup_step_score_gain": self.pre_speedup_step_score_gain,
            "post_speedup_step_score_gain": self.post_speedup_step_score_gain,
            "pre_speedup_treasure_gain": self.pre_speedup_treasure_gain,
            "post_speedup_treasure_gain": self.post_speedup_treasure_gain,
            "pre_speedup_total_score_gain": self.pre_speedup_total_score_gain,
            "post_speedup_total_score_gain": self.post_speedup_total_score_gain,
            "pre_speedup_terminal_bonus": self.pre_speedup_terminal_bonus,
            "post_speedup_terminal_bonus": self.post_speedup_terminal_bonus,
            "post_speedup_terminated": self.post_speedup_terminated,
            "terminated_flag": self.terminated_flag,
            "completed_flag": self.completed_flag,
            "abnormal_truncated_flag": self.abnormal_truncated_flag,
            "danger_level": self.danger_level,
            "nearest_treasure_dist": self.nearest_treasure_dist,
        }


def workflow(envs, agents, logger=None, monitor=None, *args, **kwargs):
    last_save_model_time = time.time()
    env = envs[0]
    agent = agents[0]

    train_conf = read_usr_conf("agent_ppo/conf/train_env_conf.toml", logger)
    eval_conf = read_usr_conf("agent_ppo/conf/eval_env_conf.toml", logger)
    if train_conf is None:
        logger.error("train_conf is None, please check agent_ppo/conf/train_env_conf.toml")
        return

    episode_runner = EpisodeRunner(
        env=env,
        agent=agent,
        usr_conf=train_conf,
        logger=logger,
        monitor=monitor,
        train_conf=train_conf,
        eval_conf=eval_conf,
        eval_every_n=50,
        eval_episodes=10,
    )

    while True:
        for g_data in episode_runner.run_episodes():
            agent.send_sample_data(g_data)
            g_data.clear()

            now = time.time()
            if now - last_save_model_time >= 1800:
                agent.save_model()
                last_save_model_time = now


class EpisodeRunner:
    def __init__(
        self,
        env,
        agent,
        usr_conf,
        logger,
        monitor,
        train_conf=None,
        eval_conf=None,
        eval_every_n=50,
        eval_episodes=10,
    ):
        self.env = env
        self.agent = agent
        self.usr_conf = usr_conf
        self.logger = logger
        self.monitor = monitor
        self.episode_cnt = 0
        self.last_get_training_metrics_time = 0

        self.train_conf = train_conf or usr_conf
        self.eval_conf = eval_conf
        self.eval_every_n = eval_every_n
        self.eval_episodes = eval_episodes
        self.is_eval_mode = False
        self.eval_episode_cnt = 0
        self.train_episode_since_last_eval = 0
        self.eval_episode_metrics = []

    def run_episodes(self):
        while True:
            if not self.is_eval_mode and self.eval_conf is not None:
                if self.train_episode_since_last_eval >= self.eval_every_n:
                    self.is_eval_mode = True
                    self.eval_episode_cnt = 0
                    self.eval_episode_metrics = []
                    self.logger.info(
                        f"[EVAL] Switching to eval mode on maps {_describe_maps(self.eval_conf)}"
                    )

            if self.is_eval_mode and self.eval_episode_cnt >= self.eval_episodes:
                self.is_eval_mode = False
                self.train_episode_since_last_eval = 0
                self.logger.info(
                    f"[EVAL] Eval completed. Back to training on maps {_describe_maps(self.train_conf)}"
                )

            current_conf = self.eval_conf if self.is_eval_mode else self.train_conf

            now = time.time()
            if now - self.last_get_training_metrics_time >= 60:
                training_metrics = get_training_metrics()
                self.last_get_training_metrics_time = now
                if training_metrics is not None:
                    self.logger.info(f"training_metrics is {training_metrics}")

            env_obs = self.env.reset(current_conf)
            if handle_disaster_recovery(env_obs, self.logger):
                continue

            self.agent.reset(env_obs)
            self.agent.load_model(id="latest")

            obs_data, remain_info = self.agent.observation_process(env_obs)

            collector = []
            episode_metrics = EpisodeMetrics()
            self.episode_cnt += 1
            done = False
            step = 0
            total_reward = 0.0

            mode_str = "EVAL" if self.is_eval_mode else "TRAIN"
            self.logger.info(f"[{mode_str}] Episode {self.episode_cnt} start")

            while not done:
                act_data = self.agent.predict(list_obs_data=[obs_data])[0]
                act = self.agent.action_process(act_data, is_stochastic=not self.is_eval_mode)

                env_reward, env_obs = self.env.step(act)
                if handle_disaster_recovery(env_obs, self.logger):
                    break

                terminated = env_obs["terminated"]
                truncated = env_obs["truncated"]
                step += 1
                done = terminated or truncated

                _obs_data, _remain_info = self.agent.observation_process(env_obs)
                reward = np.array(_remain_info.get("reward", [0.0]), dtype=np.float32)
                total_reward += float(reward[0])
                episode_metrics.observe_step(env_obs, float(reward[0]), step)

                final_reward = np.zeros(1, dtype=np.float32)
                if done:
                    _, _, env_info = _extract_observation_parts(env_obs)
                    total_score = _safe_float(env_info.get("total_score", 0.0))
                    treasures_collected = _safe_int(env_info.get("treasures_collected", 0))
                    flash_count = _safe_int(env_info.get("flash_count", 0))
                    finished_steps = _safe_int(env_info.get("finished_steps", step))
                    max_step = max(1, _safe_int(env_info.get("max_step", step)))

                    if terminated:
                        final_reward[0] = Config.TERMINATED_PENALTY
                        result_str = "FAIL"
                    elif finished_steps >= max_step:
                        final_reward[0] = Config.TRUNCATED_BONUS
                        result_str = "SURVIVE"
                    else:
                        result_str = "STOP"

                    self.logger.info(
                        f"[GAMEOVER][{mode_str}] episode:{self.episode_cnt} steps:{step} "
                        f"result:{result_str} sim_score:{total_score:.1f} "
                        f"treasures:{treasures_collected} flash:{flash_count} "
                        f"total_reward:{total_reward:.3f}"
                    )

                frame = SampleData(
                    obs=np.array(obs_data.feature, dtype=np.float32),
                    legal_action=np.array(obs_data.legal_action, dtype=np.float32),
                    act=np.array([act_data.action[0]], dtype=np.float32),
                    reward=reward,
                    done=np.array([float(done)], dtype=np.float32),
                    reward_sum=np.zeros(1, dtype=np.float32),
                    value=np.array(act_data.value, dtype=np.float32).flatten()[:1],
                    next_value=np.zeros(1, dtype=np.float32),
                    advantage=np.zeros(1, dtype=np.float32),
                    prob=np.array(act_data.prob, dtype=np.float32),
                )
                collector.append(frame)

                if done:
                    if collector:
                        collector[-1].reward = collector[-1].reward + final_reward

                    episode_metrics.finalize(
                        env_obs=env_obs,
                        final_bonus=float(final_reward[0]),
                        terminated=terminated,
                        truncated=truncated,
                        step_idx=step,
                    )

                    if self.is_eval_mode:
                        self.eval_episode_cnt += 1
                        self.eval_episode_metrics.append(episode_metrics.as_val_episode_dict())
                        if self.eval_episode_cnt >= self.eval_episodes and self.monitor:
                            self.monitor.put_data(
                                {
                                    os.getpid(): _round_metric_dict(
                                        self._build_val_monitor_data(self.eval_episode_metrics)
                                    )
                                }
                            )
                    else:
                        self.train_episode_since_last_eval += 1
                        if self.monitor:
                            self.monitor.put_data(
                                {os.getpid(): _round_metric_dict(episode_metrics.as_train_monitor_dict())}
                            )

                    if not self.is_eval_mode and collector:
                        collector = sample_process(collector)
                        yield collector
                    break

                obs_data = _obs_data
                remain_info = _remain_info

    def _build_val_monitor_data(self, val_episode_metrics):
        mean_metrics = _mean_metric_dict(val_episode_metrics)
        return {
            "val_reward": mean_metrics.get("reward", 0.0),
            "val_total_score": mean_metrics.get("total_score", 0.0),
            "val_step_score": mean_metrics.get("step_score", 0.0),
            "val_treasure_score": mean_metrics.get("treasure_score", 0.0),
            "val_treasures_collected": mean_metrics.get("treasures_collected", 0.0),
            "val_episode_steps": mean_metrics.get("episode_steps", 0.0),
            "val_speedup_reached": mean_metrics.get("speedup_reached", 0.0),
            "val_pre_speedup_steps": mean_metrics.get("pre_speedup_steps", 0.0),
            "val_post_speedup_steps": mean_metrics.get("post_speedup_steps", 0.0),
            "val_pre_speedup_reward": mean_metrics.get("pre_speedup_reward", 0.0),
            "val_post_speedup_reward": mean_metrics.get("post_speedup_reward", 0.0),
            "val_pre_speedup_shaped_reward": mean_metrics.get("pre_speedup_shaped_reward", 0.0),
            "val_post_speedup_shaped_reward": mean_metrics.get("post_speedup_shaped_reward", 0.0),
            "val_pre_speedup_step_score_gain": mean_metrics.get("pre_speedup_step_score_gain", 0.0),
            "val_post_speedup_step_score_gain": mean_metrics.get("post_speedup_step_score_gain", 0.0),
            "val_pre_speedup_treasure_gain": mean_metrics.get("pre_speedup_treasure_gain", 0.0),
            "val_post_speedup_treasure_gain": mean_metrics.get("post_speedup_treasure_gain", 0.0),
            "val_pre_speedup_total_score_gain": mean_metrics.get("pre_speedup_total_score_gain", 0.0),
            "val_post_speedup_total_score_gain": mean_metrics.get("post_speedup_total_score_gain", 0.0),
            "val_pre_speedup_terminal_bonus": mean_metrics.get("pre_speedup_terminal_bonus", 0.0),
            "val_post_speedup_terminal_bonus": mean_metrics.get("post_speedup_terminal_bonus", 0.0),
            "val_post_speedup_terminated": mean_metrics.get("post_speedup_terminated", 0.0),
            "val_terminated_rate": mean_metrics.get("terminated_flag", 0.0),
            "val_completed_rate": mean_metrics.get("completed_flag", 0.0),
            "val_abnormal_truncated_rate": mean_metrics.get("abnormal_truncated_flag", 0.0),
            "val_danger_level": mean_metrics.get("danger_level", 0.0),
            "val_nearest_treasure_dist": mean_metrics.get("nearest_treasure_dist", -1.0),
        }
