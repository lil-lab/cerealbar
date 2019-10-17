# Config

This directory contains classes defining arguments used for the main
function.

## `Args`

This is a superclass for all other argument classes.

## `ProgramArgs`

A program can have one of the following `RunType`:

- `TRAIN`, which trains a model.
- `EVAL`, which evaluates a trained model.
- `REPLAY`, which replays a previously-recorded game.

`ProgramArgs` is set of arguments defining how to run the main function. It
keeps track of the model, training, game, evaluation, and replay
arguments. 

It defines the following arguments:

- `run_type`: of type `RunType`
This argument defines what the program should do when running.

It also contains two utility functions:

- `save_args`, which saves specified `ProgramArgs` to a pickle file.
- `check_args`, which loads a saved `ProgramArgs` from a pickle file 
and checks against the specified `ProgramArgs`.

## `ModelArgs`

A model is defined by a `Task`, which takes one of the following values:

- `PLAN_PREDICTOR`: Takes as input the instruction and environment
and predicts distribution(s) over the environment.
- `ACTION_GENERATOR`: Takes as input the instruction and environment,
computes the plan distribution(s) (either 
gold distributions, or from an internal plan predictor), and generates a sequence
of actions.
- `SEQ2SEQ`: A baseline model that takes as input the instruction and 
environment and generates a sequence of actions.

`ModelArgs` is a set of arguments defining the model architecture. It
keeps track of the parameters for the instruction and state encoders,
how states are represented, and how actions are generated.

In this section, default values are those we used during our
experiments.

It defines the following arguments:

- `model_type`: of type `Task` that defines the model architecture's task. _Default: `ACTION_GENERATOR`, but when 
pretraining the plan predictor separately, this should be set to `PLAN_PREDICTOR`._
- `dropout`: of type `float` that specifies the dropout rate during training in the network. _Default: 0.0. This will
 be automatically set to 0.0 when running inference._
 
### `TextEncoderArgs`

This set of arguments specifies a configuration for encoding text, in this case instructions. It includes the 
following arguments:

* `encoder_cell_type`: The type of RNN cell to use for encoding, in string format. _Default: LSTM_
* `word_embedding_size`: The word embedding size for tokens. _Default: 64_
* `encoder_hidden_size`: The size of the hidden representation of tokens in the encoder RNN. _Default: 64_
* `encoder_number_layers`: The number of layers in the encoder RNN. _Default: 1_
* `encoder_bidirectional`: Whether to run the encoder RNN over the text in both directions. _Default: True_

### `StateEncoderArgs`

This set of arguments specifies the configuration for encoding
the environment state. It includes the following arguments, which
specify how convolution operations process image-like representations
of the environment:

* `encoder_stride`: The stride used. _Default: 2_
* `kernel_size`: The kernel size used. _Default: 3_
* `encoder_padding`: Padding used. _Default: 1_
* `encoder_depth`: The number of serial convolution operations. _Default: 4_

It also specifies a number of arguments specific to the VPN (Visitation Prediction Network, Blukis et al. 2018):

* `lingunet_convolution_layers`: The number of convolution layers in the LingUNet block at each layer. _Default: 2_
* `lingunet_after_conv_channels`: The number of channels of the image representation after 
convolving to reduce image size (lefthand side of LingUNet). _Default: 48_
* `lingunet_after_text_channels`: The number of channels of the image representation after convolving
using text-based kernels in the LingUNet (center of LingUNet). _Default: 24_
* `lingunet_normalize`: Whether to apply L2 and instance normalization within the LingUNet after each convolution 
layer. 
_Default: True_
* `lingunet_nonlinearities`: Whether to apply nonlinearities after each convolution layer in the LingUNet. _Default: 
True_
* `vpn_num_output_hidden_layers`: A number of MLPs applied on the output of the VPN. _Default: 0_
* `vpn_conv_initialization`: The initialization to use for convolution layers
in the VPN. _Default: Kaiming Uniform_

### `ActionGeneratorArgs`

This set of arguments specifies the hyperparameters for the action generator.

Recurrence over actions is specified by:
* `use_recurrence`: Whether to use an LSTM to keep track of previous actions and observed states in the action 
decoder. _Default: True_
* `action_embedding_size`: The word embedding size for each action (if `use_recurrence` is true). _Default: 32_
* `decoder_hidden_size`: The number of hidden units in the decoder LSTM (if `use_recurrence` is true). _Default: 128_
* `decoder_num_layers`: The number of layers in the decoder LSTM (if `use_recurrence` is true). _Default: 1_

The kinds of input expected to the action generator is specified by the following. The first three describe 
probabilities of specific kinds of locations in the environment satisfying a particular property, and the last 
describes a joint distribution over the entire environment:
* `use_goal_probabilities`: Individual probabilities of a goal card appearing in each location. _Default: True_
* `use_obstacle_probabilities`: Individual probabilities of an obstacle appearing in each location. _Default: True_
* `use_avoid_probabilities`: Individual probabilities of each location being somewhere the agent should avoid (e.g., 
contains a card it should not disturb). _Default: True_
* `use_trajectory_distribution`: Joint distribution over the entire map of each location being part of the trajectory
 the agent should take. _Default: True_
* `weight_trajectory_by_time`: Whether the distribution over the map specifying visitation prediction probabilities 
should be weighted according to the amount of time the agent spent in a location (if `use_trajectory_distribution`). 
_Default: True_

How the input distributions are processed is specified by:
* `crop_size`: The number of pixels (approximately hexes) to which the inputs to the action generator will be cropped
 around the agent's current location before embedding. After cropping, the representation will be of size 
 `[crop_size, crop_size, N]`, where `N` is the number of channels. _Default: 5_
* `state_internal_size`: The size of the vector that the inputs to the action generator should be compressed to 
before predicting an action. _Default: 64_
* `convolution_encode_map_distributions`: Whether to use a CNN to encode the input to the action generator before 
predicting actions. _Default: True_

Finally, this set of parameters also specifies some settings for end-to-end vs. individual training of the two model 
components.

* `end_to_end`: Whether to train the plan predictor jointly with the action generator. _Default: False, but should be
 set to True when training the two parts jointly._
* `pretrained_action_generator_filepath`: A filepath containing model parameters for a pretrained action generator.
* `pretrained_plan_predictor_filepath`: A filepath containing model parameters for a pretrained plan predictor.


# References
Mapping Navigation Instructions to Continuous Control Actions with Position Visitation Prediction.
Valts Blukis, Dipendra Misra, Ross A. Knepper, and Yoav Artzi
In Proceedings of the Conference on Robot Learning (CoRL), 2018.