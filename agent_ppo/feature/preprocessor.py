#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
###########################################################################
# Copyright © 1998 - 2026 Tencent. All Rights Reserved.
###########################################################################
"""
Author: Tencent AI Arena Authors

Feature preprocessor and reward design for Gorge Chase PPO.
峡谷追猎 PPO 特征预处理与奖励设计。
"""

import math
from dataclasses import dataclass, field

import numpy as np

from agent_ppo.conf.conf import Config

# Map size / 地图尺寸（128×128）
MAP_SIZE = 128.0
MAP_DIAGONAL = math.sqrt(2.0) * MAP_SIZE
MAX_MONSTER_SPEED = 5.0
MAX_DIST_BUCKET = 5.0
MAX_FLASH_CD = 2000.0
MAX_BUFF_DURATION = 50.0
LOCAL_HALF = Config.LOCAL_MAP_SIZE // 2
TARGET_DIST_SCALE = 16.0

DIST_BUCKET_TO_DISTANCE = {
    0: 15.0,
    1: 45.0,
    2: 75.0,
    3: 105.0,
    4: 135.0,
    5: 165.0,
}

DIRECTION_TO_VECTOR = {
    0: (0.0, 0.0),
    1: (1.0, 0.0),
    2: (math.sqrt(0.5), math.sqrt(0.5)),
    3: (0.0, 1.0),
    4: (-math.sqrt(0.5), math.sqrt(0.5)),
    5: (-1.0, 0.0),
    6: (-math.sqrt(0.5), -math.sqrt(0.5)),
    7: (0.0, -1.0),
    8: (math.sqrt(0.5), -math.sqrt(0.5)),
}


def _norm(v, v_max, v_min=0.0):
    """Normalize value to [0, 1]."""

    v = float(np.clip(v, v_min, v_max))
    return (v - v_min) / (v_max - v_min) if (v_max - v_min) > 1e-6 else 0.0


def _clip_position(pos):
    clipped = np.clip(np.asarray(pos, dtype=np.float32), 0.0, MAP_SIZE - 1.0)
    return clipped.astype(np.float32)


def _is_valid_position(pos):
    return pos is not None and float(pos[0]) >= 0.0 and float(pos[1]) >= 0.0


def _get_nested(data, keys, default=None):
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def _distance_from_bucket(dist_bucket):
    return DIST_BUCKET_TO_DISTANCE.get(int(dist_bucket), DIST_BUCKET_TO_DISTANCE[int(MAX_DIST_BUCKET)])


def _direction_to_sin_cos(direction):
    dx, dz = DIRECTION_TO_VECTOR.get(int(direction), (0.0, 0.0))
    return float(dz), float(dx)


def _estimate_position_from_relative(hero_pos, direction, dist_bucket):
    dx, dz = DIRECTION_TO_VECTOR.get(int(direction), (0.0, 0.0))
    distance = _distance_from_bucket(dist_bucket)
    return _clip_position(hero_pos + np.array([dx * distance, dz * distance], dtype=np.float32))


@dataclass
class TargetMemory:
    config_id: int
    sub_type: int
    pos: np.ndarray = field(default_factory=lambda: np.array([-1.0, -1.0], dtype=np.float32))
    found: bool = False
    available: bool = True
    direction: int = 0
    distance_bucket: int = int(MAX_DIST_BUCKET)
    last_distance: float = MAP_DIAGONAL
    distance: float = MAP_DIAGONAL


