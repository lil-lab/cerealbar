# Environment

This directory contains classes and functions for loading
environment information as it is shared from Unity into a
consistent format, and using and modifying this information.

## Position and rotation

Objects in the map have a position and rotation. We implement
operators to convert from what Unity provides to our format.

## Terrain

Each hex in the map is defined with a `Terrain`, some of which
can't be moved through by the players.

## Environment objects

There are two superclasses of objects:

* `EnvironmentObject` has a position and an object type.
* `RotatableObject` additionally has a rotation.

All objects implement equality and string operators.
Each object has a type (`ObjectType`) that defines which
subclass it is implemented as. This includes the following:

* `Agent`, representing the leader and follower players,
whose position and rotation can be updated as the agent is moving.
* `Card`, representing cards on the board. Cards have 
properties related to their color (`CardColor`), shape
(`CardShape`), count (`CardCount`), and selection (`CardSelection`).
Its selection can be updated (when an agent moves on top
of it). Its position can also be updated (e.g., for generating)
new cards to add to the board).
* `Hut` comprises the house objects, which have a color (`HutColor`).
* `Plant` comprises short plants (i.e., not trees), and have a
plant type (`PlantType`). Similarly, `Tree` comprises all trees, 
each of which has a tree type (`TreeType).
* Several structures like `Windmill`, `Tower`, `Tent`, and `Lamppost`
don't have any special properties.

All objects are obstacles, except `Agent` and `Card`.

`util.py` includes functions for converting from the information
specified by Unity to these environment objects.

## Actions

`AgentAction` comprises all six possible actions for an
agent to take:

* `MF`: Move forward
* `MB`: Move backward
* `RR`: Rotate right
* `RL`: Rotate left
* `START`: Start the current sequence of actions
* `STOP`: Stop the current sequence of actions

The affects of agent actions on an environment are described
in the `simulation/` directory.