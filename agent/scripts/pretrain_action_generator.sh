#!/usr/bin/env bash
export EXPERIMENT_NAME="action_generator"

CUDA_VISIBLE_DEVICES=0 python -m agent.scripts.main \
                  --saved_game_directory="data/" \
                  --game_state_filename="agent/preprocessed/game_states.pkl" \
                  --save_dir="agent/experiments/" \
                  --experiment_name=${EXPERIMENT_NAME} \
                  --maximum_generation_length=25 \
                  --model_type=ACTION_GENERATOR \
                  --full_observability=True \
                  --use_goal_probabilities=True \
                  --use_trajectory_distribution=True \
                  --use_avoid_probabilities=True \
                  --use_obstacle_probabilities=True
