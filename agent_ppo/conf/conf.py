#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
###########################################################################
# Copyright © 1998 - 2026 Tencent. All Rights Reserved.
###########################################################################
"""
Author: Tencent AI Arena Authors

Configuration for Gorge Chase PPO.
峡谷追猎 PPO 配置。
"""


class Config:

    # Feature dimensions / 特征维度（共528维）
    FEATURES = [
        6,
        8,
        8,
        484,
        16,
        6,
    ]
    FEATURE_SPLIT_SHAPE = FEATURES
    FEATURE_LEN = sum(FEATURE_SPLIT_SHAPE)
    DIM_OF_OBSERVATION = FEATURE_LEN

    # Action space / 动作空间：16 个离散动作（8 移动 + 8 闪现）
    ACTION_NUM = 16

    # Value head / 价值头：单头价值估计
    VALUE_NUM = 1

    # PPO hyperparameters / PPO 超参数
    GAMMA = 0.995
    LAMDA = 0.95
    INIT_LEARNING_RATE_START = 0.0002
    BETA_START = 0.003
    BETA_END = 0.0005
    BETA_DECAY_STEPS = 4000
    CLIP_PARAM = 0.15
    VF_COEF = 1.0
    GRAD_CLIP_RANGE = 0.5
    USE_ADVANTAGE_NORM = True
    ADVANTAGE_NORM_EPS = 1e-8
    TARGET_KL = 0.015

    # Reward shaping / 奖励设计
    SURVIVE_REWARD = 0.005
    DIST_SHAPING_COEF = 0.05
    TREASURE_REWARD = 1.0
    BUFF_REWARD = 0.3
    TREASURE_DIST_COEF = 0.08
    EXIT_DIST_COEF = 0.04
    FLASH_ESCAPE_REWARD_COEF = 0.05
    HIT_WALL_PENALTY = 0.05
    REVISIT_PENALTY_COEF = 0.02
    REVISIT_WINDOW_SIZE = 3
    TERMINATED_PENALTY = -12.0
    TRUNCATED_BONUS = 8.0

    # Lightweight exploration bonus / 轻量探索奖励
    ENABLE_EXPLORE_BONUS = True
    EXPLORE_BONUS_SCALE = 0.01
    EXPLORE_BONUS_GRID_SIZE = 16
    EXPLORE_BONUS_MIN_RATIO = 0.25

    # Semantic map / 局部语义地图
    LOCAL_MAP_SIZE = 11
    LOCAL_MAP_CHANNEL = 4

    # Structured observation encoder / 结构化观测编码
    HERO_ENCODER_DIM = 32
    MONSTER_ENCODER_DIM = 64
    MAP_ENCODER_DIM = 128
    CONTROL_ENCODER_DIM = 32
    FUSION_HIDDEN_DIM = 128
