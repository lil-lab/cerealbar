#!/usr/bin/env bash

export EXPERIMENT_NAME="test_experiment_finetuned"
export SAVE_FILE="SET THIS PARAMETER TO A MODEL SAVE"

CUDA_VISIBLE_DEVICES=0 python3.7 main.py \
                  --saved_game_dir="data/" \
                  --game_state_filename="agent/preprocessed/game_states.pkl" \
                  --save_dir="agent/experiments/" \
                  --initial_num_turns=100 \
                  --run_type=EVALUATE \
                  --experiment_name=${EXPERIMENT_NAME} \
                  --save_file=${SAVE_FILE} \
                  --reset_after_instruction=False \
                  --split=DEV
