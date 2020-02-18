from flask import request
from flask_socketio import emit
from webapp import socketio
from webapp.config import logger, partner_room, get_game
import webapp.database as db


@socketio.on('debug')
def log_debug_msg(jsn):
    message = jsn['data']
    db.write_debug_log(jsn['gameId'], request.sid, message)


@socketio.on('movement')
def movement(jsn):
    """Recieved when a player moves. Records the movement in the database, and
    sends the movement to the player's partner so they can update their instance
    of the game accordingly.
    """
    game_id = jsn["gameId"]
    character = jsn["character"]
    db.write_movement(jsn)

    game = get_game(game_id)
    if not game:
        raise ValueError('Game not found: ' + str(game_id))
    emit('movement', jsn, room=partner_room(character, game_id))


@socketio.on('yourTurn')
def switch_turn(jsn):
    """Recieved when one player ends their turn. Logs this in the database and
    sends in to the player's partner to give them the turn."""
    character = jsn["character"]
    game_id = jsn["gameId"]
    db.write_turn_switch(jsn)

    logger.debug("(game ID: " + str(game_id) + ") " + character + " ending turn " + str(jsn["turnId"]))

    game = get_game(game_id)
    if not game:
        raise ValueError('Game not found: ' + str(game_id))
    emit('yourTurn', room=partner_room(character, game_id))


@socketio.on('result')
def result(jsn):
    """Recieved when one player collects a card. Logs this in the database"""
    logger.debug("(game ID: " + jsn["gameId"] + ") card result: " + str(jsn))
    db.write_card_selection(jsn['gameId'], jsn['moveId'], jsn['card'], jsn['result'])


@socketio.on('set')
def card_set(jsn):
    """Recieved when one player makes a set. Logs this in the database"""
    game_id = jsn['gameId']
    logger.debug("(game ID: " + game_id + ") set made: " + str(jsn))

    db.write_set(jsn['gameId'], jsn['moveId'], jsn['score'], jsn['cards'])

    game = get_game(game_id)
    if not game:
        raise ValueError('Game not found: ' + str(game_id))
    if game.using_agent:
        my_partner_room = partner_room(jsn['character'], game_id)
        emit('set', jsn, room=my_partner_room)


@socketio.on('instruction')
def instruction(jsn):
    """Recieved when one leader sends an instruction to their follower."""
    character = jsn['character']
    if character == 'Agent':
        raise ValueError('Agent should not be sending commands!')

    game_id = jsn['gameId']

    db.write_instruction(game_id,
                         jsn['moveId'],
                         jsn['instructionId'],
                         jsn['content'],
                         jsn['time'],
                         jsn['turnId'])

    game = get_game(game_id)
    if not game:
        raise ValueError('Game not found: ' + str(game_id))
    my_partner_room = partner_room(character, game_id)
    emit('instruction', jsn, room=my_partner_room)
    logger.debug('(game ID: ' + game_id + ') instruction sent to room ' + str(my_partner_room) + ': ' +
                 jsn['content'])


@socketio.on('finishedCommand')
def finished_command(jsn):
    """Received when the follower finishes an instruction."""
    character = jsn['character']
    if character == 'Human':
        raise ValueError('Human should not be finishing commands!')
    game_id = jsn['gameId']
    logger.debug('(game ID: ' + game_id + ') follower finished a command')

    emit('finishedCommand', jsn, room=partner_room(character, game_id))
    
    db.write_finished_command(jsn)
