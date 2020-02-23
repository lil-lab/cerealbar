import sqlite3

from webapp.config import DATABASE_NAME, logger
from datetime import datetime


def get_current_time():
    # Stores the current time and date (including microseconds)
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')


def worker_connected(worker_id):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()
    q = 'SELECT disconnectType FROM clients WHERE workerId=? AND connectType=?'
    t = (worker_id, 'Validated Connection')
    c.execute(q, t)
    disconnect_type = c.fetchall()
    if disconnect_type:
        last_disconnect_type = disconnect_type[-1][0]
        return last_disconnect_type is None
    else:
        return False


def write_debug_log(game_id, request_sid, message):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'INSERT INTO debugLogs (gameId, clientSid, message) VALUES (?,?,?)'
    t = (game_id, request_sid, message)

    c.execute(q, t)
    db.commit()
    db.close()


def write_connection_event(sid, event_type):
    timestamp = get_current_time()

    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'INSERT INTO connectionEvents (clientSid, timeStamp, eventType) VALUES (?,?,?)'
    t = (sid, timestamp, event_type)

    c.execute(q, t)
    db.commit()
    db.close()


def write_raw_client(remote_addr, remote_port):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'INSERT INTO rawClients (remoteAddr, remotePort, connectionTime) VALUES (?,?,?)'
    t = (remote_addr, remote_port, get_current_time())

    c.execute(q, t)
    db.commit()
    db.close()


def write_client(sid, remote_addr, remote_port):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'INSERT INTO clients (clientSid, remoteAddr, remotePort, connectType) VALUES (?,?,?,?)'
    t = (sid, remote_addr, remote_port, 'Connected without Loading')

    c.execute(q, t)
    db.commit()
    db.close()


def update_client_info(sid, worker_id, assignment_id, connect_type):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'UPDATE clients SET workerId=?, assignmentId=?, connectType=? WHERE clientSid=?'
    t = (worker_id, assignment_id, connect_type, sid)
    c.execute(q, t)

    db.commit()
    db.close()


def is_qualified(worker_id):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'SELECT workerId FROM qualifiedWorkers WHERE workerId=? AND isQualified=?'
    t = (worker_id, 1)
    c.execute(q, t)
    result = c.fetchone()
    
    qualified = result is not None
    db.close()
    return qualified


def disconnect_client(sid, disconnect_type):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'UPDATE clients SET disconnectType=? WHERE clientSid=?'
    t = (disconnect_type, sid)
    c.execute(q, t)

    db.commit()
    db.close()


def assignment_id_used(worker_id, assignment_id):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'SELECT * FROM assignmentIds WHERE assignmentId=? AND workerId=?'
    t = (assignment_id, worker_id)

    c.execute(q, t)

    found = (c.fetchone() is not None)
    db.close()
    return found


def mark_assignment_id_used(worker_id, assignment_id):
    if worker_id:
        db = sqlite3.connect(DATABASE_NAME)
        c = db.cursor()

        q = 'INSERT INTO assignmentIds (assignmentId, workerId, timeUsed) VALUES (?,?,?)'
        t = (assignment_id, worker_id, get_current_time())
        c.execute(q, t)

        db.commit()
        db.close()


def mark_tutorial_complete(sid, is_leader, sent_worker_id, sent_assignment_id):
    table_name = 'leaderTutorial' if is_leader else 'followerTutorial'
    
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    # First, get the worker ID
    q = 'SELECT workerId, assignmentId FROM clients WHERE clientSid=?'
    t = (sid,)
    c.execute(q, t)

    result = c.fetchone()
    if result:
        worker_id, assignment_id = result
        if worker_id != sent_worker_id:
            logger.error('Sent worker ID was not expected: (sent) ' + sent_worker_id + '; (in DB) ' + worker_id)
        if assignment_id != sent_assignment_id:
            logger.error('Sent assignment ID was not expected: (sent) ' + sent_assignment_id + '; (in DB) ' + assignment_id)
    else:
        worker_id = sent_worker_id
        assignment_id = sent_assignment_id

    # See whether it's already been put in there
    q = 'SELECT * from ' + table_name + ' WHERE clientSid=? AND workerId=? AND assignmentId=?'
    t = (sid, worker_id, assignment_id)
    c.execute(q, t)
    if not c.fetchone():
        q = 'INSERT INTO ' + table_name + ' (clientSid, workerId, assignmentId, timeCompleted) VALUES (?,?,?,?)'
        t = (sid, worker_id, assignment_id, get_current_time())
        c.execute(q, t)
        db.commit()

    db.close()


