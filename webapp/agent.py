import uuid
import sys
import logging

logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)

import nltk
import socketio
import os
import random
import time
import torch
import pickle
from datetime import datetime

sys.path.append('agent_learning/')

from environment.agent_actions import AgentAction
from data.in_game_example import InGameExample
from data.state_delta import StateDelta
from environment.card import get_card_count, get_card_color, get_card_shape, Card, CardSelection
from environment.agent import Agent
from environment.position import Position, v3_pos_to_position
from environment.terrain import Terrain
from environment.util import interpret_card_info, construct_object
from simulation.util import HEX_WIDTH, HEX_DEPTH
from model.modules.trajectory_distribution import normalize_trajectory_distribution
from environment.terrain import cell_name_to_terrain
from environment.position import v3_pos_to_position
from model.modules.auxiliary import Auxiliary
from environment.environment_objects import ObjectType
from learning.inference import load_vocabulary
from simulation.python_game import PythonGame
from model.model_wrappers.model_creator import get_model_wrapper

SOCKET = socketio.Client()

#MODEL_DIR = 'agent_learning/experiments/finetune_aggregate_0.7_1'
#SAVE_NAME = 'model_17_score.pt'

MODEL_DIR = 'agent_learning/experiments/finetune_aggregate_0.7_0'
SAVE_NAME = 'model_13_score.pt'

def get_current_time():
    # Stores the current time and date (including microseconds)
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

class GameArgs:
    def __init__(self):
        self._initial_turns = 12  # Right?
        self._leader_steps_per_turn = 5
        self._follower_steps_per_turn = 10

    def get_initial_num_turns(self):
        return self._initial_turns

    def get_leader_steps_per_turn(self):
        return self._leader_steps_per_turn

    def get_follower_steps_per_turn(self):
        return self._follower_steps_per_turn

    def keep_track_of_turns(self):
        return True


dummy_game_args = GameArgs()


def get_hexes(hex_info):
    hexes = list()
    for hex_cell in hex_info:
        position: Position = v3_pos_to_position(eval(hex_cell['posV3']), HEX_WIDTH, HEX_DEPTH)
        terrain: Terrain = cell_name_to_terrain(hex_cell['lType'], float(eval(hex_cell['posV3'])[1]))

        hexes.append((terrain, position))
    return hexes


def get_props(prop_info):
    leader: Agent = None
    follower: Agent = None
    objects = list()

    for env_object in prop_info:
        prop_name: str = env_object['pName']
        position: Position = v3_pos_to_position(eval(env_object['posV3']),
                                                HEX_WIDTH,
                                                HEX_DEPTH)

        constructed_object = construct_object(prop_name,
                                              position,
                                              eval(env_object['rotV3']),
                                              [])
        if constructed_object.get_type() not in {ObjectType.FOLLOWER, ObjectType.LEADER}:
            objects.append(constructed_object)
        elif constructed_object.get_type() == ObjectType.LEADER:
            leader = constructed_object
        elif constructed_object.get_type() == ObjectType.FOLLOWER:
            follower = constructed_object
        else:
            raise ValueError('Unrecognized object type with Agent object: ' + str(constructed_object.get_type()))

    if not leader or not follower:
        raise ValueError('Didn\'t find leader or follower in the object list.')

    return objects, leader, follower


def get_initial_cards(card_info):
    return interpret_card_info(card_info, HEX_WIDTH, HEX_DEPTH)


