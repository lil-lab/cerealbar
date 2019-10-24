# Config

This directory contains classes defining arguments used for the main
function.

## `Args`

This is a superclass for all other argument classes.

## `ProgramArgs`

A program can have one of the following `RunType`:

- `TRAIN`, which trains a model.
- `EVALUATE`, which evaluates a trained model.
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

### `StateRepresentationArgs`

This set of arguments specifies how the environment state is represented before being encoded. It defines the 
following arguments:

* `full_observability`: Whether the environment representation contains full knowledge of the environment. _Default: 
True_ **Note: partial observability (`full_observability == False`) is currently not supported.**
* `property_embedding_size`: The size of the vector to encode each hex's property to. _Default: 32_
* `learn_absence_embeddings`: Whether to learn and use embeddings that correspond to the absence of a particular 
object type. If False, the property type will be set to a zero-vector. _Default: True_

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

## `TrainingArgs`

This script provides an enumeration of optimizer types, called `OptimizerType`, with the following possible values:

* `ADAM`: Adam optimizer (Kingma and Ba, 2014).
* `ADAGRAD`: Adagrad optimizer.
* `RMSPROP`: RMSProp optimizer.
* `SGD`: SGD optimizer.

This set of arguments specifies training options.

Arguments for bookkeeping:

* `save_directory`: The directory where the model parameters should be saved. A subdirectory of this will be 
saved for this specific experiment, based on the `experiment_name`.
* `experiment_name`: The name of the experiment to train.
* `log_with_slack`: Whether to log experiment details (epoch accuracies and final evaluation) to a Slack workspace.

Handling data during training.
* `batch_size`: The batch size to use in training. _Default: 16_
* `proportion_of_train_for_accuracy`: The proportion of training examples that should be used each epoch to 
compute an estimate of training accuracy. _Default: 0.1_
* `aggregate_examples`: Whether to aggregate error-recovery examples during training. _Default: False, but should be 
set to True during fine-tuning_

Arguments for training scheduling:
* `initial_patience`: The initial number of epochs allowed without improvement on validation set before terminating 
training, for pretraining. This will be updated each time the validation performance improves. _Default: 10_
* `patience_update_ratio`: The factor by which the maximum patience will be updated upon validation improvement. 
_Default: 1.01_
* `stopping_metric`: The metric used to decide when to stop based on validation performance (during pretraining only). 
_Default: 
RELAXED_ENVIRONMENT_ACCURACY_
* `validation_metrics`: A list of metrics that should be computed on the validation data after each epoch. _Default: 
all metrics_
* `training_metrics`: A list of metrics that should be computed on the training data after each epoch. _Default: all 
metrics_

Arguments for the optimizer:
* `plan_prediction_learning_rate`: The learning rate of the model when pretraining the plan predictor. _Default: 0.0075_
* `plan_prediction_l2_coefficient`: The L2 coefficient on the model parameters when pretraining the plan predictor. 
_Default: 0.000001_
* `action_generation_learning_rate`: The learning rate of the model when pretraining the action generator. _Default: 
0.001_
* `action_generation_l2_coefficient`: The L2 coefficient on the model parameters when pretraining the action 
generator. _Default: 0._
* `finetune_learning_rate`: The learning rate to use when finetuning the model components together. _Default: 0.001_
* `finetune_l2_coefficient`: The L2 coefficient on the model parameters when finetuning the model components together
. _Default: 0._
* `max_gradient`: The maximum value gradients will be clipped to during training. _Default: 1._
* `optimizer`: The type of optimizer to use. _Default: ADAM_


Coefficients for auxiliary losses. The default values are `0.`, so they should be explicitly set according to which 
stage of training. See our values below. 

There are two sets of coefficient: one to be used during pretraining the plan predictor, and another to be used 
during fine-tuning the whole network. There are auxiliary losses:

* Intermediate goal probabilities: the probability of a position containing a goal location (independent of other 
locations), as computed using an intermediate representation in the network before LingUNet is applied.
* Final goal probabilities: the probability of a position containing a goal location (independent of other locations)
, as computed on the output of the LingUNet.
* Obstacle probabilities: the probability of a position containing an obstacle (independently of other locations).
* Avoid probabilities: the probability of a position being one the agent should not reach (independently of other 
locations), e.g., containing a card it should not disturb.
* Trajectory distribution: joint distribution of probabilities of visiting each location in the environment (i.e., 
probability it appears in the trajectory).
* Implicit action probability (fine-tuning only): probability of the instruction requiring implicit actions, computed
 at the output of each LingUNet layer.

Below are the recommended values. All should be set to zero when pretraining the action generator. To remove an 
auxiliary, set its coefficient to zero. We recommend using the same auxiliary coefficients during pretraining of the 
plan predictor and fine-tuning the whole model.