def write_game_start(game):
    current_time = get_current_time()

    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = (
        "INSERT INTO games (gameId, seed, humanSid, agentSid, numCards, startTime, usingAgent, instructionCostStep) "
        "VALUES (?,?,?,?,?,?,?,?)"
    )
    t = (
        game.game_id,
        game.seed,
        game.human.sid,
        game.agent.sid,
        game.num_cards,
        current_time,
        1 if game.using_agent else 0,
        game.instruction_cost_step,
    )
    c.execute(q, t)

    db.commit()
    db.close()


def write_game_end(game_id, score):
    current_time = get_current_time()

    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'UPDATE games SET score=?, endTime=? WHERE gameId=?'
    t = (score, current_time, game_id)

    c.execute(q, t)

    db.commit()
    db.close()


def get_game_score(game_id):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'SELECT score FROM games WHERE gameId=?'
    t = (game_id,)
    c.execute(q, t)

    score = c.fetchone()[0]

    db.close()

    return score


def write_movement(jsn_rep):
    game_id = jsn_rep["gameId"]
    character = jsn_rep["character"]
    action = jsn_rep["type"]
    server_time = get_current_time()

    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    # Get the previous rotation for this character
    # TODO: should just send this over with the rest of the info
    q = 'SELECT rotation FROM movements WHERE gameId=? AND character=? AND rotation IS NOT NULL'
    t = (game_id, character)
    c.execute(q, t)

    prev_rot = c.fetchall()

    if prev_rot:
        prev_rot = prev_rot[-1][0]

        #  If they moved, update it
        if action == "RR":
            prev_rot += 60
        elif action == "RL":
            prev_rot -= 60

        rot = prev_rot % 60
    else:
        rot = 0  # from agent... should fix (TODO)

    # Add the action into the movements table
    q = 'INSERT INTO movements (gameId, moveId, character, action, position, rotation, gameTime, serverTime, turnId) ' \
        'VALUES (?,?,?,?,?,?,?,?,?)'
    t = (game_id, jsn_rep["moveId"], character, action, jsn_rep["position"], rot, jsn_rep["time"], server_time, jsn_rep["turnId"])
    c.execute(q, t)
    db.commit()
    db.close()


def write_instruction(game_id, move_id, instruction_id, content, game_time, turn_id):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()
    server_time = get_current_time()

    q = 'INSERT INTO instructions (gameId, moveId, instructionId, instruction, gameTime, serverTime, turnId) ' \
        'VALUES (?,?,?,?,?,?,?)'
    t = (game_id, move_id, instruction_id, content, game_time, server_time, turn_id)
    c.execute(q, t)
    db.commit()
    db.close()


def write_card_selection(game_id, move_id, card, result):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'SELECT * from cardSelections WHERE gameId=? AND moveId=?'
    t = (game_id, move_id)
    c.execute(q, t)

    if c.fetchone() is None:
        q = 'INSERT INTO cardSelections (gameId, moveId, card, result) VALUES (?,?,?,?)'
        t = (game_id, move_id, card, result)
        c.execute(q, t)
        db.commit()

    db.close()


