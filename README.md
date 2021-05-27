# Cereal Bar
Cereal Bar is a two-player web game designed for studying language understanding agents in collaborative interactions. This repository contains code for the game, a webapp hosting the game, the agent implementation, and recorded interactions in the game. 

The game, data, and agent implementation (architecture, learning, and evaluation) are described in the following paper:

Executing instructions in situated collaborative interactions. Alane Suhr, Claudia Yan, Jacob Schluger, Stanley Yu, Hadi Khader, Marwa Mouallem, Iris Zhang, and Yoav Artzi. To appear in EMNLP 2019. Print coming soon!

## Setup

We recommend using the same virtual environment for all aspects of the project. We use Python 3.7.0. You can set this up
 by doing:

1. Clone this repository. **Make sure to use git lfs clone or you may have to type your password for every lfs file in this repository (there are hundreds of them -- so please don't do this!)**
1. Create a virtual environment for python 3.7 called `venv`: `python3.7 -m venv venv` _If you are having issues creating a virtual environment, please see [this Github Issues answer](https://github.com/ContinuumIO/anaconda-issues/issues/6917#issuecomment-340014721)._
1. Activate the virtual environment: `. venv/bin/activate`
1. Install the requirements: `pip install -r requirements.txt`


## Cereal Bar Game

### Unity Game

The directory `game/` contains the implementation of the Cereal Bar game in C#/Unity. The game can be built both for standalone playing (e.g., for replaying recorded interactions) and as a webapp (e.g., for hosting on a webpage).

### Webapp

The directory `webapp/` contains code to support hosting Cereal Bar on the web, either as a game between two human players or as a way to interact with a trained agent.

## Interaction Data

### Recorded Data

The directory `data/` contains recorded interactions of games played between two human players (which we used for training and evaluation) and between a human player and a trained agent (results of our evaluation).

To replay a game in the Unity standalone:

1. Ensure that the standalone `Cereal-Bar.app` is in the top-level directory. If not, you may need to re-build it 
(see README under `game/`).
1. Modify `agent/scripts/replay.sh` to include the ID of the game you would like to replay. The default in this 
repository is the game in Figure 1 of our paper.
1. Run `sh agent/scripts/replay.sh`

Note: whenever the standalone is launched from Python and not closed by Python (e.g., if an exception is made), you 
must manually exit the standalone process (e.g., by pressing x in the window) before running Python again, or the
Python process will hang.


### Crowdsourcing Utilities

The directory `crowdsourcing/` contains utilities that support collecting the interactions on Amazon Mechanical Turk (e.g., issuing HITs, downloading data).

## Agent

The directory `agent/` contains the implementation of the follower agent. It includes the following subdirectories:

* `config/` manages command-line arguments.
* `data/` manages loading training and evaluation data.
* `environment/` supports discrete representations of the game environment.
* `learning/` includes learning algorithms.
* `model/` contains the architecture.
* `simulation/` contains code for simulating gameplay.

### Training

#### Setup

1. Create the experiments directory (where model saves and preprocessed data will be stored), e.g., `mkdir 
agent/experiments/`.
1. Intermediate results (e.g., performance on the validation set) is logged using Crayon on the local machine. You 
need to download and start the Crayon server. Follow 
[these instructions from DyNet](https://github.com/clab/dynet/tree/master/examples/tensorboard).
You may need to comment out lines 24 -- 37 in `crayon.py` in the crayon installation if you want to run multiple 
experiments at once.

#### Notes

Once a CrayonExperiment is created with a specific name, another with the same name cannot be created unless the old 
one is deleted. Use the script `agent/scripts/remove_crayon_experiment.py` to delete a specific experiment by name.

Additionally, once the arguments are saved to the experiment's directory, if the same experiment is started again, an
 error will be thrown. If you need to restart an experiment, just remove the directory created for that experiment.


#### Steps
There are three steps to training a model:

1. Pretraining the plan predictor.
1. Pretraining the action generator.
1. Fine-tuning both components together.

To pretrain a plan predictor:

1. If you would like to change any of the hyperparameters specified in `agent/config`, modify 
`agent/scripts/pretrain_plan_predictor.sh`.
1. Run pretraining: `sh agent/scripts/pretrain_plan_predictor.sh`.