class AgentClient:
    def __init__(self):
        self._id = sys.argv[1]

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(
            filename="agent_logs/agent_" + str(self._id) + "_console.log",
            level=logging.DEBUG,
            format="%(asctime)s:%(levelname)s:%(filename)s:%(message)s"
        )

        self._game_id = None
        self._game_seed = None
        self._num_cards = None
        self._game = None

        # Load the model
        # TODO: having multiple copies isn't great
        with open(os.path.join(MODEL_DIR, 'args.pkl'), 'rb') as infile:
            args = pickle.load(infile)
        self._model = get_model_wrapper(args.get_model_args(),
                                        args.get_training_args(),
                                        load_vocabulary(MODEL_DIR),
                                        load_pretrained=False)
        self._model.load(os.path.join(MODEL_DIR, SAVE_NAME))
        self._model.eval()
        self._model = self._model._model

        print(self._model)

        self._current_example = None

        self._dist_map = None
        self._action_sequence = None
        self._rnn_state = None

    def get_id(self) -> str:
        return self._id

    def get_game_id(self) -> str:
        return self._game_id

    def get_game(self):
        return self._game

    def set_game_id(self, game_id):
        self._game_id = game_id
        logging.info('Playing game ' + str(self._game_id))

    def set_game_seed(self, game_seed):
        self._game_seed = game_seed
        logging.info('Game seed: ' + str(self._game_seed))

    def set_num_cards(self, num_cards):
        self._num_cards = num_cards
        logging.info('Number of cards: ' + str(self._num_cards))

    def connect(self):
        SOCKET.connect('http://localhost:8080')
        SOCKET.emit('sendCredentials', {'worker_id': self._id,
                                        'assignment_id': self._id})
        logging.info('Started agent ' + str(self._id))

    def start_game(self, hexes, props, cards, leader, follower):
        logging.info('Started game! Leader location is ' + str(leader) + '; follower location is ' + str(follower))
        self._game = PythonGame(dummy_game_args,
                                hexes,
                                props,
                                StateDelta(leader, follower, cards),
                                auto_end_turn=False,
                                verbose=True)

    def add_instruction(self, instruction):
        self._game.add_instruction(instruction)

    def start_turn(self):
        self._game.end_turn()

        # It might still be the leader turn, e.g., if there are no instructions to follw. If so, end the turn.
        if self._game.is_leader_turn():
            logging.info('Immediately ended turn after starting -- there are no more instructions to follow, '
                         'so ending turn.')
            SOCKET.emit('yourTurn', {'character': 'Agent',
                                     'gameId': self._game_id,
                                     'turnId': self._game.get_turn_index(),
                                     'time': get_current_time(),
                                     'method': 'NoInstructionsToFollow'})
            return

        while not self._game.is_leader_turn():
            # Basically wait for there to be 21 cards. This isn't great but won't allow it to predict when there aren't
            # 21 on the board.
            while len(self._game.get_game_info().cards) != 21:
                pass

            if not self._current_example:
                # Plan: Run the hex predictor the first time
                self._current_example = InGameExample(self._game.get_game_info(),
                                                      self._game.get_hexes(),
                                                      self._game.get_objects(),
                                                      nltk.word_tokenize(self._game.get_current_instruction().lower()))
                logging.info('Creating a new example for instruction ' + ' '.join(self._current_example.get_instruction()))
                card_dist, auxiliary_pred = self._model._hex_predictor.get_predictions(self._current_example)
                avoid_distribution = auxiliary_pred[Auxiliary.AVOID_LOCS].unsqueeze(1)
                trajectory_distribution, _ = \
                    normalize_trajectory_distribution(auxiliary_pred[Auxiliary.TRAJECTORY][0], None)
                impassable_distribution = auxiliary_pred[Auxiliary.IMPASSABLE_LOCS].unsqueeze(1)

                self._dist_map = \
                    torch.cat((avoid_distribution,
                               impassable_distribution,
                               card_dist.unsqueeze(0),
                               trajectory_distribution), dim=1)
                self._action_sequence = [AgentAction.START]
                self._rnn_state = self._model._initialize_rnn(1)

            # Predict an action
            sleep_time = random.uniform(0.2, 0.8)
            time.sleep(sleep_time)
            pred_action, self._rnn_state, resulting_state = \
                self._model._predict_one_action(self._action_sequence,
                                                self._game,
                                                self._dist_map,
                                                None,
                                                self._rnn_state)

            # Action was already executed internally, so send it over
            self._action_sequence.append(pred_action)

            if pred_action != AgentAction.STOP:
                SOCKET.emit('movement',
                            {'character': 'Agent',
                             'gameId': self._game_id,
                             'type': str(pred_action),
                             'moveId': self._game.get_move_id(),
                             'position': str(self._game.get_game_info().follower.get_position()),
                             'time': get_current_time(),
                             'turnId': self._game.get_turn_index()})
            else:
                logging.info('finish command!')
                SOCKET.emit('finishedCommand',
                            {'character': 'Agent',
                             'gameId': self._game_id,
                             'time': get_current_time(),
                             'content': str(self._game.get_instruction_index())})

            # If there are too many actions, execute finish command
            if len(self._action_sequence) >= 25\
                    and AgentAction.STOP not in self._action_sequence\
                    and not self._game.is_leader_turn():
                logging.info('Generated too many actions: stopping')
                self._game.execute_follower_action(AgentAction.STOP)

                # Send 'finish command'
                pred_action = AgentAction.STOP

                SOCKET.emit('finishedCommand',
                            {'character': 'Agent',
                             'gameId': self._game_id,
                             'time': get_current_time(),
                             'content': str(self._game.get_instruction_index())})

            if pred_action == AgentAction.STOP:
                # Reset everything
                self._current_example = None

                self._dist_map = None
                self._action_sequence = None
                self._rnn_state = None

        # Now end the turn
        SOCKET.emit('yourTurn', {'character': 'Agent',
                                 'gameId': self._game_id,
                                 'turnId': self._game.get_turn_index(),
                                 'time': get_current_time(),
                                 'method': 'RanOutOfMoves'})

    def receive_set(self, jsn):
        card_info = jsn['cards'].split('), ')
        current_cards = self._game.get_game_info().cards
        new_cards = list()
        for card in card_info:
            card_val, loc = card.split('(')
            count, color, shape = card_val.strip().split(' ')
            loc = loc.strip('(').strip(')')
            count = get_card_count(count)
            color = get_card_color(color)
            shape = get_card_shape(shape)
            position = v3_pos_to_position(eval('(' + loc + ')'), 17.321, 15.)
            card = Card(position, 150, color, count, shape, CardSelection.UNSELECTED)
            found = False
            for old_card in current_cards:
                if card == old_card:
                    found = True
            if not found:
                new_cards.append(card)
        logging.info('Added new cards:')
        assert len(new_cards) == 3
        for card in new_cards:
            logging.info(card)
        self._game._add_cards(new_cards)
        self._game._current_state_delta.cards.extend(new_cards)


