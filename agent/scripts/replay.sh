#!/usr/bin/env bash

export GAME_ID="aa786e30502245f8918a782437d6d95f"

python -m agent.scripts.main \
    --run_type=REPLAY \
    --keep_track_of_turns=False \
    --realtime=True \
    --speed=0.2 \
    --game_directory="data/" \
    --game_id=${GAME_ID}
