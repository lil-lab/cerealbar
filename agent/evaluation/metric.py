"""Contains the class defining a metric in the CerealBar game."""
# TODO: Use this in more places in the code.
from __future__ import annotations

from enum import Enum

from agent.environment import state_delta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.data import instruction_example
    from agent.environment import position
    from typing import List


class Metric(Enum):
    # Exact sequence accuracy.
    SEQUENCE_ACCURACY: str = 'SEQUENCE_ACCURACY'

    # Card accuracy for the final state.
    CARD_ACCURACY: str = 'CARD_ACCURACY'

    # Relaxed environment accuracy -- thresholded distance from correct location and no rotation requirement
    RELAXED_ENVIRONMENT_ACCURACY: str = 'RELAXED_ENVIRONMENT_ACCURACY'

    # Exact environment accuracy -- exact location and rotation must be correct
    EXACT_ENVIRONMENT_ACCURACY: str = 'EXACT_ENVIRONMENT_ACCURACY'

    # Distance from correct state
    AGENT_DISTANCE: str = 'AGENT_DISTANCE'

    # Score for a game
    SCORE: str = 'SCORE'

    PROPORTION_FOLLOWED_CASCADING: str = 'PROPORTION_FOLLOWED_CASCADING'

    PROPORTION_VALID_CASCADING: str = 'PROPORTION_VALID_CASCADING'

    PROPORTION_POINTS_CASCADING: str = "PROPORTION_POINTS_CASCADING"

    def __str__(self) -> str:
        return self.value


def manhattan_distance(a: position.Position, b: position.Position) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)


def compute_instruction_metric(metric: Metric,
                               example: instruction_example.InstructionExample,
                               predicted_instruction_sequence: List[str],
                               final_state: state_delta.StateDelta,
                               distance_threshold: int = 0) -> float:
    correct_final_state: state_delta.StateDelta = example.get_final_state()
    card_same = state_delta.card_states_equal(correct_final_state.cards, final_state.cards)

    if metric == Metric.SEQUENCE_ACCURACY:
        return 1. if example.get_action_sequence() == predicted_instruction_sequence else 0.
    elif metric == Metric.CARD_ACCURACY:
        return 1. if card_same else 0.
    elif metric == Metric.RELAXED_ENVIRONMENT_ACCURACY:
        return 1. if (card_same and manhattan_distance(final_state.follower.get_position(),
                                                       correct_final_state.follower.get_position())
                      <= distance_threshold) else 0.
    elif metric == Metric.EXACT_ENVIRONMENT_ACCURACY:
        return 1. if (card_same
                      and final_state.follower.get_position() == correct_final_state.follower.get_position()
                      and final_state.follower.get_rotation() == correct_final_state.follower.get_rotation()) else 0.
    elif metric == Metric.AGENT_DISTANCE:
        return manhattan_distance(final_state.follower.get_position(), correct_final_state.follower.get_position())
    else:
        raise ValueError('Metric %r not supported by compute_instruction_metric' % metric)


INSTRUCTION_METRICS: List[Metric] = [Metric.SEQUENCE_ACCURACY, Metric.CARD_ACCURACY,
                                     Metric.RELAXED_ENVIRONMENT_ACCURACY, Metric.EXACT_ENVIRONMENT_ACCURACY,
                                     Metric.AGENT_DISTANCE]
