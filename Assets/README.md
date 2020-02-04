# Setting up the Unity editor

1. Open the project in the main directory (`cerealbar`).
1. Open the scene:
    * `File > Open Scene`
    * Open `cerealbar/Assets/Scenes/Game.unity`
1. Change to using .NET 4.x
    * `File > Build Settings > Player Settings...`
    * Under `Configuration`, set `Scripting Runtime Version` to `.NET 4.x Equivalent`
    * This will require restarting the Unity editor.


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
