#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
###########################################################################
# Copyright © 1998 - 2025 Tencent. All Rights Reserved.
###########################################################################
"""
Author: Tencent AI Arena Authors
"""

import numpy as np


# Configuration, including dimension settings, algorithm parameter settings.
# The last few configurations in the file are for the Kaiwu platform to use and should not be changed.
# 配置，包含维度设置，算法参数设置，文件的最后一些配置是开悟平台使用不要改动
class Config:

    # features
    # 特征
    HERO_FEATURE = [
        2,  # 当前英雄位置
        1,  # 闪现是否可用
        1,  # 闪现cd
        1,  # 加速buff是否存在
        1,  # 走过步数
    ]
    HERO_FEATURE_DIM = sum(HERO_FEATURE)
    MAP_FEATURE_SHAPE = (4, 51, 51)
    # MAP_FEATURE_SHAPE = (5, 128, 128)
    MAP_FEATURE_DIM = int(np.prod(MAP_FEATURE_SHAPE))
    FEATURES = HERO_FEATURE + [
        MAP_FEATURE_DIM,  # 地图信息
    ]
    # FEATURES = [11 * 11]

    FEATURE_SPLIT_SHAPE = FEATURES

    # Size of observation
    # observation的维度
    DIM_OF_OBSERVATION = sum(FEATURES)

    # Dimension of movement action direction
    # 移动动作方向的维度  # 神经的络输出维度
    DIM_OF_ACTION_DIRECTION = 8

    # Dimension of flash action direction
    # 闪现动作方向的维度
    DIM_OF_TALENT = 8

    # 全部动作维度
    ACTION_NUM = DIM_OF_ACTION_DIRECTION + DIM_OF_TALENT

    # Input dimension of reverb sample on learner. Note that different algorithms have different dimensions.
    # **Note**, this item must be configured correctly and should be aligned with the NumpyData2SampleData function data in definition.py
    # Otherwise the sample dimension error may be reported
    # learner上reverb样本的输入维度
    # **注意**，此项必须正确配置，应该与definition.py中的NumpyData2SampleData函数数据对齐，否则可能报样本维度错误
    SAMPLE_DIM = 2 * (DIM_OF_OBSERVATION + ACTION_NUM) + 4

    # Update frequency of target network
    # target网络的更新频率
    TARGET_UPDATE_FREQ = 200

    # Discount factor GAMMA in RL
    # RL中的回报折扣GAMMA
    GAMMA = 0.995

    # epsilon
    EPSILON_MIN = 0.1
    EPSILON_MAX = 1.0
    # EPSILON_MIN = 0.1
    # EPSILON_MAX = 0.1
    EPSILON_DECAY = 1e-6
    # EPSILON_DECAY = 1e-4
    # mjj电脑 8h 2e4步
    # wty电脑 8h 3e4步

    # Initial learning rate
    # 初始的学习率
    START_LR = 1e-4

    ############################################################
    # 在官方配置上新加入参数
    ############################################################
    SEQUENCE_LENGTH = 10  # 记忆长度

    #################### 奖励 ####################
    REW_FINISH = 15  # 到终点奖励
    REW_TRUNCATED_PUNISH = 80  # 截断惩罚
    REW_TREASURE = 10  # 获得宝箱奖励, 到终点但错失的宝箱就是惩罚
    REW_FLASH = 0.1  # 闪现距离减15乘系数并对奖励做clip(-5, 0)范围
    REW_DISTANCE = 0.1  # 距离奖励向目标 (终点) 移动 (每一帧进行一次奖励)
    REW_HIT_WALL_PUNISH = 0.1  # 撞墙惩罚 (每一帧进行一次惩罚)
    REW_BUFF = 0.5  # 获得buff奖励
    REW_EACH_STEP_PUNISH = 0.02  # 每步的惩罚
    # REW_MEMORY_PUNISH_COEF = np.array([  # 周围重复步数惩罚
    #     [0.0, 0.0, 0.0, 0.0, 0.0],
    #     [0.0, 0.5, 0.8, 0.5, 0.0],
    #     [0.0, 0.8, 1.0, 0.8, 0.0],
    #     [0.0, 0.5, 0.8, 0.5, 0.0],
    #     [0.0, 0.0, 0.0, 0.0, 0.0],
    # ], np.float32)
    # REW_MEMORY_PUNISH_STEP = 2  # 周围重复步数惩罚的步数
    REW_MEMORY_PUNISH_SIZE = 3  # 周围重复步数惩罚的大小
    REW_MEMORY_PUNISH_THRESHOLD = 9  # 周围重复步数惩罚的阈值
    REW_MEMORY_PUNISH_COEF = 0.1  # 周围重复步数惩罚系数
    REW_EXPLORATION = 0.000  # 探索奖励 (王者无需探索奖励)
    REW_GLOBAL_SCALE = 1.0  # 奖励缩放系数
