#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
###########################################################################
# Copyright © 1998 - 2025 Tencent. All Rights Reserved.
###########################################################################
"""
Author: Tencent AI Arena Authors
"""


import torch
import numpy as np
from torch import nn
import torch.nn.functional as F
from typing import List
from agent_target_dqn.conf.conf import Config

import sys
import os

if os.path.basename(sys.argv[0]) == "learner.py":
    import torch

    torch.set_num_interop_threads(2)
    torch.set_num_threads(2)
else:
    import torch

    torch.set_num_interop_threads(4)
    torch.set_num_threads(4)


class Model(nn.Module):
    def __init__(self, action_shape):
        super().__init__()
        # feature configure parameter
        # 特征配置参数
        self.feature_len = Config.DIM_OF_OBSERVATION

        # Q network
        # Q 网络
        self.q_cnn = nn.Sequential(
            nn.Conv2d(4, 32, kernel_size=7, stride=2),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=5, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU(),
            nn.Flatten(),
            MLP([4096, 512], "q_cnn", non_linearity_last=True)
        )
        # self.mlp = MLP([512 + 5, 256, action_shape], "mlp")
        # self.mlp = MLP([11*11, 128, action_shape], "mlp")
        self.mlp = nn.Sequential(
            MLP([512 + Config.HERO_FEATURE_DIM, 256], "mlp", non_linearity_last=True),
            # ResidualBlock(256),
            MLP([256, action_shape], "mlp")
        )

    # Forward inference
    # 前向推理
    def forward(self, feature):
        x, map = feature[:, :Config.HERO_FEATURE_DIM], feature[:, Config.HERO_FEATURE_DIM:].reshape(-1, *Config.MAP_FEATURE_SHAPE)
        # Action and value processing
        logits = self.mlp(torch.cat([self.q_cnn(map), x], dim=1))
        # logits = self.mlp(feature)
        return logits

def make_fc_layer(in_features: int, out_features: int, init_method: str = 'orthogonal'):
    fc_layer = nn.Linear(in_features, out_features)
    if init_method == 'orthogonal':
        nn.init.orthogonal_(fc_layer.weight)
    elif init_method == 'kaiming':
        nn.init.kaiming_uniform_(fc_layer.weight, nonlinearity='relu')
    nn.init.zeros_(fc_layer.bias)
    return fc_layer

class MLP(nn.Module):
    def __init__(
        self,
        fc_feat_dim_list: List[int],
        name: str,
        non_linearity: nn.Module = nn.ReLU,
        non_linearity_last: bool = False,
    ):
        # Create a MLP object
        # 创建一个 MLP 对象
        super().__init__()
        self.fc_layers = nn.Sequential()
        for i in range(len(fc_feat_dim_list) - 1):
            fc_layer = make_fc_layer(fc_feat_dim_list[i], fc_feat_dim_list[i + 1])
            self.fc_layers.add_module("{0}_fc{1}".format(name, i + 1), fc_layer)
            # no relu for the last fc layer of the mlp unless required
            # 除非有需要，否则 mlp 的最后一个 fc 层不使用 relu
            if i + 1 < len(fc_feat_dim_list) - 1 or non_linearity_last:
                self.fc_layers.add_module("{0}_non_linear{1}".format(name, i + 1), non_linearity())

    def forward(self, data):
        return self.fc_layers(data)

class ResidualBlock(nn.Module):
    def __init__(self, dim: int | tuple):
        super().__init__()
        self.net1 = make_fc_layer(dim, dim * 4, init_method='kaiming')
        self.net2 = make_fc_layer(dim * 4, dim, init_method='kaiming')
        self.layer_norm = nn.LayerNorm(dim)

    def forward(self, x):
        residual = x
        x = self.layer_norm(x)
        x = self.net1(x)
        x = torch.relu(x)
        x = self.net2(x)
        return residual + x

if __name__ == '__main__':
    # Example usage
    model = Model(action_shape=Config.ACTION_NUM)
    print(model)
    obs = torch.rand(10, Config.DIM_OF_OBSERVATION)  # Example observation
    output = model(obs)
    print(output)
    from agent_target_dqn.utils import PATH_DEBUG
    torch.save(model.state_dict(), PATH_DEBUG / 'model.pth')
