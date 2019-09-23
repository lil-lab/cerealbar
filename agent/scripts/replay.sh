#!/usr/bin/env bash
# TODO: Clean up the arguments here
python3.7 main.py --run_type=REPLAY \
                  --game_port=3706 \
                  --keep_track_of_turns=False \
                  --realtime=True \
                  --speed=0.2 \
                  --game_dir="/Users/alsuhr/Documents/research/my_projects/cereal-bar/mturk/games/data/" \
                  --saved_game_dir="../mturk/games/data/" \
                  --game_file_suffixes '1_27', '2_2', '2_3', 'junior2_3', '4_15', '4_16', 'junior4_15', 'junior4_16', '5_14' \
                  --game_state_filename="preprocessed/game_states.pkl" \
                  --game_id="aa786e30502245f8918a782437d6d95f" \
                  --save_dir="experiments/"
