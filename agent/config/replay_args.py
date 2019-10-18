"""Contains arguments on how to replay recorded games."""
from __future__ import annotations

from distutils.util import strtobool
from typing import TYPE_CHECKING

from agent.config import args

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace


class ReplayArgs(args.Args):
    def __init__(self, parser: ArgumentParser):
        super(ReplayArgs, self).__init__()

        parser.add_argument('--game_id',
                            default='',
                            type=str,
                            help='The ID of the game to replay.')
        parser.add_argument('--game_directory',
                            type=str,
                            help='The directory containing the stored game information. All JSON files will be '
                                 'prefixed with games_.')
        parser.add_argument('--speed',
                            type=float,
                            help='The speed to replay back each game, as a factor of the original speed.')
        parser.add_argument('--realtime',
                            default=True,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to replay in realtime or not.')
        parser.add_argument('--instruction_id',
                            default='',
                            type=str,
                            help='The instruction to replay.')

        self._game_id: str = ''
        self._instruction_id: str = ''
        self._game_directory: str = ''
        self._playback_speed: float = 1.
        self._is_realtime: bool = True

    def get_game_id(self) -> str:
        self.check_initialized()
        return self._game_id

    def get_game_directory(self) -> str:
        self.check_initialized()
        return self._game_directory

    def get_playback_speed(self) -> float:
        self.check_initialized()
        return self._playback_speed

    def is_realtime(self) -> bool:
        self.check_initialized()
        return self._is_realtime

    def get_instruction_id(self) -> str:
        self.check_initialized()
        return self._instruction_id

    def interpret_args(self, parsed_args: Namespace) -> None:
        self._game_id = parsed_args.game_id
        self._game_directory = parsed_args.game_directory
        self._playback_speed = parsed_args.speed
        self._is_realtime = parsed_args.realtime
        self._instruction_id = parsed_args.instruction_id

        super(ReplayArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        str_rep: str = '*** Replay arguments ***' \
                       '\n\tGame ID: %r' \
                       '\n\tInstruction ID: %r' \
                       '\n\tGame directory: %r' \
                       '\n\tReplay speed: %r' \
                       '\n\tRealtime replay? %r' % (self.get_game_id(), self.get_instruction_id(),
                                                    self.get_game_directory(), self.get_playback_speed(),
                                                    self.get_instruction_id())

        return str_rep
