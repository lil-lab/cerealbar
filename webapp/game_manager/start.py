import sqlite3
import time
import webapp.database as db
import subprocess
import hashlib
from flask import request
import uuid
from flask_socketio import emit, join_room, leave_room

from webapp import socketio
from webapp.config import lobby_clients, lobby_clients_active, live_games, logger
from webapp.config import CerealRequest, SERVER_START_TIME, DATABASE_NAME, PASSID
from webapp.config import agent_clients, agent_clients_active, CURRENT_MATCH_MODE, agent_processes


@socketio.on('connect')
def on_connect():
    # Just write the client and a status to the clients thing
    db.write_client(request.sid, str(hashlib.md5(request.remote_addr.encode('utf-8')).hexdigest()),
                    request.environ[
        'REMOTE_PORT'])


@socketio.on('sendCredentials')
def parse_credentials(jsn):
    # This is a hashed worker ID. Look it up against the hash.
    worker_id = jsn['worker_id']
    if db.is_qualified(worker_id):
        # Check if the assignment ID is already used.
        if db.assignment_id_used(worker_id, jsn['assignment_id']):
            db.update_client_info(request.sid, worker_id, jsn['assignment_id'], 'Already Used Assignment ID')
            logger.debug('identified worker using assignment ID another time; SID=' + request.sid)
            emit('assignmentIdUsed')
        else:
            # Check for worker ID in list of currently-connected workers 
            if db.worker_connected(worker_id):
                db.update_client_info(request.sid, worker_id, jsn['assignment_id'], 'Already Connected to Game')
                logger.debug('identified already-connected worker ' + jsn['worker_id'] + '; SID=' + request.sid)
                emit('alreadyConnected')

            else:
                db.update_client_info(request.sid, worker_id, jsn['assignment_id'], 'Validated Connection')
                logger.debug('recognizing connected worker ' + jsn['worker_id'] + '; SID=' + request.sid)
                db.write_connection_event(request.sid, 'Connected and Validated Identity')
                emit('recognizedWorker')
    elif worker_id.startswith('agent'):
        db.update_client_info(request.sid, worker_id, jsn['assignment_id'], 'Agent Connected')
        logger.debug('recognized agent; SID=' + request.sid + '; ID=' + str(worker_id))
        emit('recognizedAgent')
        db.write_connection_event(request.sid, 'Connected with Agent ID')
    else:
        if worker_id:
            db.update_client_info(request.sid, worker_id, jsn['assignment_id'], 'Non-Recognized Worker')
            logger.debug('did not recognize connector as qualified worker; SID=' + request.sid)
            emit('unqualifiedWorker')
            db.write_connection_event(request.sid, 'Connected with Unrecognized Worker ID')
        else:
            db.update_client_info(request.sid, worker_id, jsn['assignment_id'], 'No-credentials Connection')
            logger.debug('did not recognize connector; SID=' + request.sid)
            db.write_connection_event(request.sid, 'Connected with No Credentials')


@socketio.on('verifyPasscode')
def verify_passcode(jsn):
    db.update_client_info(request.sid, PASSID, '', 'Passcode Connection')
    db.write_connection_event(request.sid, "Passcode Used")
    emit('checkPasscode', {'valid': jsn['passcode'] == PASSID})


@socketio.on('completeTutorial')
def complete_tutorial(jsn):
    sid = request.sid

    db.mark_tutorial_complete(sid, jsn['isLeader'], jsn['workerId'], jsn['assignmentId'])
    db.write_connection_event(sid, "Tutorial Complete")


@socketio.on('changedFocus')
def changed_focus(jsn):
    focus = jsn['data']
    db.write_connection_event(request.sid, 'Changed Focus to ' + str(focus))


@socketio.on('joinLobby')
def join_lobby(jsn):
    """Player joins lobby for partner matchmaking. 'lobby_clients' holds all
    players currently in queue to find a partner.
    """
    # Just put them in the lobby.
    worker_id = jsn['worker_id']

    my_request = CerealRequest(request.remote_addr, request.sid, worker_id, jsn['assignment_id'])

    if worker_id.startswith('agent'):
        agent_clients.put((time.time() - SERVER_START_TIME, my_request))
        agent_clients_active[request.sid] = True

    else:
        lobby_clients.put((time.time() - SERVER_START_TIME, my_request))
        lobby_clients_active[request.sid] = True

        logger.info('MATCHING WITH HUMAN? ' + str(CURRENT_MATCH_MODE.use_human))
        if not CURRENT_MATCH_MODE.use_human:
            # Spawn an agent client
            logger.debug('Spawning an agent client...')
            agent_uuid = 'agent_' + str(uuid.uuid4().hex)
            process = subprocess.Popen(['python3', '-m', 'webapp.agent', agent_uuid])
            agent_processes[agent_uuid] = process
            logger.debug('Spawned agent=' + agent_uuid + ', pid=' + str(process.pid))

    logger.debug("player joined lobby: " + str(my_request))

    db.write_connection_event(request.sid, "Join Lobby")

    # Each player's room is just their unique request debugrmation for now
    # Later on, when they are ready, they will enter their game's room
    join_room(my_request.sid)


