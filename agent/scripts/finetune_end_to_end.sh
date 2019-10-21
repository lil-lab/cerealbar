#!/usr/bin/env bash
export EXPERIMENT_NAME="test_experiment_finetuned"
export PLAN_PREDICTOR_FILEPATH="SET THIS PARAMETER TO YOUR BEST MODEL SAVE"
export ACTION_GENERATOR_FILEPATH="SET THIS PARAMETER TO YOUR BEST MODEL SAVE"

# TODO: Absolute import fixing
CUDA_VISIBLE_DEVICES=0 python3.7 agent/scripts/main.py \
                  --saved_game_dir="data/" \
                  --game_state_filename="agent/preprocessed/game_states.pkl" \
                  --save_dir="agent/experiments/" \
                  --experiment_name=${EXPERIMENT_NAME} \
                  --model_type=PLAN_PREDICTOR \
                  --end_to_end=True \
                  --aggregate_examples=True \
                  --generate_new_cards=True \
                  --finetune_auxiliary_coefficient_intermediate_goal_probabilities=1. \
                  --finetune_auxiliary_coefficient_final_goal_probabilities=1. \
                  --finetune_auxiliary_coefficient_obstacle_probabilities=0.1 \
                  --finetune_auxiliary_coefficient_avoid_probabilities=0.1 \
                  --finetune_auxiliary_coefficient_trajectory_distribution=1. \
                  --finetune_auxiliary_coefficient_implicit_actions=0.7 \
                  --pretrained_plan_predictor_filepath=${PLAN_PREDICTOR_FILEPATH} \
                  --pretrained_action_generator_filepath=${ACTION_GENERATOR_FILEPATH}
