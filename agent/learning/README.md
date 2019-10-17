# Learning

## Metrics

We define several metrics that can be used to evaluate an agent's performance in the CerealBar game.

* `SEQUENCE_ACCURACY` compares a predicted sequence's equality to another sequence.
* `CARD_ACCURACY` compares whether the statuses and values of the cards on the board are as expected.
* `RELAXED_ENVIRONMENT_ACCURACY` requires card statuses and values to be as expected, and the agent to be within a 
certain distance of the goal location.
* `EXACT_ENVIRONMENT_ACCURACY` requires the environment status to be exactly as expected, including the agent 
location and position and card values and statuses.
* `AGENT_DISTANCE` is the agent's distance in hexes from the gold distance.
* `POSITION_PREFIX` is the proportion of states visited by the agent that were correct (of the gold action sequence).
* `SCORE` is the score of a game.
* `PROPORTION_FOLLOWED_CASCADING` is the proportion of instructions that were successfully followed by the agent in 
cascaded inference.
* `PROPORTION_VALID_CASCADING` is the proportion of final states that were valid (i.e., card statuses were expected) 
in cascaded inference.
* `PROPORTION_POINTS_CASCADING` is the proportion of the gold points that were achieved during cascaded inference.