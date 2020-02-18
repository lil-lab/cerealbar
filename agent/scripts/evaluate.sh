#!/usr/bin/env bash

export EXPERIMENT_NAME="fixed_action_generator_partial_observability"
export SAVE_FILE="model_12_card.pt"

CUDA_VISIBLE_DEVICES=0 python -m agent.scripts.main \
                  --saved_game_dir="data/" \
                  --game_state_filename="agent/preprocessed/game_states.pkl" \
                  --save_dir="agent/experiments/" \
                  --initial_number_of_turns=100 \
                  --maximum_generation_length=25 \
                  --run_type=EVALUATE \
                  --experiment_name=${EXPERIMENT_NAME} \
                  --save_file=${SAVE_FILE} \
                  --reset_after_instruction=True \
                  --action_delay=0. \
                  --evaluation_results_filename="debug_evaluation.log" \
                  --split=DEV \
                  --evaluate_with_pretrained_plan_predictor_path="agent/experiments/fixed_plan_predictor/model_16_bestacc.pt"
