# Game simulation

This directory contains classes and utilities for interfacing Python with the CerealBar game, for example during 
replay of recorded games, or evaluation of a trained model. 

## `Game`, `UnityGame`, and `PythonGame`

`Game` is an abstract class that keeps track of gameplay information.
Most of the gameplay (e.g., tracking whose turn it is) is
 left to the responsibility of Python when using the Unity standalone version, so these classes keep track of this 
 information instead. `UnityGame` is a game that connects to the Unity standalone, while `PythonGame` is a version 
 that implements the game entirely in Python. 
 
## Connecting to the standalone

`ServerSocket` begins and closes a connection to the Unity standalone (as well as launches and closes the app). It 
can be used to send information to, and retrieve information from, the Unity standalone.

## Replaying recorded games

`replay.py` offers an interface to replay recorded games from raw data.

# Computing observability

TODO: describe how to build the game so that you can compute observability (e.g., setting SCOPE to non-transparent)