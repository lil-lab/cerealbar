""" Contains different action type classes for actions used in the Cereal Bar data.

GameplayAction differs from agent_actions.AgentAction because it includes actions about the game itself, changes in state, and timing.
Its intended use is to turn raw data from the logged games into are more usable class.

Functions:
    tokenize. Takes a sentence and splits into a list of strings.
    process_actions. Returns a list of Action given a dictionary representation of actions.
    process_action. Takes a dictionary-represented action and returns an Action.

Classes:
    GameplayAction (ABC): Abstract class for an action.
    MovementAction (Action): Class for a movement action.
    InstructionAction (Action): Class for an instruction action.
    EndTurnAction (Action): Class for ending a turn action.
    FinishCommandAction (Action): Class for finishing a command.

"""
from __future__ import annotations
import nltk

from abc import ABC
from datetime import datetime
from typing import TYPE_CHECKING

from agent.environment import agent_actions
from agent.environment import environment_objects


if TYPE_CHECKING:
    from agent.config import data_args
    from agent.environment import state_delta
    from typing import Any, Dict, List

DATE_FORMAT: str = '%Y-%m-%d %H:%M:%S.%f'


def process_actions(json_actions: List[Dict[str, Any]],
                    data_arguments: data_args.DataArgs) -> List[GameplayAction]:
    actions: List[GameplayAction] = []

    for action in json_actions:
        if action['type'] == 'movement' and action['move_id'] < 0:
            continue
        resulting_action: GameplayAction = process_action(action, data_arguments)
        if resulting_action:
            actions.append(resulting_action)
    return actions


def process_action(action: Dict[str, Any],
                   data_arguments: data_args.DataArgs) -> GameplayAction:
    if action['type'] == 'movement':
        return MovementAction(action)
    elif action['type'] == 'instruction':
        return InstructionAction(action, data_arguments)
    elif action['type'] == 'finish command':
        return FinishCommandAction(action)
    elif action['type'] == 'end turn':
        # Don't keep track of begin turn actions, as these will just happen automatically.
        return EndTurnAction(action)


def tokenize(text: str, case_sensitive: bool) -> List[str]:
    return nltk.word_tokenize(text) if case_sensitive else nltk.word_tokenize(text.lower())


class GameplayAction(ABC):
    def __init__(self, time):
        self._time = datetime.strptime(time, DATE_FORMAT)


class MovementAction(GameplayAction):
    def __init__(self, json_object: Dict[str, Any]):
        super(MovementAction, self).__init__(json_object['time'])

        self._agent: environment_objects.ObjectType = environment_objects.ObjectType.LEADER if \
            json_object['character'] == 'Leader' else environment_objects.ObjectType.FOLLOWER
        self._action: agent_actions.AgentAction = agent_actions.AgentAction(json_object['action'])

        self._card_result = json_object['card_result']
        self._set_result = json_object['set_result']

        self._prior_game_info: state_delta.StateDelta = None
        self._posterior_game_info: state_delta.StateDelta = None

    def get_action(self) -> agent_actions.AgentAction:
        return self._action

    def get_agent(self) -> environment_objects.ObjectType:
        return self._agent

    def get_prior_game_info(self) -> state_delta.StateDelta:
        if not self._prior_game_info:
            raise ValueError('Prior game info was not set')
        return self._prior_game_info

    def get_posterior_game_info(self) -> state_delta.StateDelta:
        if not self._posterior_game_info:
            raise ValueError('Posterior game info was not set')
        return self._posterior_game_info

    def set_game_info(self, game_info: state_delta.StateDelta, posterior_info: state_delta.StateDelta) -> None:
        if self._prior_game_info or self._posterior_game_info:
            raise ValueError('Prior or posterior game info is not already None')
        self._prior_game_info = game_info
        self._posterior_game_info = posterior_info


class InstructionAction(GameplayAction):
    def __init__(self, json_object: Dict[str, Any], data_arguments: data_args.DataArgs):
        super(InstructionAction, self).__init__(json_object['time'])

        self._instruction_index: int = json_object['instruction_id']
        self._instruction: str = json_object['instruction']
        self._tokenized_instruction: List[str] = tokenize(self._instruction,
                                                          data_arguments.case_sensitive())
        self._completed: bool = json_object['completed']

        self._agent_aligned_actions: List[agent_actions.AgentAction]
        if self._completed:
            self._agent_aligned_actions = \
                [agent_actions.AgentAction(action) for action in json_object['aligned_actions'] if action != 'initial']

    def get_instruction(self) -> str:
        return self._instruction

    def get_tokenized_instruction(self) -> List[str]:
        return self._tokenized_instruction

    def completed(self) -> bool:
        return self._completed

    def get_idx(self) -> int:
        return self._instruction_index


class EndTurnAction(GameplayAction):
    def __init__(self, json_object: Dict[str, Any]):
        super(EndTurnAction, self).__init__(json_object['time'])
        self._turn_index: int = json_object['turn_id']
        self._end_method: str = json_object['end_method']
        self._agent: environment_objects.ObjectType = environment_objects.ObjectType.LEADER if \
            json_object['character'] == 'Leader' else environment_objects.ObjectType.FOLLOWER

    def get_agent(self) -> environment_objects.ObjectType:
        return self._agent

    def is_automatic_end(self) -> bool:
        return self._end_method == 'No Commands to Follow'


class FinishCommandAction(GameplayAction):
    def __init__(self, json_object: Dict[str, Any]):
        super(FinishCommandAction, self).__init__(json_object['time'])
        self._instruction_index = json_object['instruction_id']

        self._prior_game_info: state_delta.StateDelta = None

    def get_prior_game_info(self) -> state_delta.StateDelta:
        if not self._prior_game_info:
            raise ValueError('Prior game info was not set')
        return self._prior_game_info

    def set_prior_game_info(self, game_info: state_delta.StateDelta) -> None:
        if self._prior_game_info:
            raise ValueError('Prior game info is not already None')
        self._prior_game_info = game_info
