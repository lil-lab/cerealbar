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

It defines the following arguments:

- `model_type`: of type `Task` that defines the model architecture's task.

