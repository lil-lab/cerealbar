# Shell scripts

We provide a number of scripts to replicate our experiments and browse the data using `main.py`. Most arguments are not 
set (see `config/` for a description of all possible arguments to `main.py`) because the defaults are what we used in
 our experiments. If you would like to change a hyperparameter, make sure to add the correct argument here.
 
We tested these scripts using bash, but you can adapt them to a scripting language of your choice.

* `pretrain_plan_predictor.sh` pretrains the plan predictor with gold plans as output.
* `pretrain_action_generator.sh` pretrains the action generator with gold plans as input.
* `finetune_end_to_end.sh` finetunes the two components together with pretrained components.
* `evaluate.sh` evaluates a model.
* `replay.sh` replays recorded game data.

The replay and evaluation scripts are particularly customizable (e.g., if you wish to run on Unity, or replay a 
different set of games than specified in those scripts).

# TODO 

- [ ] Add a script for creating the `game_states.pkl` file
