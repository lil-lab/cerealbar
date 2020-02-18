var WebSocketPlugin = {
  // Global variables.
  $gVar: {},

  // Initialize web socket connection.
  Init: function() {
    // Get the worker ID and assignment ID from the header if possible
    var param = {};
    var s = window.parent.location.search.substring(1).split('&');
    for (var i=0; i < s.length; ++i){
      var parts = s[i].split('=');
      param[parts[0]] = parts[1];
    }

    gVar.workerId = "";
    if ("workerId" in param) {
        gVar.workerId = md5(param["workerId"]);
        console.log("Set worker ID as " + gVar.workerId);
    }


    gVar.assignmentId = "";
    if ("assignmentID" in param) {
        gVar.assignmentId = param["assignmentID"];
    }

    // Connect using the worker and assignment ID?
    var socket_connection = 'http://' + document.domain + ':' + location.port;
    console.log('connecting to ' + socket_connection);
    
    gVar.webSocket = io.connect(socket_connection);
    gVar.webSocket.emit('sendCredentials', {'worker_id': gVar.workerId,
                             'assignment_id': gVar.assignmentId });

    gVar.gameStarted = false;
    gVar.gameLoaded = false;
    gVar.gameId = -1;
    gVar.moveId = -1;
    gVar.numCards = -1;
    gVar.instructionId = -1;
    gVar.currInstrIdx = 0;
    gVar.character = null;
    gVar.turnId = 0;
    gVar.qId = "";

    // Received when an initial connection is recognized as a worker.
    gVar.webSocket.on('recognizedWorker', function() {
        console.log('You were recognized as a MTurk worker. Welcome!');

        // Worker was automatically recognized, so tell the game that.
        gameInstance.SendMessage('Start', 'ValidateGameAccess', 'Game');
    });

    gVar.webSocket.on('unqualifiedWorker', function() {
        console.log('You were recognized as a worker, but not a qualified worker.');
        var msg = 'Qual+' + gVar.workerId;
        gameInstance.SendMessage('Start', 'ValidateGameAccess', msg);
    });

    gVar.webSocket.on('alreadyConnected', function() {
        console.log('You are already connected to the game in another tab');

        gameInstance.SendMessage('Start', 'AlreadyConnected');
    });

    gVar.webSocket.on('assignmentIdUsed', function() { 
        console.log('You already used this assignment ID');

        gameInstance.SendMessage('Start', 'AssignmentIDUsed');
    });

    // Received in response to sending a passcode to check on the server.
    gVar.webSocket.on('checkPasscode', function(json) {
        var msg = json['valid'] ? 'Game' : 'Invalid';
        gameInstance.SendMessage('Start', 'ValidateGameAccess', msg);
    });

    // Received from server in response to sending 'joinLobby', which happens
    // after client joins the lobby of looking for a partner.
    gVar.webSocket.on('initGame', function(json) {
      console.log('initGame received:', json);
      gVar.character = json["character"];
      gVar.gameId = json["gameId"];
      gVar.seed = json['seed'];
      gVar.numCards = json['num_cards'];

      // For now, completely disable fast paths.
      gameInstance.SendMessage('GameManager','SetPaths','Normal');
      gameInstance.SendMessage('GameManager', 'SetNumCards', gVar.numCards);
      gameInstance.SendMessage('GameManager', 'SetSeed', gVar.seed.toString());
      gameInstance.SendMessage('GameManager', 'SetCharacter', gVar.character);
    });

    // Received from server when initially matched with a partner for gameplay.
    gVar.webSocket.on('lobbyReady', function() {
      console.log('lobbyReady received');
      gameInstance.SendMessage('GameManager', 'LobbyReady');
    });

    // Received after both (already matched) players press the button saying
    // they are ready to play, sending 'readyPressed'.
    gVar.webSocket.on('startGame', function() {
      console.log('startGame received');

      // Make sure not to send the StartGame message twice, if for whatever
      // reason both players sent it.
      if (!gVar.gameStarted) {
          gameInstance.SendMessage('GameManager', 'StartGame');
          gVar.gameStarted = true;
      } else {
          console.log('(but ignoring; game is already started');
      }

    });

    // Received after both players games have fully loaded (i.e. both players
    // have sent 'readyToStartGamePlay' to the server)
    gVar.webSocket.on('startGamePlay', function(json) {
      	console.log('startGamePlay received');

        if (!gVar.gameLoaded) {
            gameInstance.SendMessage('GameManager', 'StartGamePlay');
            gVar.gameLoaded = true;
        } else {
            console.log('(but ignoring; game is already loaded');
        }
    });

    // Received when other player moves, so this client can update the other
    // character's position in their version of the game.
    gVar.webSocket.on('movement', function(json) {
      if (json["character"] != gVar.character) {
      	console.log('movement received: ', json);
      	gameInstance.SendMessage('GameManager', 'ExternalMovement', json["type"]);
        gVar.moveId = json["moveId"]
      }
    });

    // Received when the other player sends this player an instruction.
    gVar.webSocket.on('instruction', function(json) {
      console.log('instruction received: ', json);
      gameInstance.SendMessage('Command Center', 'StoreCommand', json['content']);
    });

    gVar.webSocket.on('finishedCommand', function(json) {
      console.log('follower finished command: ', json);
      gameInstance.SendMessage('Command Center', 'ReceiveFinishCommand', json['content']);
    });

    // Received when the player's partner quits the game.
    gVar.webSocket.on('partnerLeft', function() {
      console.log('Partner left the game!');
      gameInstance.SendMessage('GameManager','PartnerLeft');
    });

    // Received after a player times out.
    gVar.webSocket.on('reset', function(json) {
      console.log('Resetting game');
      gameInstance.SendMessage('GameManager','Reset');
      gVar.gameStarted = false;
      gVar.gameLoaded = false;
      gVar.gameId = -1;
      gVar.moveId = -1;
      gVar.instructionId = -1;
      gVar.currInstrIdx = 0;
      gVar.character = null;
      gVar.turnId = 0;
    });

    // Received when turn changes from partner's turn to this player's turn.
    gVar.webSocket.on('yourTurn', function() {
      gameInstance.SendMessage("GameManager", "GetTurn");
      gVar.turnId += 1;
    });

    // Received in to initialize simulation mode.
    gVar.webSocket.on('initReplay', function(json) {
      console.log('initReplay received: ', json);
      // console.log("seed: " + json["seed"].toString());
      // console.log("instructions: " + json["instructions"].join('|').toString());
      // console.log("moves: " + json["moves"].join('|').toString());

      gameInstance.SendMessage('GameManager', 'StartReplay', json["seed"].toString());
      gameInstance.SendMessage('GameManager', 'ReplayInstructions', json["instructions"].join("|").toString());
      gameInstance.SendMessage('GameManager', 'ReplayMoves',json["moves"].join("|").toString());
      });
  },

  SetTag: function(character) {
    var charBuf = Pointer_stringify(character);
    gVar.character = charBuf;
  },

  // Sets that an ID has been used because a tutorial is complete.
  CompleteTutorial: function(isLeader) {
    var json = { 'isLeader': isLeader, 'workerId': gVar.workerId, 'assignmentId': gVar.assignmentId};
    gVar.webSocket.emit('completeTutorial', json);
  },

  QueryPasscode: function() {
      var passcode = prompt("Please enter your passcode (FOR DEBUGGING ONLY):");
      if(passcode === null)
        return;
      var bufSize = lengthBytesUTF8(passcode) + 1;
      var buf = _malloc(bufSize);
      stringToUTF8(passcode, buf, bufSize);
      var json = { 'passcode': passcode};
      gVar.webSocket.emit('verifyPasscode', json);
  },

  // Main method for sending data to the server.
  SockSend: function(route, msg) {
    // Convert data to Javascript string.
    var routeBuf = Pointer_stringify(route);
    var msgBuf = Pointer_stringify(msg);

    console.log("Sending:", routeBuf, msgBuf);
    var json = JSON.parse(msgBuf);

    if(routeBuf == "movement") {
      if (json["character"] != gVar.character) {
        return;
      }
      gVar.moveId += 1;
    }
    if (routeBuf == 'yourTurn') {
      gVar.turnId += 1;
      if (json["character"] != gVar.character) {
        return;
      }
    }
    if(routeBuf == "instruction") {
      gVar.instructionId += 1;
      gVar.moveId += 1;
      json["instructionId"] = gVar.instructionId;
    }

    if (routeBuf == "finishedCommand") {
      gVar.currInstrIdx += 1;
      gVar.moveId += 1;
      json["currInstrIdx"] = gVar.currInstrIdx;
    }
    if (routeBuf == "changedFocus") {
        console.log("HELLO, changed focus " + json);
    }

    json["moveId"] = gVar.moveId;
    json["gameId"] = gVar.gameId;
    json["character"] = gVar.character;
    json["turnId"] = gVar.turnId;
    json["worker_id"] = gVar.workerId;
    json["assignment_id"] = gVar.assignmentId;
    gVar.webSocket.emit(routeBuf, json);
  },
};

autoAddDeps(WebSocketPlugin, '$gVar');
mergeInto(LibraryManager.library, WebSocketPlugin);
