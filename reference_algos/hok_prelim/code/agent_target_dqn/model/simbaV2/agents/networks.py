import torch
import torch.nn as nn
# from tensordict import from_modules
from copy import deepcopy
import math
from agent_target_dqn.model.simbaV2.agents.layers import (
    HyperDense,
    HyperEmbedder,
    HyperLERPBlock,
    HyperNormalPolicyHead,
    HyperDiscreteValueHead,
)
from agent_target_dqn.model.simbaV2.common.math import l2normalize


class SimbaV2Actor(nn.Module):
    def __init__(
        self,
        in_dim,
        num_blocks,
        hidden_dim,
        action_dim,
        scaler_init,
        scaler_scale,
        alpha_init,
        alpha_scale,
        c_shift,
    ):
        super().__init__()
        self.embedder = HyperEmbedder(
            in_dim=in_dim,
            hidden_dim=hidden_dim,
            scaler_init=scaler_init,
            scaler_scale=scaler_scale,
            c_shift=c_shift,
        )
        self.encoder = nn.Sequential(
            *[
                HyperLERPBlock(
                    in_dim=hidden_dim,
                    hidden_dim=hidden_dim,
                    scaler_init=scaler_init,
                    scaler_scale=scaler_scale,
                    alpha_init=alpha_init,
                    alpha_scale=alpha_scale,
                )
                for _ in range(num_blocks)
            ]
        )
        self.predictor = HyperNormalPolicyHead(
            in_dim=hidden_dim,
            hidden_dim=hidden_dim,
            action_dim=action_dim,
            scaler_init=1.0,
            scaler_scale=1.0,
        )

    def forward(self, obs):
        y = self.embedder(obs)
        z = self.encoder(y)
        raw_mean, raw_log_std = self.predictor(z)

        # construct tanh action here?

        return raw_mean, raw_log_std


class SimbaV2Critic(nn.Module):
    def __init__(
        self,
        in_dim,
        num_blocks,
        hidden_dim,
        scaler_init,
        scaler_scale,
        alpha_init,
        alpha_scale,
        c_shift,
        num_bins,
    ):
        super().__init__()
        self.embedder = HyperEmbedder(
            in_dim=in_dim,
            hidden_dim=hidden_dim,
            scaler_init=scaler_init,
            scaler_scale=scaler_scale,
            c_shift=c_shift,
        )
        self.encoder = nn.Sequential(
            *[
                HyperLERPBlock(
                    in_dim=hidden_dim,
                    hidden_dim=hidden_dim,
                    scaler_init=scaler_init,
                    scaler_scale=scaler_scale,
                    alpha_init=alpha_init,
                    alpha_scale=alpha_scale,
                )
                for _ in range(num_blocks)
            ]
        )
        self.predictor = HyperDiscreteValueHead(
            in_dim=hidden_dim,
            hidden_dim=hidden_dim,
            num_bins=num_bins,
            scaler_init=1.0,
            scaler_scale=1.0,
        )

    def forward(self, x):
        y = self.embedder(x)
        z = self.encoder(y)
        value_bins = self.predictor(z)
        return value_bins


class Temperature(nn.Module):
    def __init__(self, initial_value=0.01):
        super().__init__()
        self.log_temp = nn.Parameter(torch.ones([]) * math.log(initial_value))

    def __call__(self):
        return torch.exp(self.log_temp)


# class Ensemble(nn.Module):
#     """
#     Vectorized ensemble of modules.
#     """

#     def __init__(self, modules, **kwargs):
#         super().__init__()
#         # combine_state_for_ensemble causes graph breaks
#         self.params = from_modules(*modules, as_module=True)
#         with self.params[0].data.to("meta").to_module(modules[0]):
#             self.module = deepcopy(modules[0])
#         self._repr = str(modules[0])
#         self._n = len(modules)

#     def __len__(self):
#         return self._n

#     def _call(self, params, *args, **kwargs):
#         with params.to_module(self.module):
#             return self.module(*args, **kwargs)

#     def forward(self, *args, **kwargs):
#         # (0, None, None): for **two-args** forward call, like value_net(obs, action)
#         return torch.vmap(self._call, (0, None, None), randomness="different")(
#             self.params, *args, **kwargs
#         )

#     def __repr__(self):
#         return f"Vectorized {len(self)}x " + self._repr


@torch.no_grad()
def l2normalize_network(network):
    """Apply L2 normalization to all hyper-dense layers in the network"""

    # def norm_ensemble(name, tensor):
    #     if "hyper_dense" in name:
    #         assert tensor.ndim == 3
    #         tensor.set_(l2normalize(tensor, dim=1))

    def norm(m):
        if isinstance(m, HyperDense):
            assert m.hyper_dense.weight.ndim == 2
            m.hyper_dense.weight.set_(l2normalize(m.hyper_dense.weight, dim=0))

    # if isinstance(
    #     network, Ensemble
    # ):  # Params of Ensemble cannot be accessed via nn.Module.apply; apply manually instead.
    #     network.params.named_apply(norm_ensemble, nested_keys=True)
    # else:
    #     network.apply(norm)
    network.apply(norm)
