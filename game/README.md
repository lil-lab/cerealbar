# Setting up the Unity editor

1. Open the project in the this directory (`game`). It's important to open in this directory as all of the project 
files (e.g., settings) are included in this directory.
1. Open the scene:
    * `File > Open Scene`
    * Open `game/Assets/Scenes/Game.unity`


# Building the game

1. For the WebGL version
    * `File > Build Settings > Player Settings...`
    * Select platform `WebGL`
    * Build with `Build`. It can take several minutes to build.
1. For the standalone version
    * `File > Build Settings > Player Settings...`
    * Select platform `PC, Mac & Linux Standalone`
    * Under `Scripting Defined Symbols`, type `SIMULATING`
    * Build with `Build`. It will build relatively quickly.


# Our environment

We developed the game on MacOS 10.14.6 using Unity editor 2018.2.17f1.


# Scripts organization (contents of `Scripts/`)

* `CardGen` -- randomly generating and placing cards on the board.
* `Communication` -- communication between the players when playing on the web version.
* `Functions` -- classes containing various types of data (e.g., what a player can see). 
* `GameElements` -- keeps track of the game, including the score, time, and valid sets.
* `JSON_stuff` -- serializable classes for various information about the game (e.g., a player's position/rotation)
* `MapGen` -- for generating the map (including terrain, props)
* `Movement` -- various types of movement players can take between hexes. We use `HexToHexControl.cs`, the others are probably obselete.
* `PL` -- formal language used to control the players. This is obselete.
* `Plugins` -- WebGL related things. `Plugins/web-socket.jslib` contains Javascript that interacts with the client's browser and the server during web-based gameplay.
* `Python` -- interface to a python backend that can control the players (for standalone playing).
* `ScriptableObjects` -- databases for object types (e.g., trees). See readme.
* `Turns` -- controls the switching between player turns.
* `Tutorial` -- code for tutorial of the two players.
* `UI` -- UI for various parts of the game.