* `*_auxiliary_coefficient_intermediate_goal_probabilities=1.0`
* `*_auxiliary_coefficient_final_goal_probabilities=1.0`
* `*_auxiliary_coefficient_obstacle_probabilities=0.1`
* `*_auxiliary_coefficient_avoid_probabilities=0.1`
* `*_auxiliary_coefficient_trajectory_distribution=1.0` 
* `finetune_auxiliary_coefficient_implicit_actions=0.7`

## `ReplayArgs`
When the program's run type is `REPLAY`, recorded games will be played back in the Unity standalone application. The 
following arguments can be used to control how to replay the games:

* `game_directory`: A directory containing JSON files with game information.
* `game_id`: The ID of the game to replay.
* `instruction_id`: The ID of the instruction to replay. If not set, the whole game will be replayed.
* `realtime`: Whether to play back the games taking into account the original timing between actions.
* `speed`: If executing instructions in realtime, pauses in the game are scaled by this factor. E.g., if set to 0.5, 
games will be replayed at double the speed.

## `GameArgs`
These arguments define how the Unity standalone (or Python equivalent) should implement game rules. For example, it 
allows you to set a new value for the number of moves per turn each player has. It has the following arguments:

* `game_ip`: The IP address where the game is being hosted. _Default: localhost_
* `game_port`: The port where the game is being hosted. _Default: 6000_
* `keep_track_of_turns`: Whether the game should keep track of whose turn it is, how many moves are left in a turn, 
and how many turns are remaining. If set to False, it's assumed that actions sent to the game will correctly follow 
the game rules (e.g., explicitly end a turn). This is useful when replaying recorded games.
* `initial_number_of_turns`: The initial number of turns the two players have. _Default: 6_
* `leader_moves_per_turn`: The number of moves the leader has per turn. _Default: 5_
* `follower_moves_per_turn`: The number of moves the follower has per turn. _Default: 10_
* `action_delay`: The number of seconds to delay between actions. If replaying and `realtime` is set to True, this 
value should be set to 0. 
* `generate_new_cards`: Whether new cards should be generated by Python when an unexpected set is made (e.g., during 
inference).

## `DataArgs`

These arguments define how data is loaded and processed for training and evaluation.

* `saved_game_directory`: The directory where game JSON files are saved for training and evaluation.
* `game_state_filename`: A path to a `pkl` file (will be created if it doesn't exist) that caches all game states. 
The original JSON files don't contain every bit of information about the game (props and terrain, game board state 
after each action), so this file must be created before any training occurs by replaying each game in the training 
and evaluation sets. _Default: False_
* `case_sensitive`: Whether to keep the original casing of text.
* `minimum_wordtype_occurrence`: Word types that appear at least this many times will be kept in the vocabulary; 
all others will be mapped to an unknown token. _Default: 2_
* `validation_proportion`: The proportion of training data that will be held out during training for stopping. 
_Default: 0.05_
* `maximum_instruction_index`: If set to zero or more, only instructions with this index (or less) will be used 
during training and evaluation. This is good for debugging as it reduces the dataset size, and generally first 
instructions are a bit easier than later ones. _Default: -1 (uses all data)_
* `maximum_number_examples`: If set to zero or more, only this number of games will be loaded from disk. Use it only 
for debugging. _Default: -1 (uses all data)_

## `EvaluationArgs`

These arguments define how evaluation should be performed. These arguments also apply to evaluation done during 
training (e.g., on the validation set).

* `use_unity`: Whether to use the Unity standalone to show inference.
* `visualize_auxiliaries`: Whether to visualize predicted plans in the Unity standalone.
* `save_file`: The name of the model save to load from.
* `maximum_generation_length`: The maximum number of actions that the agent can generate. _Default: 25_
* `metric_distance_threshold`: How far the agent can be from the goal location to score a point under 
`RELAXED_ENVIRONMENT_ACCURACY`. _Default: 0 (must be in the correct spot)_
* `reset_after_instruction`: Whether to reset the game state after an instruction has been completed. If False, 
instructions in an interaction will be followed sequentially without resetting (allowing error propagation).
* `split`: The split to evaluate on.
* `examples_filename`: If `split` is `SPECIFIED`, this should be set to a filepath containing game IDs of examples to 
run inference on, pulled from the training, development, or test set. This can be used for debugging.


# References
Valts Blukis, Dipendra Misra, Ross A. Knepper, and Yoav Artzi. 
Mapping navigation instructions to continuous control 
actions with position visitation prediction.
In CoRL, 2018.

Diederik P. Kingma and Jimmy Ba. 
Adam: A method for stochastic optimization. 
In ICLR, 2014.

# TODO

- [ ] Interactive replay browser with a bit more functionality than just specifying a game ID.