from __future__ import annotations

from typing import TYPE_CHECKING

from agent.environment import state_delta
from agent.simulation import python_game

if TYPE_CHECKING:
    from typing import Any, Dict, List
    from agent.config import evaluation_args
    from agent.config import game_args
    from agent.data import instruction_example
    from agent.environment import agent
    from agent.model.model_wrappers import action_generator_model_wrapper


def execution_accuracies(model: action_generator_model_wrapper.ActionGeneratorModelWrapper,
                         examples: List[instruction_example.InstructionExample],
                         game_arguments: game_args.GameArgs,
                         evaluation_arguments: evaluation_args.EvaluationArgs):
    sequence_accuracy_sum = 0.
    exact_state_sum = 0.
    position_sum = 0.
    environment_accuracy_sum = 0.
    card_state_accuracy_sum = 0.

    auxiliary_predictions_dict: Dict[str, Any] = dict()

    for example in examples:
        game_server: python_game.PythonGame = python_game.PythonGame(game_arguments,
                                                                     example.get_hexes(),
                                                                     example.get_objects(),
                                                                     example.get_initial_state(),
                                                                     leader_actions=None)

        game_server.reset_state(leader_actions=example.get_leader_actions(),
                                state=example.get_initial_state(),
                                expected_sets=example.get_expected_sets(),
                                num_steps_remaining=example.get_number_of_moves_in_first_turn())

        correct_sequence: List[str] = example.get_action_sequence()
        correct_final_follower: agent.Agent = example.get_final_state().follower

        predicted_sequence, auxiliary_predictions, _ = \
            model.get_predictions(example, game_server=game_server, evaluation_arguments=evaluation_arguments)
        predicted_sequence = [str(action) for action in predicted_sequence]
        if game_server.valid_state():
            game_server.finish_all_leader_actions()

        predicted_follower = game_server.get_game_info().follower

        auxiliary_predictions_dict[example.get_id()] = auxiliary_predictions

        cards_same = state_delta.card_states_equal(example.get_final_state().cards, game_server.get_game_info().cards)

        if correct_sequence == predicted_sequence:
            sequence_accuracy_sum += 1.

        if cards_same:
            card_state_accuracy_sum += 1.

        if correct_final_follower.get_position() == predicted_follower.get_position():
            position_sum += 1.
            if cards_same:
                environment_accuracy_sum += 1.
                if correct_final_follower.get_rotation() == predicted_follower.get_rotation():
                    exact_state_sum += 1.

    return (sequence_accuracy_sum / len(examples),
            position_sum / len(examples),
            exact_state_sum / len(examples),
            environment_accuracy_sum / len(examples),
            card_state_accuracy_sum / len(examples),
            auxiliary_predictions_dict)
