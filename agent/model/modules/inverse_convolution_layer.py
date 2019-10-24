import math
import torch
from typing import Tuple

from torch import nn as nn

from agent.model.utilities import initialization


class InverseConvolutionLayer(torch.nn.Module):
    def __init__(self,
                 depth: int,
                 in_channels: int,
                 out_channels: int,
                 kernel_size,
                 stride: int =1,
                 padding: int = 0,
                 initializer: initialization.Initialization = initialization.Initialization.KAIMING_UNIFORM,
                 upsampling_deconv: bool = False):
        super(InverseConvolutionLayer, self).__init__()

        self._stride = stride

        self._deconv_layers = nn.ModuleList([])
        self._depth = depth
        self._upsample = upsampling_deconv

        for i in range(self._depth):
            s: int = stride if i == self._depth - 1 else 1
            inc: int = in_channels if i == 0 else out_channels

            if upsampling_deconv:
                # Stride is always 1 because we want the output size to be the larger size (we don't want the image
                # to be smaller).
                layer: nn.Module() = nn.Conv2d(inc, out_channels, kernel_size, stride=1, padding=padding)
                initializer.initialize(layer.weight)
            else:
                layer: nn.Module = nn.ConvTranspose2d(inc, out_channels, kernel_size, stride=s, padding=padding)
                initializer.initialize(layer.weight)
            self._deconv_layers.append(layer)

            # Leaky relu between layers (but not on the output)
            if i < self._depth - 1:
                self._deconv_layers.append(nn.LeakyReLU())

    def forward(self, img: torch.Tensor, output_size: torch.Size):
        internal_size: Tuple[int] = [math.ceil(i / self._stride) for i in output_size]
        x = img
        num_deconvs: int = 0
        for i, layer in enumerate(self._deconv_layers):
            if i == len(self._deconv_layers) - 1 and self._upsample:
                # Upsample
                x = nn.functional.interpolate(x, size=(output_size[2], output_size[3]))
            if isinstance(layer, nn.ConvTranspose2d):
                # If it's one of the deconv layers, the output size will be the internal size if it's not the final
                # deconv, otherwise it will be the output size.
                x = layer(x, output_size=internal_size if (num_deconvs < self._depth - 1) else output_size)
                num_deconvs += 1
            else:
                x = layer(x)
        return x
