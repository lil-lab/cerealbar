"""Contains arguments on the platform to run gameplay."""
from argparse import ArgumentParser, Namespace
from distutils.util import strtobool

from agent.config import args


class GameArgs(args.Args):
    """ Arguments for running games."""

    def __init__(self, parser: ArgumentParser):
        super(GameArgs, self).__init__()

        parser.add_argument('--game_ip',
                            default='localhost',
                            type=str,
                            help='The IP address where the game is being served.')
        parser.add_argument('--game_port',
                            default=3706,
                            type=int,
                            help='The port where the game is being served.')
        parser.add_argument('--initial_number_of_turns',
                            default=6,
                            type=int,
                            help='The initial number of turns each player starts with.')
        parser.add_argument('--leader_moves_per_turn',
                            default=5,
                            type=int,
                            help='The number of moves each human gets per turn.')
        parser.add_argument('--follower_moves_per_turn',
                            default=10,
                            type=int,
                            help='The number of moves each agent gets per turn.')
        parser.add_argument('--keep_track_of_turns',
                            default=True,
                            type=lambda x: bool(strtobool(x)),
                            help="Whether to be strict about keeping track of whose turn it is, and how many turns are "
                                 "left.")
        parser.add_argument('--action_delay',
                            default=0.,
                            type=float,
                            help='The amount of time to delay between actions.')
        parser.add_argument('--generate_new_cards',
                            default=True,
                            type=bool,
                            help='Whether to randomly generate new cards when an unexpected set is made.')

        self._ip_address: str = None
        self._port: int = None
        self._initial_number_of_turns: int = None
        self._action_delay: float = None

        self._leader_moves_per_turn: int = None
        self._follower_moves_per_turn: int = None

        self._keep_track_of_turns: bool = None
        self._generate_new_cards: bool = None

    def generate_new_cards(self) -> bool:
        self.check_initialized()
        return self._generate_new_cards

    def get_ip_address(self) -> str:
        self.check_initialized()
        return self._ip_address

    def get_port(self) -> int:
        self.check_initialized()
        return self._port

    def keep_track_of_turns(self) -> bool:
        self.check_initialized()
        return self._keep_track_of_turns

    def get_action_delay(self) -> float:
        self.check_initialized()
        return self._action_delay

    def get_initial_number_of_turns(self) -> int:
        self.check_initialized()
        return self._initial_number_of_turns

    def get_leader_moves_per_turn(self) -> int:
        self.check_initialized()
        return self._leader_moves_per_turn

    def get_follower_moves_per_turn(self) -> int:
        self.check_initialized()
        return self._follower_moves_per_turn

    def interpret_args(self, parsed_args: Namespace) -> None:
        self._ip_address = parsed_args.game_ip
        self._port = parsed_args.game_port
        self._initial_number_of_turns = parsed_args.initial_number_of_turns
        self._keep_track_of_turns = parsed_args.keep_track_of_turns

        self._leader_moves_per_turn = parsed_args.leader_moves_per_turn
        self._follower_moves_per_turn = parsed_args.follower_moves_per_turn
        self._action_delay = parsed_args.action_delay
        self._generate_new_cards = parsed_args.generate_new_cards

        super(GameArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        str_rep: str = '*** Game arguments ***' \
                       '\n\tGame served on: %r:%r' \
                       '\n\tInitial number of turns: %r' \
                       '\n\tLeader/follower moves per turn: %r/%r' \
                       '\n\tKeep track of turns? %r' \
                       '\n\tGenerate new cards in Python? %r' % (self.get_ip_address(), self.get_port(),
                                                                 self.get_initial_number_of_turns(),
                                                                 self.get_leader_moves_per_turn(),
                                                                 self.get_follower_moves_per_turn(),
                                                                 self.keep_track_of_turns(), self.generate_new_cards())

        return str_rep

    def __eq__(self, other) -> bool:
        return True
