# This repo is under construction and the resources described below should be available soon!

# Cereal Bar
Cereal Bar is a two-player web game designed for studying language understanding agents in collaborative interactions. This repository contains code for the game, a webapp hosting the game, the agent implementation, and recorded interactions in the game. 

The game, data, and agent implementation (architecture, learning, and evaluation) are described in the following paper:

Executing instructions in situated collaborative interactions. Alane Suhr, Claudia Yan, Jacob Schluger, Stanley Yu, Hadi Khader, Marwa Mouallem, Iris Zhang, and Yoav Artzi. To appear in EMNLP 2019. Print coming soon!

## Setup

We recommend using the same virtual environment for all aspects of the project. We use Python 3.7.0. You can set this up
 by doing:

1. Create a virtual environment for python 3.7 called `venv`: `python3.7 -m venv venv`
1. Install the requirements: `pip install -r requirements.txt`
1. Activate the virtual environment: `. venv/bin/activate`


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

## TODO

- [ ] Add a section describing how to do different things with this code. E.g., running the game, or training an agent, etc.
- [ ] Nicer data browser.