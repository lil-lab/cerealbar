# Cereal Bar
Cereal Bar is a two-player web game designed for studying language understanding agents in collaborative interactions. This repository contains code for the game, a webapp hosting the game, the agent implementation, and recorded interactions in the game. 

The game, data, and agent implementation (architecture, learning, and evaluation) are described in the following paper:

Executing instructions in situated collaborative interactions. Alane Suhr, Claudia Yan, Jacob Schluger, Stanley Yu, Hadi Khader, Marwa Mouallem, Iris Zhang, and Yoav Artzi. To appear in EMNLP 2019. Print coming soon!

## Cereal Bar Game

### Unity Game

The directory `game/` contains the implementation of the Cereal Bar game in C#/Unity. The game can be built both for standalone playing (e.g., for replaying recorded interactions) and as a webapp (e.g., for hosting on a webpage).

### Webapp

The directory `webapp/` contains code to support hosting Cereal Bar on the web, either as a game between two human players or as a way to interact with a trained agent.

## Interaction Data

### Recorded Data

The directory `data/` contains recorded interactions of games played between two human players (which we used for training and evaluation) and between a human player and a trained agent (results of our evaluation).

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