# TODO: this may also be written twice
def write_set(game_id, move_id, score, cards):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'SELECT * from cardSets WHERE gameId=? AND moveId=?'
    t = (game_id, move_id)
    c.execute(q, t)

    if c.fetchone() is None:
        q = 'INSERT INTO cardSets (gameId, moveId, setId, cards) VALUES (?,?,?,?)'
        t = (game_id, move_id, score, cards)

        c.execute(q, t)
        db.commit()

    db.close()


def write_first_turn(game_id):
    # TODO: in rare cases this may be written twice
    current_time = get_current_time()

    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'INSERT INTO turns (gameId, turnId, gameTime, serverTime, method, type, character) VALUES (?,?,?,?,?,?,?)'
    t = (game_id, 0, 0, current_time, 'game started', 'begin', 'Human')
    c.execute(q, t)

    db.commit()
    db.close()


def write_turn_switch(jsn_rep):
    game_id = jsn_rep['gameId']
    game_time = jsn_rep['time']
    current_time = get_current_time()

    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    # Get the previous turn ID
    q = 'SELECT turnId, character from turns WHERE gameId=?'
    t = (game_id,)
    c.execute(q, t)
    prev_turn = c.fetchall()[-1]

    q = 'INSERT INTO turns (gameId, turnId, gameTime, serverTime, method, type, character) VALUES (?,?,?,?,?,?,?)'

    # Save the fact that the turn ended, and that the next turn started.
    t = (game_id, prev_turn[0], game_time, current_time, jsn_rep['method'], 'end', prev_turn[1])
    c.execute(q, t)

    t = (game_id, prev_turn[0] + 1, game_time, current_time, 'begin', 'begin', 'Human' if prev_turn[1] == 'Agent' else 'Agent')
    c.execute(q, t)

    db.commit()
    db.close()


def write_final_turn(game_id, game_time):
    current_time = get_current_time()

    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    # Get the previous turn ID
    q = 'SELECT turnId, character from turns WHERE gameId=?'
    t = (game_id,)
    c.execute(q, t)
    prev_turn = c.fetchall()[-1]

    q = 'INSERT INTO turns (gameId, turnId, gameTime, serverTime, method, type, character) VALUES (?,?,?,?,?,?,?)'
    t = (game_id, prev_turn[0], game_time, current_time, 'game ended', 'end', prev_turn[1])
    c.execute(q, t)

    db.commit()
    db.close()


def write_finished_command(jsn_rep):
    current_time = get_current_time()

    game_id = jsn_rep["gameId"]
    game_time = jsn_rep["time"]

    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    # Get the previous instruction index
    q = 'SELECT instructionId FROM commandFinishingActions WHERE gameId=?'
    t = (game_id,)
    c.execute(q, t)
    result = c.fetchall()
    
    if not result:
        finished_index = 0
    else:
        finished_index = result[-1][0] + 1

    q = 'INSERT INTO commandFinishingActions (gameId, instructionId, gameTime, serverTime) VALUES (?,?,?,?)'
    t = (game_id, finished_index, game_time, current_time)
    c.execute(q, t)

    db.commit()
    db.close()


def write_initial_info(seed, hex_cells, props, cards):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'SELECT seed FROM initialInfo WHERE seed=?'
    t = (seed,)
    c.execute(q, t)

    result = c.fetchone()

    if not result:
        q = 'INSERT INTO initialInfo (seed, hexCellInfo, propPlacementInfo, cardInfo) VALUES (?,?,?,?)'
        t = (seed, hex_cells, props, cards)
        c.execute(q, t)
        db.commit()

    db.close()


def get_agent_id_for_game(game_id):
    db = sqlite3.connect(DATABASE_NAME)
    c = db.cursor()

    q = 'SELECT workerId FROM clients WHERE clientSid IN (SELECT agentSid FROM games WHERE gameId=?)'
    t = (game_id,)
    c.execute(q, t)
    result = c.fetchall()

    db.close()

    return result[0][0] if result else ''
