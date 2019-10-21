#!/usr/bin/env bash
export EXPERIMENT_NAME="test_experiment_plan_predictor"

# TODO: Absolute import fixing
CUDA_VISIBLE_DEVICES=0 python3.7 agent/scripts/main.py \
                  --saved_game_dir="data/" \
                  --game_state_filename="agent/preprocessed/game_states.pkl" \
                  --save_dir="agent/experiments/" \
                  --experiment_name=${EXPERIMENT_NAME} \
                  --model_type=PLAN_PREDICTOR \
                  --pretrain_auxiliary_coefficient_intermediate_goal_probabilities=1. \
                  --pretrain_auxiliary_coefficient_final_goal_probabilities=1. \
                  --pretrain_auxiliary_coefficient_obstacle_probabilities=0.1 \
                  --pretrain_auxiliary_coefficient_avoid_probabilities=0.1 \
                  --pretrain_auxiliary_coefficient_trajectory_distribution=1.
