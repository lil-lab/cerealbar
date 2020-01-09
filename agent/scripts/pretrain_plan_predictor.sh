#!/usr/bin/env bash
export EXPERIMENT_NAME="plan_predictor"

CUDA_VISIBLE_DEVICES=0 python -m agent.scripts.main \
                  --saved_game_dir="../cereal-bar/official_data/" \
                  --game_state_filename="agent/preprocessed/game_states.pkl" \
                  --save_dir="agent/experiments/" \
                  --experiment_name=${EXPERIMENT_NAME} \
                  --model_type=PLAN_PREDICTOR \
                  --pretrain_auxiliary_coefficient_intermediate_goal_probabilities=1. \
                  --pretrain_auxiliary_coefficient_final_goal_probabilities=1. \
                  --pretrain_auxiliary_coefficient_obstacle_probabilities=0.1 \
                  --pretrain_auxiliary_coefficient_avoid_probabilities=0.1 \
                  --pretrain_auxiliary_coefficient_trajectory_distribution=0.04 \
                  --full_observability=True
