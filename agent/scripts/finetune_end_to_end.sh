#!/usr/bin/env bash
export EXPERIMENT_NAME="finetuned"
export PLAN_PREDICTOR_FILEPATH="agent/experiments/plan_predictor/best_save.pt"
export ACTION_GENERATOR_FILEPATH="agent/experiments/action_generator/best_save.pt"

CUDA_VISIBLE_DEVICES=0 python -m agent.scripts.main \
                  --saved_game_dir="data/" \
                  --game_state_filename="agent/preprocessed/game_states.pkl" \
                  --save_dir="agent/experiments/" \
                  --experiment_name=${EXPERIMENT_NAME} \
                  --model_type=ACTION_GENERATOR \
                  --end_to_end=True \
                  --aggregate_examples=False \
                  --maximum_generation_length=25 \
                  --generate_new_cards=True \
                  --full_observability=True \
                  --finetune_auxiliary_coefficient_intermediate_goal_probabilities=1. \
                  --finetune_auxiliary_coefficient_final_goal_probabilities=1. \
                  --finetune_auxiliary_coefficient_obstacle_probabilities=0.1 \
                  --finetune_auxiliary_coefficient_avoid_probabilities=0.1 \
                  --finetune_auxiliary_coefficient_trajectory_distribution=0.04 \
                  --use_trajectory_distribution=True \
                  --use_goal_probabilities=True \
                  --use_obstacle_probabilities=True \
                  --use_avoid_probabilities=True \
                  --evaluation_results_filename="training_inference.log" \
                  --pretrained_plan_predictor_filepath=${PLAN_PREDICTOR_FILEPATH} \
                  --pretrained_action_generator_filepath=${ACTION_GENERATOR_FILEPATH}
