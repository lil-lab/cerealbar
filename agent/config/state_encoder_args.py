""" Contains arguments for the environment state encoder.

Classes:
    StateEncoderType (Enum): The types of state encoders.
    StateEncoderArgs (Args): The arguments for the state encoder.
"""
from argparse import ArgumentParser, Namespace
from distutils.util import strtobool

from agent.model.utilities import initialization
from agent.config import args


class StateEncoderArgs(args.Args):
    """ State encoder arguments."""

    def __init__(self, parser: ArgumentParser):
        super(StateEncoderArgs, self).__init__()

        # Generic encoder parameters.
        parser.add_argument('--encoder_stride',
                            default=2,
                            type=int,
                            help='Stride for convolution.')
        parser.add_argument('--kernel_size',
                            default=3,
                            type=int,
                            help='Kernel size for convolution.')
        parser.add_argument('--encoder_padding',
                            default=1,
                            type=int,
                            help='Padding for convolution.')
        parser.add_argument('--encoder_depth',
                            default=4,
                            type=int,
                            help='Number of serial convolution layers.')

        # VPN-specific parameters.
        parser.add_argument('--vpn_num_output_hidden_layers',
                            default=0,
                            type=int,
                            help='Depth of the MLP after applying VPN.')
        parser.add_argument('--vpn_convolution_initialization',
                            default=initialization.Initialization.KAIMING_UNIFORM,
                            type=initialization.Initialization,
                            help='The initialization to use for the convolution layers in VPN.')

        parser.add_argument('--lingunet_after_convolution_channels',
                            default=48,
                            type=int,
                            help='Number of channels of representation after reduction convolutions in LingUNet.')
        parser.add_argument('--lingunet_after_text_channels',
                            default=24,
                            type=int,
                            help='Number of channels of representation after convolving using text channels.')
        parser.add_argument('--lingunet_convolution_layers',
                            default=2,
                            type=int,
                            help='The number of layers per convolutional block depth in LingUNet.')
        parser.add_argument('--lingunet_normalize',
                            default=True,
                            type=lambda x: strtobool(x),
                            help='Whether to apply L2 and instance normalization after convolutional layers in '
                                 'LingUNet.')
        parser.add_argument('--lingunet_nonlinearities',
                            default=True,
                            type=lambda x: strtobool(x),
                            help='Whether to apply nonlinearities after convolutional layers in LingUNet.')

        self._encoder_stride: int = None
        self._kernel_size: int = None
        self._encoder_padding: int = None
        self._encoder_depth: int = None

        self._vpn_num_output_hidden_layers: int = None
        self._vpn_convolution_initialization: initialization.Initialization = None

        self._lingunet_after_convolution_channels: int = None
        self._lingunet_after_text_channels: int = None
        self._lingunet_convolution_layers: int = None

        self._lingunet_normalize: bool = None
        self._lingunet_nonlinearities: bool = None

    def get_lingunet_after_convolution_channels(self) -> int:
        self.check_initialized()
        return self._lingunet_after_convolution_channels

    def get_lingunet_after_text_channels(self) -> int:
        self.check_initialized()
        return self._lingunet_after_text_channels

    def get_lingunet_convolution_layers(self) -> int:
        self.check_initialized()
        return self._lingunet_convolution_layers

    def get_vpn_convolution_initialization(self) -> initialization.Initialization:
        self.check_initialized()
        return self._vpn_convolution_initialization

    def lingunet_normalize(self) -> bool:
        self.check_initialized()
        return self._lingunet_normalize

    def lingunet_nonlinearities(self) -> bool:
        self.check_initialized()
        return self._lingunet_nonlinearities

    def get_vpn_num_output_hidden_layers(self) -> int:
        self.check_initialized()
        return self._vpn_num_output_hidden_layers

    def get_encoder_stride(self) -> int:
        self.check_initialized()
        return self._encoder_stride

    def get_kernel_size(self) -> int:
        self.check_initialized()
        return self._kernel_size

    def get_encoder_padding(self) -> int:
        self.check_initialized()
        return self._encoder_padding

    def get_encoder_depth(self) -> int:
        self.check_initialized()
        return self._encoder_depth

    def interpret_args(self, parsed_args: Namespace) -> None:
        self._encoder_stride = parsed_args.encoder_stride
        self._kernel_size = parsed_args.kernel_size
        self._encoder_padding = parsed_args.encoder_padding
        self._encoder_depth = parsed_args.encoder_depth

        self._vpn_num_output_hidden_layers = parsed_args.vpn_num_output_hidden_layers
        self._vpn_convolution_initialization = parsed_args.vpn_convolution_initialization

        self._lingunet_after_convolution_channels = parsed_args.lingunet_after_convolution_channels
        self._lingunet_after_text_channels = parsed_args.lingunet_after_text_channels
        self._lingunet_convolution_layers = parsed_args.lingunet_convolution_layers
        self._lingunet_normalize = parsed_args.lingunet_normalize
        self._lingunet_nonlinearities = parsed_args.lingunet_nonlinearities

        super(StateEncoderArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        str_rep: str = '*** State encoder arguments ***' \
                       '\nConvolution stride: %r' \
                       '\nConvolution kernel size: %r' \
                       '\nConvolution padding: %r' \
                       '\nConvolution depth (number of layers): %r' \
                       '\n\nVPN specific arguments...' \
                       '\nNumber of output hidden layers: %r' \
                       '\nConvolution initialization: %r' \
                       '\nNumber of channels after initial convolutions: %r' \
                       '\nNumber of channels after text-based convolutions: %r' \
                       '\nNumber of convolution operations in each LingUNet layer: %r' \
                       '\nNormalize after convolutions? %r' \
                       '\nNonlinearities after convolutions? %r' % (self._encoder_stride, self._kernel_size,
                                                                    self._encoder_padding, self._encoder_depth,
                                                                    self._vpn_num_output_hidden_layers,
                                                                    self._vpn_convolution_initialization,
                                                                    self._lingunet_after_convolution_channels,
                                                                    self._lingunet_after_text_channels,
                                                                    self._lingunet_convolution_layers,
                                                                    self._lingunet_normalize,
                                                                    self._lingunet_nonlinearities)

        return str_rep

    def __eq__(self, other) -> bool:
        if isinstance(other, StateEncoderArgs):
            still_equal = self._encoder_stride == other.get_encoder_stride() \
                          and self._encoder_padding == other.get_encoder_padding() \
                          and self._encoder_depth == other.get_encoder_depth() \
                          and self._kernel_size == other.get_kernel_size() \
                          and self._vpn_num_output_hidden_layers == other.get_vpn_num_output_hidden_layers() \
                          and self._vpn_convolution_initialization == other.get_vpn_convolution_initialization() \
                          and self._lingunet_after_convolution_channels == \
                          other.get_lingunet_after_convolution_channels() \
                          and self._lingunet_after_text_channels == other.get_lingunet_after_text_channels() \
                          and self._lingunet_convolution_layers == other.get_lingunet_convolution_layers() \
                          and self._lingunet_normalize == other.lingunet_nonlinearities() \
                          and self._lingunet_nonlinearities == other.lingunet_nonlinearities()
            return still_equal
        return False
