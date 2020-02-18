# Starting and testing the server

1. Build the WebGL version of the game (see `game/` for instructions). Name it `Release`. The binary should go in 
`webapp/static/`.
1. Ensure you have a worker ID file. For testing purposes, you can create an empty file by doing `touch 
mturk/worker_ids.txt`.
1. Initialize the game database.

    `python -m webapp.init_db mturk/worker_ids.txt`
    
1. Start the game server.

    `python -m webapp.run`
    
1. Connect to the game. Because the game is two-player, you should connect in two windows. The default port is 8080. Go
 to `localhost:8080`.

1. Click `Find Partner!` in both windows. You should be automatically paired. 

1. To begin gameplay, click `Ready to Play Game`. The game map should load and the Leader's turn should begin.