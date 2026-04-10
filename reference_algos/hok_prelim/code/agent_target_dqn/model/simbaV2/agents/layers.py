import torch
import torch.nn as nn
from agent_target_dqn.model.simbaV2.common.math import l2normalize
import math
import torch.nn.init as init


class Scaler(nn.Module):
    def __init__(self, dim, init=1.0, scale=1.0):
        super().__init__()
        self.init = init
        self.scale = scale
        self.scaler = nn.Parameter(torch.empty(dim))
        self.forward_scaler = self.init / self.scale

        self._init_weights()

    def _init_weights(self):
        init.constant_(self.scaler, 1.0 * self.scale)

    def forward(self, x):
        return self.scaler * self.forward_scaler * x


class HyperDense(nn.Module):
    def __init__(self, in_dim, hidden_dim):
        super().__init__()
        self.hyper_dense = nn.Linear(in_dim, hidden_dim, bias=False)

        self._init_weights()

    def _init_weights(self):
        init.orthogonal_(self.hyper_dense.weight)

    def forward(self, x):
        return self.hyper_dense(x)


class HyperMLP(nn.Module):
    def __init__(
        self, in_dim, hidden_dim, out_dim, scaler_init, scaler_scale, act=None, eps=1e-8
    ):
        super().__init__()
        self.w1 = HyperDense(in_dim, hidden_dim)
        self.scaler = Scaler(hidden_dim, scaler_init, scaler_scale)
        if act is None:
            self.act = nn.ReLU()
        else:
            self.act = act
        self.w2 = HyperDense(hidden_dim, out_dim)
        self.eps = eps

    def forward(self, x):
        x = self.w1(x)
        x = self.scaler(x)
        x = self.act(x) + self.eps  # `eps` is required to prevent zero vector.
        x = self.w2(x)
        x = l2normalize(x, dim=-1)
        return x


class HyperEmbedder(nn.Module):
    def __init__(self, in_dim, hidden_dim, scaler_init, scaler_scale, c_shift):
        super().__init__()
        self.w = HyperDense(in_dim + 1, hidden_dim)  # add one dim for feature shift
        self.scaler = Scaler(hidden_dim, scaler_init, scaler_scale)
        self.c_shift = c_shift

    def forward(self, x):
        new_dim = torch.ones((x.shape[:-1] + (1,)), device=x.device) * self.c_shift
        x = torch.concat([x, new_dim], dim=-1)
        x = l2normalize(x, dim=-1)
        x = self.w(x)
        x = self.scaler(x)
        x = l2normalize(x, dim=-1)
        return x


class HyperLERPBlock(nn.Module):
    def __init__(
        self,
        in_dim,
        hidden_dim,
        scaler_init,
        scaler_scale,
        alpha_init,
        alpha_scale,
        expansion=4,
    ):
        super().__init__()
        self.mlp = HyperMLP(
            in_dim=in_dim,
            hidden_dim=hidden_dim * expansion,
            out_dim=hidden_dim,
            scaler_init=scaler_init / math.sqrt(expansion),
            scaler_scale=scaler_scale / math.sqrt(expansion),
        )
        self.alpha_scaler = Scaler(
            hidden_dim,
            init=alpha_init,
            scale=alpha_scale,
        )

    def forward(self, x):
        residual = x
        x = self.mlp(x)
        x = residual + self.alpha_scaler(x - residual)
        x = l2normalize(x, dim=-1)
        return x


class HyperNormalPolicyHead(nn.Module):
    def __init__(
        self,
        in_dim,
        hidden_dim,
        action_dim,
        scaler_init,
        scaler_scale,
    ):
        super().__init__()
        self.mean_w1 = HyperDense(in_dim, hidden_dim)
        self.mean_scaler = Scaler(hidden_dim, scaler_init, scaler_scale)
        self.mean_w2 = HyperDense(hidden_dim, action_dim)
        self.mean_bias = nn.Parameter(torch.empty(action_dim))

        self.std_w1 = HyperDense(in_dim, hidden_dim)
        self.std_scaler = Scaler(hidden_dim, scaler_init, scaler_scale)
        self.std_w2 = HyperDense(hidden_dim, action_dim)
        self.std_bias = nn.Parameter(torch.empty(action_dim))

        self._init_weights()

    def _init_weights(self):
        init.zeros_(self.mean_bias)
        init.zeros_(self.std_bias)

    def forward(self, x):
        mean = self.mean_w1(x)
        mean = self.mean_scaler(mean)
        mean = self.mean_w2(mean) + self.mean_bias

        log_std = self.std_w1(x)
        log_std = self.std_scaler(log_std)
        log_std = self.std_w2(log_std) + self.std_bias

        return mean, log_std


class HyperDiscreteValueHead(nn.Module):
    def __init__(
        self,
        in_dim,
        hidden_dim,
        num_bins,
        scaler_init,
        scaler_scale,
    ):
        super().__init__()
        self.w1 = HyperDense(in_dim, hidden_dim)
        self.scaler = Scaler(hidden_dim, scaler_init, scaler_scale)
        self.w2 = HyperDense(hidden_dim, num_bins)
        self.bias = nn.Parameter(torch.empty(num_bins))

        self._init_weights()

    def _init_weights(self):
        init.zeros_(self.bias)

    def forward(self, x):
        value_bins = self.w1(x)
        value_bins = self.scaler(value_bins)
        value_bins = self.w2(value_bins) + self.bias
        return value_bins
