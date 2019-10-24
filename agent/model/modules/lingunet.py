"""
Attribution:
    LingUNet: Blukis et al. 2018 (CoRL), Misra et al. 2018 (EMNLP)
    Code: Chen et al. 2019 (CVPR), https://github.com/clic-lab/street-view-navigation
          Blukis et al. 2018 (CoRL); and ongoing work by Valts Blukis.

    Official drone sim code:
        https://github.com/clic-lab/drone-sim/blob/release/learning/modules/unet/unet_5_contextual_bneck3.py

"""
# TODO: Clean this code.
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import torch
import torch.nn as nn

from agent.model.modules import convolution_layer
from agent.model.modules import inverse_convolution_layer

if TYPE_CHECKING:
    from agent.config import state_encoder_args
    from typing import List, Optional, Tuple


class LingUNet(nn.Module):
    def __init__(self,
                 args: state_encoder_args.StateEncoderArgs,
                 input_channels: int,
                 text_hidden_size: int,
                 output_channels: int,
                 dropout: float = 0.,
                 extra_head_channels: int = 0,
                 input_img_size: int = 0,
                 layer_single_preds: bool = False):
        super(LingUNet, self).__init__()
        self._args: state_encoder_args.StateEncoderArgs = args
        self._input_channels: int = input_channels

        depth: int = self._args.get_encoder_depth()
        if text_hidden_size % depth != 0:
            raise ValueError('Text hidden size should be evenly divisible by depth: '
                             + str(text_hidden_size) + ' vs. ' + str(depth))

        sliced_text_vector_size: int = text_hidden_size // depth

        self._convolution_layers = nn.ModuleList([])
        self._text_kernel_fully_connected = nn.ModuleList([])
        self._text_convolution_instance_normsl = nn.ModuleList([])
        self._inverse_convolution_layers = nn.ModuleList([])
        self._text_kernel_outsizes: List[Tuple[int, int]] = list()
        self._dropout_layer = nn.Dropout(dropout)

        self._layer_single_preds: bool = layer_single_preds
        self._single_pred_layers = nn.ModuleList([])
        self._top_text_single_pred = None

        for i in range(depth):
            # INPUT CONV LAYERS
            conv_in_channels = self._args.get_lingunet_after_convolution_channels() if i > 0 else input_channels
            conv_out_channels: int = self._args.get_lingunet_after_convolution_channels()
            conv_module = nn.ModuleList([])
            conv_module.append(convolution_layer.ConvolutionLayer(
                self._args.get_lingunet_convolution_layers(),
                conv_in_channels,
                conv_out_channels,
                kernel_size=self._args.get_kernel_size(),
                stride=self._args.get_encoder_stride(),
                padding=self._args.get_encoder_padding(),
                initializer=self._args.get_vpn_convolution_initialization()))

            # Add a ReLU after each layer
            if self._args.lingunet_nonlinearities():
                conv_module.append(nn.LeakyReLU())

            # Add instance norm on the output of each layer except the last
            if i < depth - 1 and self._args.lingunet_normalize():
                conv_module.append(nn.InstanceNorm2d(conv_out_channels))

            # Have to set this as an attribute of the class, otherwise it won't be included in the parameters.
            self._convolution_layers.append(conv_module)

            # TEXT KERNEL LAYERS
            text_out_channels: int = self._args.get_lingunet_after_text_channels() if i < depth - 1 \
                else conv_out_channels
            self._text_kernel_fully_connected.append(nn.Linear(
                sliced_text_vector_size, conv_out_channels * text_out_channels))
            self._text_kernel_outsizes.append((text_out_channels, conv_out_channels))

            if i < depth - 1 and self._args.lingunet_normalize():
                self._text_convolution_instance_normsl.append(nn.InstanceNorm2d(text_out_channels))

            # This goes on the output of the text kernel at the topmost layer
            if self._layer_single_preds and i == 0:
                self._top_text_single_pred = nn.Conv2d(text_out_channels, 1, 1, bias=False)
                self._args.get_vpn_convolution_initialization().initialize(
                    self._top_text_single_pred.weight)

            # INVERSE CONVOLUTION LAYERS
            if i > 0:  # The deconv layer for i = 0 is separate.
                # At the very bottom, this takes as input only the output from the text kernel.
                deconv_in_channels = text_out_channels if i == depth - 1 else text_out_channels + conv_out_channels

                deconv_out_channels = conv_out_channels if i > 1 else input_channels

                deconv_module = nn.ModuleList([])
                deconv_module.append(
                    inverse_convolution_layer.InverseConvolutionLayer(
                        self._args.get_lingunet_convolution_layers(),
                        deconv_in_channels,
                        deconv_out_channels,
                        kernel_size=self._args.get_kernel_size(),
                        stride=self._args.get_encoder_stride(),
                        padding=self._args.get_encoder_padding(),
                        initializer=self._args.get_vpn_convolution_initialization(),
                        upsampling_deconv=False))
                if self._args.lingunet_nonlinearities():
                    deconv_module.append(nn.LeakyReLU())

                # Except for the very bottom level, add an instance norm
                if i < depth - 1 and self._args.lingunet_normalize():
                    deconv_module.append(nn.InstanceNorm2d(deconv_out_channels))
                self._inverse_convolution_layers.append(deconv_module)

                if self._layer_single_preds:
                    map_conv: nn.Module = nn.Conv2d(deconv_out_channels, 1, 1, bias=False)
                    self._args.get_vpn_convolution_initialization().initialize(map_conv.weight)

                    self._single_pred_layers.append(map_conv)

        # Then the final deconv layer
        # The input size will be number of input channels (from previous deconv)
        # + number of channels from top-level text conv
        # Output size is 1 (predicting a distribution)
        input_to_deconv_size = input_channels + self._text_kernel_outsizes[0][0]
        out_size = output_channels if self._args.get_vpn_num_output_hidden_layers() == 0 \
            else input_to_deconv_size
        self._final_deconv = nn.ConvTranspose2d(input_to_deconv_size,
                                                out_size,
                                                kernel_size=self._args.get_kernel_size(),
                                                stride=self._args.get_encoder_stride(),
                                                padding=self._args.get_encoder_padding())
        self._final_mlps = None
        if self._args.get_vpn_num_output_hidden_layers() > 0:
            hidden_layers = []
            for i in range(self._args.get_vpn_num_output_hidden_layers() - 1):
                hidden_layers += [nn.Linear(input_to_deconv_size, input_to_deconv_size), nn.ReLU()]
            self._final_mlps = nn.Sequential(*hidden_layers, nn.Linear(input_to_deconv_size, 1, bias=False))

        self._second_head_conv: nn.Module = None
        self._second_head_maxpool: nn.Module = None
        if extra_head_channels:
            # The stride is the size of the input image. E.g., if stride is 2, it will be 71/2 = 36.
            if input_img_size <= 0:
                raise ValueError('Input image size should be provided when expecting extra outputs.')
            self._second_head_conv = nn.Conv2d(input_to_deconv_size,
                                               extra_head_channels,
                                               self._args.get_kernel_size(),
                                               stride=self._args.get_encoder_stride())
            self._args.get_vpn_convolution_initialization().initialize(self._second_head_conv.weight)

            second_head_conv_stride: int = \
                math.ceil(math.ceil(input_img_size / self._args.get_encoder_stride())
                          / self._args.get_encoder_stride())
            self._second_head_maxpool = nn.MaxPool2d(second_head_conv_stride)

    def forward(self,
                images: torch.Tensor,
                texts: torch.Tensor) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[torch.Tensor]]:
        # [1] Apply the input convolutions.
        conv_outputs: List[torch.Tensor] = list()
        for i, layer in enumerate(self._convolution_layers):
            # Apply the layer to the previous output
            conv_in = images if i == 0 else conv_outputs[-1]
            x = conv_in
            for l in layer:
                x = l(x)

            conv_outputs.append(x)

        # [2] Apply the text convolutions.
        batch_size, text_hidden_size = texts.size()
        depth: int = self._args.get_encoder_depth()

        if self._args.lingunet_normalize():
            texts: torch.Tensor = nn.functional.normalize(texts, p=2, dim=1)
        sliced_size: int = text_hidden_size // depth

        text_conv_outputs: List[torch.Tensor] = list()
        top_text: torch.Tensor = None

        for i in range(depth):
            text_slices: torch.Tensor = texts[:, (i * sliced_size):((i + 1) * sliced_size)]

            layer_fc = self._text_kernel_fully_connected[i]

            input_size, output_size = self._text_kernel_outsizes[i]

            kernel_shape = (batch_size, input_size, output_size, 1, 1)

            # Compute the text kernel; normalize
            text_kernel: torch.Tensor = layer_fc(text_slices).view(kernel_shape)
            if self._args.lingunet_normalize():
                text_kernel: torch.Tensor = nn.functional.normalize(text_kernel)

            # Apply the text kernel. Have to do this by iterating over the batch.
            conv_output = conv_outputs[i]
            text_output: List[torch.Tensor] = list()
            for ex_output, f in zip(conv_output, text_kernel):
                text_output.append(nn.functional.conv2d(ex_output.unsqueeze(0), f))
            text_outputs = torch.cat(text_output, 0)

            # Apply the instance norm
            if i < depth - 1 and self._args.lingunet_normalize():
                text_outputs = self._text_convolution_instance_normsl[i](text_outputs)
            elif i == depth - 1:
                # Apply dropout on the final text-convolved output
                text_outputs = self._dropout_layer(text_outputs)

            if i == 0:
                top_text = text_outputs

            text_conv_outputs.append(text_outputs)

        # [3] Apply the deconvolutions from the bottom up.
        last_text_out: torch.Tensor = text_conv_outputs[-1]

        text_out_single_pred = None
        if self._layer_single_preds:
            text_out_single_pred = \
                nn.AvgPool2d(top_text.size(2))(self._top_text_single_pred(top_text)).view(batch_size, 1)

        deconv_outputs: List[torch.Tensor] = list()
        single_layer_preds: List[torch.Tensor] = list()
        for i in range(depth - 1, 0, -1):
            if i == depth - 1:
                deconv_input = last_text_out
            else:
                last_text_out = text_conv_outputs[i]
                # Concatenate the previous deconv output with this layer's text conv output
                deconv_input = torch.cat((last_text_out, deconv_outputs[-1]), 1)

            x = deconv_input
            for l in self._inverse_convolution_layers[i - 1]:
                if isinstance(l, inverse_convolution_layer.InverseConvolutionLayer):
                    x = l(x, output_size=text_conv_outputs[i - 1].size())
                else:
                    x = l(x)
            deconv_outputs.append(x)
            if self._layer_single_preds:
                unpooled_pred: torch.Tensor = self._single_pred_layers[i - 1](x)
                single_layer_preds.append(nn.AvgPool2d(unpooled_pred.size(2))(unpooled_pred).view(batch_size, 1))
        if self._layer_single_preds:
            single_layer_preds = torch.cat(tuple(single_layer_preds + [text_out_single_pred]), dim=1)

        # Apply the final deconvolution operation
        final_input = torch.cat((text_conv_outputs[0], deconv_outputs[-1]), 1)

        out = self._final_deconv(final_input, output_size=images.size())

        extra_preds: torch.Tensor = None
        if self._second_head_conv is not None:
            conv_out = self._second_head_conv(torch.cat((text_conv_outputs[0], deconv_outputs[-1]), dim=1))
            extra_preds = self._second_head_maxpool(conv_out).view(batch_size, -1)

        if self._final_mlps is not None:
            raise ValueError('The view/permute below is probably wrong!')
            flat_out = out.view(-1, out.size(1))
            out = self._final_mlps(flat_out).view(batch_size, 1, images.size(2), images.size(3))

        return out, extra_preds, single_layer_preds
