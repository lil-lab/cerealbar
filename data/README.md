# Cereal Bar interaction data

This directory contains data collected between two human 
players (used for training and evaluation) and between a
human and an agent player (results of our evaluation).

## JSON files

We use JSON files to store each interaction. Its format is
a dictionary mapping from game ID (uniquely identifying
32-byte string) to another dictionary containing the game
information.

### Basic structure
The game dictionary has the following keys:

* `game_id`: The same game ID mentioned above: a uniquely-
identifying 32-byte string.
* `seed`: The seed number used to generate the game map in
Unity.
* `num_cards`: The number of cards on the board in the game.
All games use 21 cards.
* `leader_id`: An anonymized Turker ID (consistently
anonymized across all data).
* `actions`: A list of actions taken by both players in the
game.
* `split`: Which split of the data the game is from.
* `score`: The final score of the game.

Each action is represented as a dictionary. Though the
 structure of each dictionary is slightly different 
 depending on the action type, all actions have the 
 following fields:
 
* `type`: Determines the type of action, e.g., `movement`,
`instruction`. This determines the structure of the action
dictionary.
* `time`: The exact time that the action was recorded to 
the database on the server. When processing an action
from a player client, the server first processes it by
 writing it to the database, then sends the message
 to the other player client (i.e., this is the soonest
 action time we can record.) See below for discussion of
accuracy.
* `game_time`: The number of seconds since the game began.
* `turn_id`: The index of the turn in which the action was
taken. The value may be `-1` for actions taken before the
game started (e.g., the action describing the starting
location of each player.)

The `actions` field is sorted by `time`, but this does not
guarantee that the actions were originally executed in this
order due to possible lag between players. In practice,
this happens very rarely (we only go off of the `time`
field, and didn't notice any issues). 
 

### `movement` actions
Type `movement` actions have the following additional
fields. The first two `movement` actions only show the 
initial position of both players.

* `character`: The player taking the action, either `Agent` 
or `Human`.
* `action`: The movement taken, which is one of `initial` 
(for the first movement), `MF` (move forward), `RR` (rotate
right), `RL` (rotate left), `MB` (move backward).

The following fields of `movement` are stored for 
redundancy and quick data analysis only. Due to timing
issues, sometimes the information contained in them
is incomplete or slightly incorrect. When replaying 
games or training and evaluating an agent, we strongly suggest 
re-simulating the games in Unity (as described in the 
`agent/` directory) and getting a pickled version of all
game states for all games. The re-simulation will only
consider the `time`, `character`, and `action` fields, so
the following fields will basically be recomputed. 

* `move_id`: The index of the movement in the list of all
movements by both players (`-1` for both first `movement`
actions).
* `card_result`: Whether the action taken resulted in a 
card changing its status. This is a string in the format
`CHANGE NUMBER COLOR SHAPE`, e.g., `ACTIVATED 1 card_pink Torus`.
* `set_result`: Whether the action resulted in a set being
made, and if so, some information about the new set. This
is a dictionary that has up to three fields: `made_set`, 
which is `true` or `false`; `new_score`, which is the new
game score if `made_set` is `true`, and `new_cards`, which is
a list of new card properties (number, color, and shape) if
`made_set` is `true`.
* `resulting_position`: The position of the agent
after executing the action.
* `reuslting_rotation`: The rotation of the agent
after executing the action.
* `instruction_id`: The index of the instruction that this
movement is aligned with.


### Turn actions
`begin_turn` and `end_turn` actions indicate that a player
has ended or begun their turn. It has one extra field:

* `character`: The player beginning or ending the turn, 
either `Agent` or `Human`.
* The `end_turn` action has an extra field `end_method`
indicating how the player ended their turn, e.g.,
`Ran Out of Moves` or `game ended`.


### `instruction` actions
Type `instruction` actions have the following additional
fields. Note that the `time` indicates when the instruction
was added to the instruction queue, not necessarily when
the follower first sees or can act on the instruction. Only 
the leader can give instructions.

* `instruction`: The instruction given by the leader.
* `instruction_id`: The index of the instruction
* `completed`: Whether the follower marked the instruction
as completed. The last few instructions may be incomplete
if the game ended before the follower could get to them.

Similar to above, the following field is stored for
redundancy and data analysis only and will be re-computed
when re-simulating the games.

* `aligned_actions`: A list of follower actions that align
with this instruction.

### `finish command` actions
Type `finish command` actions indicate when the follower
marked a particular command as finished. It has the following
additional field:

* `instruction_id`: The instruction index being marked
as complete.


## Preprocessed game states

## TODO

- [ ] `turn_id` field for `finish command`
- [ ] Remove fields like `card_result` and `set_result` in instruction
- [ ] Anonymize Turker IDs
- [x] Make sure that the game states file doesn't have any
PII for turkers
- [x] Add in the preprocessed game state pickle file
