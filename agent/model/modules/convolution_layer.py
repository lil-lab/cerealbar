import torch
from torch import nn as nn

from agent.model.utilities import initialization


class ConvolutionLayer(torch.nn.Module):
    def __init__(self,
                 depth: int,
                 in_channels: int,
                 out_channels: int,
                 kernel_size: int,
                 stride: int = 1,
                 padding: int = 0,
                 initializer: initialization.Initialization = initialization.Initialization.KAIMING_UNIFORM):
        super(ConvolutionLayer, self).__init__()
        self._conv_layers = nn.ModuleList([])
        for i in range(depth):
            s: int = stride if i == 0 else 1
            o: int = out_channels if i == depth - 1 else in_channels
            layer: nn.Module = nn.Conv2d(in_channels, o, kernel_size, stride=s, padding=padding)
            initializer.initialize(layer.weight)
            self._conv_layers.append(layer)

            # Add a leaky relu between layers (but not on the output)
            if i < depth - 1:
                self._conv_layers.append(nn.LeakyReLU())

    def forward(self, img):
        x = img
        for l in self._conv_layers:
            x = l(x)
        return x
