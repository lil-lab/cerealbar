#!/usr/bin/env bash

export GAME_ID="ENTER GAME ID HERE"

python3.7 main.py --run_type=REPLAY \
                  --keep_track_of_turns=False \
                  --realtime=True \
                  --speed=0.2 \
                  --game_directory="data/" \
                  --saved_game_directory="data/" \
                  --game_state_filename="agent/preprocessed/game_states.pkl" \
                  --game_id=${GAME_ID}
