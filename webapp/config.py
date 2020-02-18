import logging
import time
from queue import PriorityQueue

from dataclasses import dataclass
from collections import namedtuple
from enum import Enum


# *************** GLOBAL VARIABLES ***************

class MatchMode(Enum):
    HUMAN_ONLY = 'HUMAN_ONLY'
    HUMAN_AND_AGENT = 'HUMAN_AND_AGENT'
    AGENT_ONLY = 'AGENT_ONLY'


SERVER_START_TIME = time.time()
TIMEOUT_AGE = 15 * 60  # 5 minutes before removing ghost session
MATCH_MODE = MatchMode.HUMAN_ONLY


@dataclass
class CurrentMatchMode:
    use_human: bool


CURRENT_MATCH_MODE = CurrentMatchMode(MATCH_MODE == MatchMode.HUMAN_ONLY)


@dataclass
class LoggedOverCapacity:
    num_connected: int


LOGGED_OVER_CAPACITY = LoggedOverCapacity(0)


for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(
    filename="app_console.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(filename)s:%(message)s"
    )
logger = logging.getLogger()

# Filter debug/info messages from apscheduler
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

"""Enable checking that players only get matched with players with
different IP addresses.

NOTE: This is not supported. We ensure workers don't connect more than once by checking their worker ID.
"""
ENABLE_IP_CHECK = False
PASSID = ""

"""lobby_clients is a list of players who are in the startup/matching
process. Each element is a 2-tuple of (IP, GameData object).

Priority is inverse of time they joined  since server started  (prioritizing
workers who waited longer.)
"""
lobby_clients = PriorityQueue()

agent_clients = PriorityQueue()

# Client still there keeps track of whether a given client is still around.
lobby_clients_active = dict()
agent_clients_active = dict()

"""liveGames is a list of GameData objects of ongoing games."""
live_games = dict() 

DATABASE_NAME = "database.db"

agent_processes = dict()  # Dictionary containing agent uuids and Popens

# ***** Classes *****

CerealRequest = namedtuple("CerealRequest", ["remote_addr", "sid", "worker_id", "assignment_id"])


class GameData:
    """
    human_id:   CerealRequest
    agent_id:   CerealRequest
    """
    def __init__(self, seed, game_id, num_cards, human, agent, using_agent):
        self.seed = seed
        self.game_id = game_id
        self.num_cards = num_cards
        self.human = human
        self.agent = agent
        self.human_ready = False
        self.agent_ready = False
        self.human_loaded = False
        self.agent_loaded = False
        self.human_quit = False
        self.agent_quit = False
        self.using_agent = using_agent

    def human_room(self):
        return room_name("Human", self.game_id)

    def agent_room(self):
        return room_name("Agent", self.game_id)

    def human_assignment_id(self):
        return self.human.assignment_id

    def agent_assignment_id(self):
        return self.agent.assignment_id

    def human_id(self):
        return self.human.worker_id

    def agent_id(self):
        return self.agent.worker_id

    def set_human_loaded(self):
        self.human_loaded = True

    def set_agent_loaded(self):
        self.agent_loaded = True

    def set_human_ready(self):
        self.human_ready = True

    def set_agent_ready(self):
        self.agent_ready = True

    def both_ready(self):
        return self.human_ready and self.agent_ready

    def both_loaded(self):
        return self.human_loaded and self.agent_loaded

    def set_human_quit(self):
        self.human_quit = True

    def set_agent_quit(self):
        self.agent_quit = True


# ***** Util functions *****
def lobby_room_name(cereal_request):
    return cereal_request.remote_addr + "/" + cereal_request.sid + "/" + cereal_request.worker_id


def room_name(character, game_id):
    return "/" + str(game_id) + "/" + character


def partner_room(my_character, game_id):
    return room_name("Human" if my_character == "Agent" else "Agent", game_id)


def get_game(game_id):
    try:
        game = live_games[game_id]
    except KeyError:
        logger.error('Game ' + str(game_id) + ' not found in live games')
        return
    return game


