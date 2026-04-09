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

    # Feature dimensions / 特征维度（共40维）
    FEATURES = [
        4,
        5,
        5,
        16,
        8,
        2,
    ]
    FEATURE_SPLIT_SHAPE = FEATURES
    FEATURE_LEN = sum(FEATURE_SPLIT_SHAPE)
    DIM_OF_OBSERVATION = FEATURE_LEN

    # Action space / 动作空间：8个移动方向
    ACTION_NUM = 8

    # Value head / 价值头：单头生存奖励
    VALUE_NUM = 1

    # PPO hyperparameters / PPO 超参数
    GAMMA = 0.99
    LAMDA = 0.95
    INIT_LEARNING_RATE_START = 0.0003
    BETA_START = 0.001
    BETA_END = 0.0002
    BETA_DECAY_STEPS = 2000
    CLIP_PARAM = 0.2
    VF_COEF = 1.0
    GRAD_CLIP_RANGE = 0.5
    USE_ADVANTAGE_NORM = True
    ADVANTAGE_NORM_EPS = 1e-8
    TARGET_KL = 0.02

    # Reward shaping / 奖励设计
    SURVIVE_REWARD = 0.01
    DIST_SHAPING_COEF = 0.1

    # Lightweight exploration bonus / 轻量探索奖励
    ENABLE_EXPLORE_BONUS = True
    EXPLORE_BONUS_SCALE = 0.02
    EXPLORE_BONUS_GRID_SIZE = 16
    EXPLORE_BONUS_MIN_RATIO = 0.25

    # Structured observation encoder / 结构化观测编码
    HERO_ENCODER_DIM = 16
    MONSTER_ENCODER_DIM = 32
    MAP_ENCODER_DIM = 32
    CONTROL_ENCODER_DIM = 16
    FUSION_HIDDEN_DIM = 64