@socketio.on('readyPressed')
def ready_pressed(jsn):
    """Recieved when player presses button to indicate they are ready to start.
    Game actually starts loading after both lobby_clients send this message, i.e. they
    are both ready.
    """
    logger.debug("%s from %s pressed ready", jsn["character"], jsn["gameId"])

    game_id = jsn["gameId"]
    try:
        game = live_games[game_id]
    except KeyError as e:
        logger.warn('Game ' + str(game_id) + ' not found in live games')
        return

    # Set ready, and also join the room actually corresponding to the in-play
    # game
    if jsn["character"] == "Human":
        game.set_human_ready()
        logger.debug('human joined room: ' + game.human_room())
        join_room(game.human_room())
        db.write_connection_event(request.sid, "Pressed Ready (Leader)")

    elif jsn["character"] == "Agent":
        game.set_agent_ready()
        logger.debug('agent joined room: ' + game.agent_room())
        join_room(game.agent_room())
        db.write_connection_event(request.sid, "Pressed Ready (Follower)")

    else:
        raise ValueError('Unrecognized character name: ' + jsn['character'])

    if game.both_ready():
        emit('startGame', room=game.human_room())
        emit('startGame', room=game.agent_room())

        # Mark the assignment IDs as used
        db.mark_assignment_id_used(game.human_id(), game.human_assignment_id())
        db.mark_assignment_id_used(game.agent_id(), game.agent_assignment_id())


@socketio.on('readyToStartGamePlay')
def start_gameplay(jsn):
    """Recieved when one player's game is loaded, so they are ready to start
    playing. Gameplay starts after both players send this message.
    """
    game_id = jsn["gameId"]
    requester_sid = request.sid
    logger.debug("player: " + requester_sid + " loaded the game " + game_id)

    db.write_connection_event(requester_sid, 'Game Loaded')

    try:
        game = live_games[game_id]
    except KeyError:
        logger.error('Game ' + str(game_id) + ' not found in live games')
        return

    if jsn['character'] == 'Human':
        game.set_human_loaded()
        partner_room = game.agent_room()
    elif jsn['character'] == 'Agent':
        game.set_agent_loaded()
        partner_room = game.human_room()
    else:
        raise ValueError('Unrecognized character type: ' + jsn['character'])

    if game.both_loaded():
        # need both players to be in the same room so we can send the
        # start msg in one emit, to get each player to recieve the message
        # as close to the same time as possible

        join_room(partner_room)
        logger.debug('sending start game play to my partner')
        emit('startGamePlay', room=partner_room)
        leave_room(partner_room)

        db.write_first_turn(game_id)


@socketio.on('init')
def init(jsn):
    """Record game information in initialInfo and logging initial states
    of both players.
    """
    seed = int(jsn['seed'])
    db.write_initial_info(seed, str(jsn['hexCellInfo']), str(jsn['propPlacementInfo']), str(jsn['cardInfo']))

    game_id = jsn['gameId']

    # If using a human-agent game, record this debugrmation to the agent.
    try:
        game = live_games[game_id]
    except KeyError:
        logger.error('Game ' + str(game_id) + ' not found in live games')
        return

    logger.debug('Received init! game using agent? ' + str(game.using_agent))
    if game.using_agent:
        # Send to the other player
        logger.debug('Sending initial debug to agent!')
        emit('initialMapInfo', jsn, room=game.agent_room())

    initial_pos = jsn["propPlacementInfo"][-1]["posV3"]
    initial_rot = float(jsn["propPlacementInfo"][-1]["rotV3"].split(",")[1].strip())

    database = sqlite3.connect(DATABASE_NAME)
    c = database.cursor()

    q = ('INSERT INTO movements (gameId, moveId, character, action, position, '
         'rotation, gameTime, serverTime, turnId) VALUES (?,?,?,?,?,?,?,?,?)')
    t = (game_id, -1, jsn["character"], "initial", initial_pos, initial_rot,
         "0", db.get_current_time(), -1)
    c.execute(q, t)
    database.commit()
    database.close()