class Preprocessor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.step_no = 0
        self.max_step = 1000
        self.last_min_monster_distance = MAP_DIAGONAL * 0.5
        self.visit_counts = {}
        self.last_grid = None
        self.last_hero_pos = None
        self.blocked_move_actions = set()
        self.visit_heat = np.zeros((int(MAP_SIZE), int(MAP_SIZE)), dtype=np.float32)
        self.treasure_memory = {}
        self.buff_memory = {}
        self.last_treasure_count = 0
        self.last_buff_count = 0
        self.last_flash_count = 0
        self.last_target_treasure_distance = None
        self.last_target_buff_distance = None

    def feature_process(self, env_obs, last_action):
        """Process env_obs into feature vector, legal_action mask, reward and stats."""

        observation = env_obs.get("observation", env_obs)
        frame_state = observation.get("frame_state", {})
        env_info = observation.get("env_info", {})
        hero = self._extract_hero(frame_state)
        hero_pos = self._extract_position(hero)
        if hero_pos is None:
            hero_pos = np.array([0.0, 0.0], dtype=np.float32)

        self.step_no = int(observation.get("step_no", env_info.get("step_no", 0)))
        self.max_step = max(1, int(env_info.get("max_step", self.max_step)))

        hit_wall = self._update_movement_state(hero_pos, last_action)
        self._register_visit(hero_pos)

        legal_action = self._build_legal_action_mask(
            observation.get("legal_act", observation.get("legal_action")),
        )
        monsters, min_monster_distance = self._build_monster_features(frame_state.get("monsters", []), hero_pos)
        treasure_target, buff_target = self._sync_collectible_memory(frame_state.get("organs", []), env_info, hero_pos)
        semantic_map = self._build_semantic_map(
            map_info=observation.get("map_info"),
            hero_pos=hero_pos,
            monsters=monsters,
        )

        treasure_total = max(1, int(env_info.get("total_treasure", 10)))
        buff_total = max(1, int(env_info.get("total_buff", 2)))
        treasure_count = int(
            env_info.get(
                "treasures_collected",
                hero.get("treasure_collected_count", 0),
            )
        )
        buff_count = int(env_info.get("collected_buff", 0))
        flash_count = int(env_info.get("flash_count", 0))
        flash_config_cd = max(1, int(env_info.get("flash_cooldown", 100)))

        step_norm = _norm(self.step_no, self.max_step)
        treasure_collected_ratio = treasure_count / float(treasure_total)
        buff_collected_ratio = buff_count / float(buff_total)
        remaining_treasure_ratio = max(0.0, 1.0 - treasure_collected_ratio)
        flash_opportunity = max(1.0, self.step_no / float(flash_config_cd) + 1.0)
        flash_used_ratio = float(np.clip(flash_count / flash_opportunity, 0.0, 1.0))

        hero_feat = np.array(
            [
                _norm(hero_pos[0], MAP_SIZE - 1.0),
                _norm(hero_pos[1], MAP_SIZE - 1.0),
                _norm(self._extract_flash_cooldown(hero), MAX_FLASH_CD),
                _norm(self._extract_buff_remaining(hero), MAX_BUFF_DURATION),
                treasure_collected_ratio,
                step_norm,
            ],
            dtype=np.float32,
        )

        progress_feat = np.array(
            [
                step_norm,
                step_norm,
                remaining_treasure_ratio,
                buff_collected_ratio,
                flash_used_ratio,
                float(treasure_target is not None or buff_target is not None),
            ],
            dtype=np.float32,
        )

        feature = np.concatenate(
            [
                hero_feat,
                monsters[0]["feature"],
                monsters[1]["feature"],
                semantic_map.reshape(-1),
                np.asarray(legal_action, dtype=np.float32),
                progress_feat,
            ]
        ).astype(np.float32)

        reward, reward_terms = self._build_reward(
            hero_pos=hero_pos,
            min_monster_distance=min_monster_distance,
            treasure_target=treasure_target,
            buff_target=buff_target,
            treasure_count=treasure_count,
            buff_count=buff_count,
            flash_count=flash_count,
            last_action=last_action,
            hit_wall=hit_wall,
        )

        self.last_min_monster_distance = min_monster_distance
        self.last_target_treasure_distance = treasure_target.distance if treasure_target is not None else None
        self.last_target_buff_distance = buff_target.distance if buff_target is not None else None
        self.last_treasure_count = treasure_count
        self.last_buff_count = buff_count
        self.last_flash_count = flash_count
        self.last_hero_pos = hero_pos

        return feature, legal_action, [reward], {"reward_terms": reward_terms}

    def _extract_hero(self, frame_state):
        hero = frame_state.get("heroes", {})
        if isinstance(hero, list):
            return hero[0] if hero else {}
        return hero

    def _extract_position(self, obj):
        pos = None
        if isinstance(obj, dict):
            if "pos" in obj and isinstance(obj["pos"], dict):
                pos = obj["pos"]
            elif "x" in obj and "z" in obj:
                pos = obj
        if not isinstance(pos, dict) or "x" not in pos or "z" not in pos:
            return None
        return _clip_position([pos["x"], pos["z"]])

    def _extract_flash_cooldown(self, hero):
        return float(
            hero.get(
                "flash_cooldown",
                _get_nested(hero, ["talent", "cooldown"], 0.0),
            )
        )

    def _extract_buff_remaining(self, hero):
        return float(
            hero.get(
                "buff_remaining_time",
                hero.get("buff_remain_time", hero.get("buff_remain", 0.0)),
            )
        )

    def _extract_relative_direction(self, obj):
        return int(
            obj.get(
                "hero_relative_direction",
                _get_nested(obj, ["relative_pos", "direction"], 0),
            )
        )

    def _extract_relative_distance_bucket(self, obj):
        return int(
            obj.get(
                "hero_l2_distance",
                _get_nested(obj, ["relative_pos", "l2_distance"], int(MAX_DIST_BUCKET)),
            )
        )

    def _update_movement_state(self, hero_pos, last_action):
        if self.last_hero_pos is None or last_action == -1:
            self.blocked_move_actions.clear()
            return False

        moved_distance = float(np.linalg.norm(hero_pos - self.last_hero_pos))
        hit_wall = moved_distance < 0.5
        if hit_wall:
            self.blocked_move_actions.add(int(last_action) % 8)
        else:
            self.blocked_move_actions.clear()
        return hit_wall

    def _register_visit(self, hero_pos):
        x = int(np.clip(round(hero_pos[0]), 0, MAP_SIZE - 1))
        z = int(np.clip(round(hero_pos[1]), 0, MAP_SIZE - 1))
        self.visit_heat[x, z] += 1.0

    def _build_legal_action_mask(self, legal_act_raw):
        legal_action = [1] * Config.ACTION_NUM

        if isinstance(legal_act_raw, (list, tuple, np.ndarray)) and len(legal_act_raw) > 0:
            first = legal_act_raw[0]
            if isinstance(first, (bool, np.bool_)):
                legal_action = [int(bool(v)) for v in legal_act_raw[: Config.ACTION_NUM]]
                if len(legal_action) < Config.ACTION_NUM:
                    legal_action.extend([1] * (Config.ACTION_NUM - len(legal_action)))
            else:
                valid_set = {int(a) for a in legal_act_raw if 0 <= int(a) < Config.ACTION_NUM}
                legal_action = [1 if idx in valid_set else 0 for idx in range(Config.ACTION_NUM)]

        for blocked_action in self.blocked_move_actions:
            if 0 <= blocked_action < 8:
                legal_action[blocked_action] = 0

        if sum(legal_action) == 0:
            legal_action = [1] * Config.ACTION_NUM

        return legal_action

    def _build_monster_features(self, monsters, hero_pos):
        monster_infos = []
        for idx in range(2):
            if idx >= len(monsters):
                monster_infos.append(
                    {
                        "feature": np.zeros(8, dtype=np.float32),
                        "distance": MAP_DIAGONAL,
                        "pos": None,
                    }
                )
                continue

            monster = monsters[idx]
            pos = self._extract_position(monster)
            direction = self._extract_relative_direction(monster)
            dist_bucket = self._extract_relative_distance_bucket(monster)
            active_flag = 1.0

            if pos is not None:
                is_visible = float(monster.get("is_in_view", 1.0))
                est_pos = pos
                distance = float(np.linalg.norm(est_pos - hero_pos))
            else:
                is_visible = float(monster.get("is_in_view", 0.0))
                est_pos = _estimate_position_from_relative(hero_pos, direction, dist_bucket)
                distance = _distance_from_bucket(dist_bucket)

            dir_sin, dir_cos = _direction_to_sin_cos(direction)
            feature = np.array(
                [
                    is_visible,
                    _norm(est_pos[0], MAP_SIZE - 1.0),
                    _norm(est_pos[1], MAP_SIZE - 1.0),
                    _norm(monster.get("speed", 1), MAX_MONSTER_SPEED),
                    _norm(dist_bucket, MAX_DIST_BUCKET),
                    dir_sin,
                    dir_cos,
                    active_flag,
                ],
                dtype=np.float32,
            )
            monster_infos.append({"feature": feature, "distance": distance, "pos": est_pos})

        min_distance = min(info["distance"] for info in monster_infos if info["pos"] is not None)
        return monster_infos, float(min_distance)

    def _sync_collectible_memory(self, organs, env_info, hero_pos):
        remaining_treasures = {
            int(treasure_id)
            for treasure_id in (env_info.get("treasure_id", []) or [])
        }

        for organ in organs or []:
            sub_type = int(organ.get("sub_type", 0))
            if sub_type not in (1, 2):
                continue

            config_id = int(organ.get("config_id", 0))
            memory_bank = self.treasure_memory if sub_type == 1 else self.buff_memory
            target = memory_bank.get(config_id)
            if target is None:
                target = TargetMemory(config_id=config_id, sub_type=sub_type)
                memory_bank[config_id] = target

            status = int(organ.get("status", 1))
            target.direction = self._extract_relative_direction(organ)
            target.distance_bucket = self._extract_relative_distance_bucket(organ)

            available = status != 0
            if sub_type == 1 and remaining_treasures:
                available = config_id in remaining_treasures
            target.available = available

            pos = self._extract_position(organ)
            if pos is not None and status != -1:
                target.pos = pos
                target.found = True
            elif not target.found and target.direction > 0:
                target.pos = _estimate_position_from_relative(hero_pos, target.direction, target.distance_bucket)

            target.last_distance = target.distance
            if _is_valid_position(target.pos):
                target.distance = float(np.linalg.norm(target.pos - hero_pos))
            else:
                target.distance = _distance_from_bucket(target.distance_bucket)

        if remaining_treasures:
            for config_id, target in self.treasure_memory.items():
                target.available = config_id in remaining_treasures

        treasure_target = self._pick_nearest_available(self.treasure_memory)
        buff_target = self._pick_nearest_available(self.buff_memory)
        return treasure_target, buff_target

    def _pick_nearest_available(self, memory_bank):
        candidates = [
            target
            for target in memory_bank.values()
            if target.available and _is_valid_position(target.pos)
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda target: target.distance)

    def _build_semantic_map(self, map_info, hero_pos, monsters):
        semantic_map = np.zeros(
            (Config.LOCAL_MAP_CHANNEL, Config.LOCAL_MAP_SIZE, Config.LOCAL_MAP_SIZE),
            dtype=np.float32,
        )
        semantic_map[0] = self._build_obstacle_channel(map_info)
        semantic_map[1] = self._build_visit_channel(hero_pos)
        semantic_map[2] = self._build_collectible_channel(hero_pos)
        semantic_map[3] = self._build_risk_channel(hero_pos, monsters)
        return semantic_map

    def _to_map_array(self, map_info):
        if map_info is None:
            return None
        if isinstance(map_info, np.ndarray):
            return map_info.astype(np.float32)
        if isinstance(map_info, list) and len(map_info) > 0 and isinstance(map_info[0], dict):
            return np.asarray([line.get("values", []) for line in map_info], dtype=np.float32)
        return np.asarray(map_info, dtype=np.float32)

    def _build_obstacle_channel(self, map_info):
        patch = np.zeros((Config.LOCAL_MAP_SIZE, Config.LOCAL_MAP_SIZE), dtype=np.float32)
        map_array = self._to_map_array(map_info)
        if map_array is None or map_array.ndim != 2:
            return patch

        center = map_array.shape[0] // 2
        for row in range(Config.LOCAL_MAP_SIZE):
            for col in range(Config.LOCAL_MAP_SIZE):
                src_row = center - LOCAL_HALF + row
                src_col = center - LOCAL_HALF + col
                if 0 <= src_row < map_array.shape[0] and 0 <= src_col < map_array.shape[1]:
                    patch[row, col] = float(map_array[src_row, src_col] > 0)
        return patch

    def _build_visit_channel(self, hero_pos):
        channel = np.zeros((Config.LOCAL_MAP_SIZE, Config.LOCAL_MAP_SIZE), dtype=np.float32)
        hero_x = int(round(hero_pos[0]))
        hero_z = int(round(hero_pos[1]))
        for row in range(Config.LOCAL_MAP_SIZE):
            for col in range(Config.LOCAL_MAP_SIZE):
                dx = col - LOCAL_HALF
                dz = LOCAL_HALF - row
                x = hero_x + dx
                z = hero_z + dz
                if 0 <= x < MAP_SIZE and 0 <= z < MAP_SIZE:
                    channel[row, col] = min(self.visit_heat[x, z] / 5.0, 1.0)
        return channel

    def _build_collectible_channel(self, hero_pos):
        channel = np.zeros((Config.LOCAL_MAP_SIZE, Config.LOCAL_MAP_SIZE), dtype=np.float32)

        for target in self.treasure_memory.values():
            if target.available and _is_valid_position(target.pos):
                row, col = self._project_to_local(hero_pos, target.pos)
                self._mark_channel(channel, row, col, 1.0 if target.found else 0.5)

        for target in self.buff_memory.values():
            if target.available and _is_valid_position(target.pos):
                row, col = self._project_to_local(hero_pos, target.pos)
                self._mark_channel(channel, row, col, -1.0 if target.found else -0.5)

        return channel

    def _build_risk_channel(self, hero_pos, monsters):
        channel = np.zeros((Config.LOCAL_MAP_SIZE, Config.LOCAL_MAP_SIZE), dtype=np.float32)
        for monster in monsters:
            if monster["pos"] is None:
                continue
            row, col = self._project_to_local(hero_pos, monster["pos"])
            strength = max(0.2, 1.0 - monster["distance"] / (MAP_DIAGONAL * 0.35))
            self._paint_blob(channel, row, col, strength)
        return np.clip(channel, 0.0, 1.0)

    def _project_to_local(self, hero_pos, target_pos):
        delta = np.asarray(target_pos, dtype=np.float32) - np.asarray(hero_pos, dtype=np.float32)
        dx, dz = float(delta[0]), float(delta[1])
        max_abs = max(abs(dx), abs(dz), 1.0)
        if max_abs > LOCAL_HALF:
            scale = LOCAL_HALF / max_abs
            dx *= scale
            dz *= scale

        row = int(np.clip(round(LOCAL_HALF - dz), 0, Config.LOCAL_MAP_SIZE - 1))
        col = int(np.clip(round(LOCAL_HALF + dx), 0, Config.LOCAL_MAP_SIZE - 1))
        return row, col

    def _mark_channel(self, channel, row, col, value):
        if abs(value) >= abs(channel[row, col]):
            channel[row, col] = value

    def _paint_blob(self, channel, row, col, value):
        for d_row in range(-1, 2):
            for d_col in range(-1, 2):
                rr = row + d_row
                cc = col + d_col
                if 0 <= rr < Config.LOCAL_MAP_SIZE and 0 <= cc < Config.LOCAL_MAP_SIZE:
                    distance = abs(d_row) + abs(d_col)
                    decay = 1.0 if distance == 0 else 0.5 if distance == 1 else 0.25
                    channel[rr, cc] = max(channel[rr, cc], value * decay)

    def _build_reward(
        self,
        hero_pos,
        min_monster_distance,
        treasure_target,
        buff_target,
        treasure_count,
        buff_count,
        flash_count,
        last_action,
        hit_wall,
    ):
        survive_reward = Config.SURVIVE_REWARD
        dist_shaping = Config.DIST_SHAPING_COEF * self._away_reward(
            self.last_min_monster_distance,
            min_monster_distance,
        )

        treasure_dist_reward = 0.0
        if treasure_target is not None and self.last_target_treasure_distance is not None:
            treasure_dist_reward = Config.TREASURE_DIST_COEF * self._towards_reward(
                self.last_target_treasure_distance,
                treasure_target.distance,
            )

        guide_dist_reward = 0.0
        if treasure_target is None and buff_target is not None and self.last_target_buff_distance is not None:
            guide_dist_reward = Config.EXIT_DIST_COEF * self._towards_reward(
                self.last_target_buff_distance,
                buff_target.distance,
            )

        treasure_reward = max(0, treasure_count - self.last_treasure_count) * Config.TREASURE_REWARD
        buff_reward = max(0, buff_count - self.last_buff_count) * Config.BUFF_REWARD

        flash_escape_reward = 0.0
        if last_action >= 8 and self.last_min_monster_distance < 45.0:
            flash_escape_reward = Config.FLASH_ESCAPE_REWARD_COEF * max(
                self._away_reward(self.last_min_monster_distance, min_monster_distance),
                0.0,
            )

        hit_wall_penalty = -Config.HIT_WALL_PENALTY if hit_wall else 0.0
        revisit_penalty = -Config.REVISIT_PENALTY_COEF * self._revisit_intensity(hero_pos)
        explore_bonus = self._explore_bonus(hero_pos)

        reward_terms = {
            "survive_reward": survive_reward,
            "dist_shaping": dist_shaping,
            "treasure_dist_reward": treasure_dist_reward,
            "guide_dist_reward": guide_dist_reward,
            "treasure_reward": treasure_reward,
            "buff_reward": buff_reward,
            "flash_escape_reward": flash_escape_reward,
            "hit_wall_penalty": hit_wall_penalty,
            "revisit_penalty": revisit_penalty,
            "explore_bonus": explore_bonus,
        }
        reward = float(sum(reward_terms.values()))
        return reward, reward_terms

    def _towards_reward(self, last_distance, current_distance):
        return float(np.clip((last_distance - current_distance) / TARGET_DIST_SCALE, -1.0, 1.0))

    def _away_reward(self, last_distance, current_distance):
        return float(np.clip((current_distance - last_distance) / TARGET_DIST_SCALE, -1.0, 1.0))

    def _revisit_intensity(self, hero_pos):
        hero_x = int(np.clip(round(hero_pos[0]), 0, MAP_SIZE - 1))
        hero_z = int(np.clip(round(hero_pos[1]), 0, MAP_SIZE - 1))
        half = Config.REVISIT_WINDOW_SIZE // 2

        values = []
        for dx in range(-half, half + 1):
            for dz in range(-half, half + 1):
                x = hero_x + dx
                z = hero_z + dz
                if 0 <= x < MAP_SIZE and 0 <= z < MAP_SIZE:
                    values.append(self.visit_heat[x, z])

        if not values:
            return 0.0

        revisit_mean = float(np.mean(values))
        return float(np.clip((revisit_mean - 1.0) / 2.0, 0.0, 1.0))

    def _explore_bonus(self, hero_pos):
        if not Config.ENABLE_EXPLORE_BONUS:
            return 0.0

        grid = self._grid_cell(hero_pos)
        if grid == self.last_grid:
            return 0.0

        visit_count = self.visit_counts.get(grid, 0) + 1
        self.visit_counts[grid] = visit_count
        self.last_grid = grid

        novelty_ratio = 1.0 / math.sqrt(float(visit_count))
        if novelty_ratio < Config.EXPLORE_BONUS_MIN_RATIO:
            return 0.0

        return Config.EXPLORE_BONUS_SCALE * novelty_ratio

    def _grid_cell(self, hero_pos):
        grid_size = max(1, int(Config.EXPLORE_BONUS_GRID_SIZE))
        bucket_size = MAP_SIZE / grid_size
        x_idx = min(grid_size - 1, max(0, int(hero_pos[0] / bucket_size)))
        z_idx = min(grid_size - 1, max(0, int(hero_pos[1] / bucket_size)))
        return x_idx, z_idx
