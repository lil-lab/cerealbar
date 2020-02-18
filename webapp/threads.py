import webapp.database as db
import eventlet
import time
import uuid
import sys
import queue
import random

from webapp import socketio

from webapp.config import lobby_clients, lobby_clients_active, logger, live_games, SERVER_START_TIME, TIMEOUT_AGE
from webapp.config import GameData, MATCH_MODE, MatchMode, agent_clients, agent_clients_active, CURRENT_MATCH_MODE, LOGGED_OVER_CAPACITY


def maintain_lobby():
    while True:
        remove_ghost_sessions()

        match_players()

        eventlet.sleep(0.1)


def match_human_players():
    if lobby_clients.qsize() >= 2:
        try:
            client_1 = lobby_clients.get()
        except queue.Empty as e:
            logger.debug("Couldn't get client 1 in human-human match, " + str(e))
            return

        try:
            client_2 = lobby_clients.get()
        except queue.Empty as e:
            logger.debug("Couldn't get client 2 in human-human match, " + str(e))
            lobby_clients.put(client_1)
            return

        # If one of them isn't there anymore, remove (put the other one back)
        if not (lobby_clients_active[client_1[1].sid] and lobby_clients_active[client_2[1].sid]):
            logger.debug("Pair between " + client_1[1].sid + " and " + client_2[1].sid +
                         " didn't work; removing one or both of them")
            if lobby_clients_active[client_1[1].sid]:
                lobby_clients.put(client_1)
            elif lobby_clients_active[client_2[1].sid]:
                lobby_clients.put(client_2)
            return

        if client_1[1].sid == client_2[1].sid:
            # It is possible they can match with themselves in the case
            # that they time out and restart from the same page. Avoid this
            # by removing a client if it has the same sid.

            # This only happens because the player joins the lobby twice from the
            # same sid (we don't make them reload the page to return to the
            # lobby). lobby_clients_active is updated to True for the second
            # time they join the lobby, so for both clients in the lobby, they
            # are considered active (the only thing different between the two
            # clients is the time they entered, which we don't want to require
            # for lookups in lobby_clients_active). Return the one to the
            # queue that has waited shorter (i.e., the one that just joined).
            lobby_clients.put(client_2)
            return

        client_1_waittime = time.time() - client_1[0] - SERVER_START_TIME
        client_2_waittime = time.time() - client_2[0] - SERVER_START_TIME

        client_1 = client_1[1]
        client_2 = client_2[1]

        lobby_clients_active[client_1.sid] = False
        lobby_clients_active[client_2.sid] = False

        db.write_connection_event(client_1.sid, "Matched With Partner")
        db.write_connection_event(client_2.sid, "Matched With Partner")

        # pair them up
        # guaranteed to be free of collisions and we don't need ordering on
        # game IDs so just use uuid
        game_id = str(uuid.uuid4().hex)
        game_seed = random.randint(0, pow(2, 30))
        print('game seed: ' + str(game_seed))
        logger.debug('game seed: ' + str(game_seed))

        num_cards = 21

        character_1 = "Human" if game_seed % 2 == 0 else "Agent"
        character_2 = "Agent" if character_1 == "Human" else "Human"
        if character_1 == "Human":
            game = GameData(game_seed,
                            game_id,
                            num_cards,
                            human=client_1,
                            agent=client_2,
                            using_agent=False)
        else:
            game = GameData(game_seed,
                            game_id,
                            num_cards,
                            human=client_2,
                            agent=client_1,
                            using_agent=False)
        live_games[game_id] = game
        logger.debug("starting game #" + str(game_id) + " with seed " + str(game_seed) + " and worker ids "
                     + client_1.worker_id + " / " + client_2.worker_id)
        logger.debug("client 1 (" + str(client_1) + " waited for " + str(client_1_waittime) + " s")
        logger.debug("client 2 (" + str(client_2) + " waited for " + str(client_2_waittime) + " s")

        # Initialize the game for both players, and also say that the lobby
        # is ready (players matched) -- this will play the audio reminder

        # For now, each player is in a room corresponding to their sid.
        # But later they will go into a room corresponding to the game, so
        # movement communication is easier.
        socketio.emit('initGame',
                      {'character': character_1,
                       'gameId': game_id,
                       'seed': game_seed,
                       'num_cards': num_cards},
                      room=client_1.sid)
        socketio.emit('lobbyReady',
                      room=client_1.sid)

        socketio.emit('initGame',
                      {'character': character_2,
                       'gameId': game_id,
                       'seed': game_seed,
                       'num_cards': num_cards},
                      room=client_2.sid)
        socketio.emit('lobbyReady',
                      room=client_2.sid)

        db.write_game_start(game)

        # Switch the mode
        if MATCH_MODE == MatchMode.HUMAN_AND_AGENT:
            CURRENT_MATCH_MODE.use_human = False
            logger.debug('Switching to matching with human: ' + str(CURRENT_MATCH_MODE.use_human))


