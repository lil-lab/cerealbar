import sqlite3   # Enable control of an SQLite database
import sys


if __name__ == "__main__":
    worker_qual_file = sys.argv[1]

    f = "database.db"

    db = sqlite3.connect(f) #open if f exists, otherwise create
    c = db.cursor()    #facilitate db ops

    #------------------------create tables----------------------------------------
    #### Connection events table
    # clientSid: The SID for the client interacting with the webserver.
    # timeStamp: The timestamp of the event.
    # eventType: The type of the event, e.g., joined lobby, timed out, game ended.
    q = ("CREATE TABLE connectionEvents (clientSid STRING, timeStamp INTEGER, eventType STRING)")
    c.execute(q)

    #### Stores clients that join the lobby
    # clientSid: The SID of the client that has joined the lobby.
    # remoteAddr: The (hashed) IP address of the client.
    # uniqueId: The unique ID they used. Guaranteed not to change -- even if they time out
    #    on this sid, they will stick with the same unique ID. Also, this is only
    #    populated with people who join the lobby for the full game, so guaranteed
    #    to have a unique ID.
    # But TODO in the future might be to store all clients.
    q = ("CREATE TABLE clients (clientSid STRING, remoteAddr STRING, remotePort STRING, workerId STRING, assignmentId STRING, connectType STRING, disconnectType STRING)")
    c.execute(q)


    q = ("CREATE TABLE qualifiedWorkers (workerId STRING, isQualified INTEGER)")
    c.execute(q)

    # Now insert into the qualified workers whatever's in there already
    with open(worker_qual_file) as infile:
        qual_workers = [line.strip() for line in infile]
        print('Adding ' + str(len(qual_workers)) + ' qualified workers to the DB')
        for worker in qual_workers:
            q = "INSERT INTO qualifiedWorkers (workerId, isQualified) VALUES (?,?)"
            t = (worker, 1)
            c.execute(q, t)

    # Includes ALL connections to the page, even if they did not access the game.
    q = ("CREATE TABLE rawClients (remoteAddr STRING, remotePort STRING, connectionTime STRING)")
    c.execute(q)

    q = ("CREATE TABLE debugLogs (gameId STRING, clientSid STRING, message STRING)")
    c.execute(q)

    # All assignment IDs
    q = ("CREATE TABLE assignmentIds (assignmentId STRING, workerId STRING, timeUsed STRING)")
    c.execute(q)

    q = ("CREATE TABLE leaderTutorial (clientSid STRING, workerId STRING, assignmentId STRING, timeCompleted STRING)")
    c.execute(q)

    q = ("CREATE TABLE followerTutorial (clientSid STRING, workerId STRING, assignmentId STRING, timeCompleted STRING)")
    c.execute(q)

    q = ("CREATE TABLE movements (gameId STRING, moveId INTEGER, character STRING, "
         "action STRING, position STRING, rotation INTEGER, gameTime INTEGER, serverTime INTEGER, turnId INTEGER)")
    c.execute(q)

    q = ("CREATE TABLE cardSelections (gameId STRING, moveId INTEGER, card STRING, result STRING)")
    c.execute(q)

    # setId is the # of sets completed when the cards appeared.
    q = ("CREATE TABLE cardSets (gameId STRING, moveId INTEGER, setId INTEGER, cards STRING)")
    c.execute(q)

    # method is how the turn ran out
    # type is whether it was the beginning or end of a turn
    q = ("CREATE TABLE turns (gameId STRING, turnId INTEGER, gameTime INTEGER, serverTime INTEGER, method STRING, type STRING, character STRING)")
    c.execute(q)

    q = ("CREATE TABLE initialInfo (seed INTEGER, hexCellInfo STRING, "
        "propPlacementInfo STRING, cardInfo STRING)")
    c.execute(q)

    q = "CREATE TABLE games (gameId INTEGER, seed INTEGER, humanSid STRING, agentSid STRING, numCards INTEGER, score INTEGER, startTime INTEGER, endTime INTEGER, usingAgent INTEGER)"
    c.execute(q)

    q = "CREATE TABLE commandFinishingActions (gameId INTEGER, instructionId INTEGER, gameTime INTEGER, serverTime INTEGER)"
    c.execute(q)

    q = ("CREATE TABLE instructions (gameId INTEGER, moveId INTEGER, "
        "instructionId INTEGER, instruction STRING, gameTime INTEGER, "
        "serverTime INTEGER, turnId INTEGER)")
    c.execute(q)

    db.commit()
    db.close()
