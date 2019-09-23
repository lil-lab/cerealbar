#!/usr/bin/env bash
# TODO: Clean up the arguments here
CUDA_VISIBLE_DEVICES=0 python3.7 main.py --game_port=3706 \
                  --saved_game_dir="../mturk/games/data/" \
                  --game_file_suffixes "1_27" "2_2" "2_3" "junior2_3" \
                  --game_state_filename="preprocessed/game_states.pkl" \
                  --leader_steps_per_turn=5 \
                  --follower_steps_per_turn=10 \
                  --initial_num_turns=100 \
                  --output_seq_len=25 \
                  --minimum_score 0 \
                  --run_type=EVAL \
                  --held_out_prop 0.05 \
                  --action_delay 0. \
                  --save_dir="experiments/" \
                  --experiment_name="finetune_aggregate_0.7_1" \
                  --save_file="model_17_score.pt" \
                  --reset_after_instruction=False \
                  --use_unity=False \
                  --split=DEV