AGENT = AgentClient()
AGENT.connect()


@SOCKET.on('recognizedAgent')
def on_recognized(jsn):
    logging.info('Authorized, now joining lobby.')
    SOCKET.emit('joinLobby', {'worker_id': AGENT.get_id(),
                              'assignment_id': AGENT.get_id()})


@SOCKET.on('initGame')
def on_game_init(json_data):
    # Just save the basic information. The js client doesn't do anything besides save the information here.
    AGENT.set_game_id(json_data['gameId'])
    AGENT.set_game_seed(json_data['seed'])
    AGENT.set_num_cards(json_data['num_cards'])


@SOCKET.on('startGame')
def start_game(jsn):
    logging.info('Starting game.')
    SOCKET.emit('readyToStartGamePlay', {'character': 'Agent',
                                         'gameId': AGENT.get_game_id()})


@SOCKET.on('lobbyReady')
def on_lobby_ready(jsn):
    logging.info('Lobby is ready.')
    SOCKET.emit('readyPressed', {'character': 'Agent',
                                 'gameId': AGENT.get_game_id()})


@SOCKET.on('startGamePlay')
def on_start_game_play(jsn):
    logging.info('Start game play.')


@SOCKET.on('initialMapInfo')
def initial_map_info(jsn):
    logging.info('Got map info ')
    props, leader, follower = get_props(jsn['propPlacementInfo'])
    AGENT.start_game(get_hexes(jsn['hexCellInfo']),
                     props,
                     get_initial_cards(jsn['cardInfo']),
                     leader,
                     follower)


@SOCKET.on('movement')
def on_movement(jsn):
    if jsn['character'] == 'Human':
        AGENT.get_game().execute_leader_action(AgentAction(jsn['type']))


@SOCKET.on('instruction')
def on_instruction(jsn):
    AGENT.add_instruction(jsn['content'])


@SOCKET.on('yourTurn')
def on_your_turn(jsn):
    AGENT.start_turn()


@SOCKET.on('set')
def on_set(jsn):
    AGENT.receive_set(jsn)