def match_human_with_agent():
    # Don't allow more than N concurrent games
    if len(live_games) >= 30:
        if lobby_clients.qsize() > LOGGED_OVER_CAPACITY.num_connected:
            logger.debug("New maximum connections reached: %r" % lobby_clients.qsize())
            LOGGED_OVER_CAPACITY.num_connected = lobby_clients.qsize()
        elif lobby_clients.qsize() < LOGGED_OVER_CAPACITY.num_connected:
            logger.debug("Number of connections lowered: %r" % lobby_clients.qsize())
            LOGGED_OVER_CAPACITY.num_connected = lobby_clients.qsize()

        return

    if lobby_clients.qsize() >= 1 and agent_clients.qsize() >= 1:
        try:
            human_client = lobby_clients.get()
        except queue.Empty as e:
            logger.debug("Couldn't get human in human-agent match, " + str(e))
            return

        try:
            agent_client = agent_clients.get()
        except queue.Empty as e:
            logger.debug("Couldn't get agent in human-agent match, " + str(e))
            lobby_clients.put(human_client)
            return

        # If one of them isn't there anymore, remove (put the other one back)
        if not (lobby_clients_active[human_client[1].sid] and agent_clients_active[agent_client[1].sid]):
            logger.debug("Pair between " + human_client[1].sid + " and " + agent_client[1].sid +
                         " didn't work; removing one or both of them")
            if lobby_clients_active[human_client[1].sid]:
                lobby_clients.put(human_client)
            elif agent_clients_active[agent_client[1].sid]:
                agent_clients.put(agent_client)
            return

        if human_client[1].sid == agent_client[1].sid:
            raise ValueError('Agent and human client sid should never be the same!' + str(human_client[1].sid))

        client_1_waittime = time.time() - human_client[0] - SERVER_START_TIME
        client_2_waittime = time.time() - agent_client[0] - SERVER_START_TIME

        human_client = human_client[1]
        agent_client = agent_client[1]

        lobby_clients_active[human_client.sid] = False
        agent_clients_active[agent_client.sid] = False

        db.write_connection_event(human_client.sid, "Matched With Partner")
        db.write_connection_event(agent_client.sid, "Matched With Partner")

        # pair them up
        # guaranteed to be free of collisions and we don't need ordering on
        # game IDs so just use uuid
        game_id = str(uuid.uuid4().hex)
        game_seed = random.randint(0, pow(2, 30))
        num_cards = 21

        game = GameData(game_seed,
                        game_id,
                        num_cards,
                        human=human_client,
                        agent=agent_client,
                        using_agent=True)
        live_games[game_id] = game
        logger.debug("starting game #" + str(game_id) + " with seed " + str(game_seed) + " and worker ids "
                     + human_client.worker_id + " / " + agent_client.worker_id)
        logger.debug("client 1 (" + str(human_client) + " waited for " + str(client_1_waittime) + " s")
        logger.debug("client 2 (" + str(agent_client) + " waited for " + str(client_2_waittime) + " s")

        # Initialize the game for both players, and also say that the lobby
        # is ready (players matched) -- this will play the audio reminder

        # For now, each player is in a room corresponding to their sid.
        # But later they will go into a room corresponding to the game, so
        # movement communication is easier.
        socketio.emit('initGame',
                      {'character': 'Human',
                       'gameId': game_id,
                       'seed': game_seed,
                       'num_cards': num_cards},
                      room=human_client.sid)
        socketio.emit('lobbyReady',
                      room=human_client.sid)

        socketio.emit('initGame',
                      {'character': 'Agent',
                       'gameId': game_id,
                       'seed': game_seed,
                       'num_cards': num_cards},
                      room=agent_client.sid)
        socketio.emit('lobbyReady',
                      room=agent_client.sid)

        db.write_game_start(game)

        # Switch the mode
        if MATCH_MODE == MatchMode.HUMAN_AND_AGENT:
            CURRENT_MATCH_MODE.use_human = True
            logger.debug('Switching to matching with human: ' + str(CURRENT_MATCH_MODE.use_human))


def match_players():
    if CURRENT_MATCH_MODE.use_human:
        match_human_players()
    else:
        match_human_with_agent()


def remove_ghost_sessions():
    cur_age = sys.maxsize
    ghost_start_time = time.time() - SERVER_START_TIME
    while cur_age > TIMEOUT_AGE and not lobby_clients.empty():
        client_entered_time, client = lobby_clients.get()

        client_age = ghost_start_time - client_entered_time

        if client_age <= TIMEOUT_AGE:
            # If hasn't been waiting long, put it back and break
            lobby_clients.put((client_entered_time, client))
        else:
            lobby_clients_active[client.sid] = False

            socketio.emit('reset', room=client.sid)
            logger.debug('marked inactive client ' + str(client) + '; waited for ' + str(client_age) + ' s')
            db.write_connection_event(client.sid, "Removed Ghost Session")

        cur_age = client_age

