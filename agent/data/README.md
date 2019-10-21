# Data for training

This directory contains utilities associated with processing the CerealBar data for training and evaluation purposes.

## Dataset splits

We enumerate a few types of dataset splits:

* `TRAIN`: All original training data.
* `DEV`: All original development data.
* `TEST`: All original test data.
* `VALIDATION`: A held-out subset of the training data used for early stopping during training.
* `UPDATE`: A subset of the training data actually used to update model parameters (i.e., `TRAIN - VALIDATION`).
* `SPECIFIED`: A subset of all data that is expected to be specified by the user. This can be used for debugging (e.g., evaluating on specific examples).

## Gameplay actions

The original game data (stored in JSON files) can be processed into a sequence of `GameplayAction` objects that 
specify not only the exact movements taken by the players, but also things like ending turns and sending instructions.

There are four types of gameplay actions. All actions have a time.

* `MovementAction` is an action (rotating or moving backwards/forward). This action is taken by either agent. 
Alongside it is stored the change in state of the game when the movement was taken (e.g., new card values).
* `InstructionAction` is an action of sending an instruction by the leader. It contains not only the original 
instruction, but a version tokenized according to the specified `DataArgs`. It also contains the movements taken by 
the follower to follow this instruction.
* `EndTurnAction` is an action taken by either player that simply indicates they have ended their turn (and the 
method by which they ended it).
* `FinishCommandAction` is an action taken only by the follower indicating they have marked a command as complete. It
 also includes the state of the world when the instruction was completed.