#!/usr/bin/env bash
export EXPERIMENT_NAME="test_experiment_action_generator"

CUDA_VISIBLE_DEVICES=0 python3.7 main.py \
                  --saved_game_directory="data/" \
                  --game_state_filename="agent/preprocessed/game_states.pkl" \
                  --save_dir="agent/experiments/" \
                  --experiment_name=${EXPERIMENT_NAME} \
                  --model_type=ACTION_GENERATOR
