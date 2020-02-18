from time import gmtime, strftime
import sqlite3
import webapp.database as db
from flask import request
from flask_socketio import emit

from .. import socketio
from webapp.config import lobby_clients, lobby_clients_active, live_games, logger, DATABASE_NAME, agent_processes


def kill_agent(game_id):
    agent_id = db.get_agent_id_for_game(game_id)
    logger.debug('Trying to kill agent ' + str(agent_id))

    if not agent_id:
        logger.debug('Could not find agent ID for game ' + str(game_id))
    elif agent_id in agent_processes:
        # Kill the process
        process = agent_processes[agent_id]
        logger.debug('Killing process associated with agent=' + agent_id + ', pid=' + str(process.pid))
        process.kill()
        agent_processes.pop(agent_id)
    else:
        logger.debug('Could not find agent ' + agent_id + ' process')


@socketio.on('disconnect')
def disconnectEvent():
    """Recieved when a client exits from their game."""
    db.disconnect_client(request.sid, 'Disconnected')
    db.write_connection_event(request.sid, "Disconnected")

    if request.sid in lobby_clients_active and lobby_clients_active[request.sid]:  # If was in the lobby,
        logger.debug('Lobby client ' + request.sid + ' disconnected')
        db.write_connection_event(request.sid, "Disconnected from Lobby")
        db.disconnect_client(request.sid, 'Disconnected from Lobby')
        lobby_clients_active[request.sid] = False
        return

    # Find the game that this request was connected to
    request_is_human = False
    found_game = None
    for game_id, game in live_games.items():
        if game.human.sid == request.sid:
            request_is_human = True
            found_game = game
            logger.debug('Requester ' + request.sid + ' was human in game ' + str(game_id))
            break
        elif not game.using_agent and game.agent.sid == request.sid:
            found_game = game
            logger.debug('Requester ' + request.sid + ' was agent in game ' + str(game_id))
            break

    if not found_game:
        return

    # Log that they exited prematurely
    game_id = found_game.game_id

    if request_is_human:
        if found_game.using_agent:
            logger.debug('Removing game ' + str(game_id) + ' from live games; human from agent-human game.')
            db.disconnect_client(request.sid, 'Disconnected After Game')
            db.write_connection_event(request.sid, "Quit Game")

            # Check if in live games first -- might not be anymore if the partner
            # concurrently ended the game
            kill_agent(game_id)
            if game_id in live_games:
                # Get the agent ID
                live_games.pop(game_id)
        else:
            if found_game.agent_quit:
                logger.debug('Removing game ' + str(game_id) + ' from live games; both people quit.')
                db.disconnect_client(request.sid, 'Disconnected After Game')
                db.write_connection_event(request.sid, "Quit Game")

                # Check if in live games first -- might not be anymore if the partner
                # concurrently ended the game
                if game_id in live_games:
                    live_games.pop(game_id)
            else:
                logger.debug('Agent from game ' + str(game_id) + ' is still there.')
                found_game.set_human_quit()

                # Notify the agent that their partner left. Use the sid, rather than
                # the game room, because they may not have pressed that they are
                # ready yet.
                emit('partnerLeft', room=found_game.agent.sid)

                # If the game hasn't started, remove it.
                if not found_game.both_loaded():
                    logger.debug("Completely removed game " + str(game_id) +
                                 " because it has not started or loaded for both players.")
                    live_games.pop(game_id)
                    db.disconnect_client(request.sid, 'Disconnected Before Loading Game')
                    db.write_connection_event(request.sid, "Quit Game Prematurely (Before Loading)")
                else:
                    db.disconnect_client(request.sid, 'Disconnected During Game')
                    db.write_connection_event(request.sid, "Quit Game Prematurely (Ongoing Game)")
    else:
        if found_game.using_agent:
            raise ValueError('(game ID: ' + str(game_id) +
                             ' When using the agent, the requester who disconnects should be a human.')
        if found_game.human_quit:
            logger.debug('Removing game ' + str(game_id) + ' from live games; both people quit.')
            db.disconnect_client(request.sid, 'Disconnected After Game')
            db.write_connection_event(request.sid, "Quit Game")

            # Check if in live games first -- might not be anymore if the partner
            # concurrently ended the game
            if game_id in live_games:
                live_games.pop(game_id)
        else:
            logger.debug('Human from game ' + str(game_id) + ' is still there.')
            found_game.set_agent_quit()

            # Notify the agent that their partner left.
            emit('partnerLeft', room=found_game.human.sid)

            # If the game hasn't started, remove it.
            if not found_game.both_loaded():
                logger.debug("Completely removed game " + str(game_id) +
                             " because it has not started or loaded for both players.")
                live_games.pop(game_id)
                db.disconnect_client(request.sid, 'Disconnected Before Loading Game')
                db.write_connection_event(request.sid, "Quit Game Prematurely (Before Loading)")
            else:
                db.disconnect_client(request.sid, 'Disconnected During Game')
                db.write_connection_event(request.sid, "Quit Game Prematurely (Ongoing Game)")


@socketio.on('gameOver')
def gameOver(jsn):
    """Recieved when the game ends for a pair of players."""
    game_id = jsn["gameId"]

    ### Make sure that the game is either in the live games, or has an entry
    # in the database already.

    db.write_connection_event(request.sid, "Game Ended Normally")

    if game_id in live_games:
        logger.debug('game over (ID: ' + str(game_id) + ')')

        db.write_final_turn(game_id, jsn["time"])
        db.write_game_end(game_id, jsn["score"])

        live_games.pop(game_id)
        kill_agent(game_id)
    else:
        # If it's not, make sure that the score has been set and accurately
        # reflects what was in the database already.
        expected_score = db.get_game_score(game_id)

        if not expected_score == jsn["score"]:
            logger.warn("Didn't find game " + game_id + " in live games, but the score was not "
                        "expected! (database) " + str(expected_score) + "; (client) " + str(jsn["score"]))
