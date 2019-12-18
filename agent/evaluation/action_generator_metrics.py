from __future__ import annotations

import numpy as np
from typing import TYPE_CHECKING

from agent import util
from agent.data import in_game_example
from agent.data import instruction_example
from agent.data import partial_observation
from agent.environment import state_delta
from agent.evaluation import evaluation_logger
from agent.evaluation import metric
from agent.simulation import python_game
from agent.simulation import server
from agent.simulation import unity_game
from agent.simulation import game

if TYPE_CHECKING:
    from typing import Dict, List
    from agent.config import evaluation_args
    from agent.config import game_args
    from agent.data import cereal_bar_game
    from agent.environment import card
    from agent.model.model_wrappers import action_generator_model_wrapper


def sample_for_game_without_reset(game_arguments: game_args.GameArgs,
                                  evaluation_arguments: evaluation_args.EvaluationArgs,
                                  evaluated_game: cereal_bar_game.CerealBarGame,
                                  model: action_generator_model_wrapper.ActionGeneratorModelWrapper,
                                  logger: evaluation_logger.EvaluationLogger):
    number_instructions_followed: List[int] = list()
    score_increases: List[float] = list()

    for i, beginning_example in enumerate(evaluated_game.get_examples()):
        # TODO: Allow to run with a Unity server
        game_server: game.Game = python_game.PythonGame(game_arguments,
                                                        evaluated_game.get_hexes(),
                                                        evaluated_game.get_objects(),
                                                        evaluated_game.get_initial_state(),
                                                        verbose=True)

        # Reset to the correct initial state in the game simulator.
        game_server.reset_state(leader_actions=beginning_example.get_leader_actions(limit_to_instruction=False),
                                state=beginning_example.get_initial_state(),
                                num_steps_remaining=beginning_example.get_number_of_moves_in_first_turn(),
                                expected_sets=beginning_example.get_expected_sets(),
                                num_instructions=beginning_example.get_number_of_instructions_when_starting())

        # Keep track of the partial observations starting from the beginning of this instruction.
        current_partial_observation: partial_observation.PartialObservation = \
            beginning_example.get_partial_observations()[0]

        followed_instruction_index: int = 0

        for j, executed_example in enumerate(evaluated_game.get_examples()[i:]):
            temporary_example = in_game_example.InGameExample(game_server.get_game_info(),
                                                              evaluated_game.get_hexes(),
                                                              evaluated_game.get_objects(),
                                                              executed_example.get_instruction(),
                                                              current_partial_observation,
                                                              executed_example.get_touched_cards())
            _, _, visited_states, current_partial_observation = model.get_predictions(
                temporary_example, game_server, evaluation_arguments, logger=logger)

            expected_cards_changed: List[card.Card] = executed_example.get_touched_cards(allow_duplicates=False)

            filtered_expected_cards: List[card.Card] = list()
            for card1 in expected_cards_changed:
                for card2 in visited_states[0].cards:
                    if card1 == card2:
                        filtered_expected_cards.append(card1)

            changed_cards = instruction_example.get_changed_cards_along_trajectory(visited_states)
            changed_expected_cards = state_delta.card_states_equal(filtered_expected_cards, changed_cards)

            if changed_expected_cards:
                followed_instruction_index += 1

            if not changed_expected_cards or not game_server.valid_state():
                break

        number_instructions_followed.append(followed_instruction_index)
        possible_points_scored: int = len(evaluated_game.get_expected_sets())
        if possible_points_scored:
            score_increases.append(float(game_server.get_score()) / possible_points_scored)

    possible_num_followed = len(evaluated_game.get_examples()) * (len(evaluated_game.get_examples()) + 1) / 2

    return (float(np.sum(np.array(number_instructions_followed))) / possible_num_followed,
            float(np.mean(np.array(score_increases))) if score_increases else None)


def execution_accuracies(model: action_generator_model_wrapper.ActionGeneratorModelWrapper,
                         game_arguments: game_args.GameArgs,
                         evaluation_arguments: evaluation_args.EvaluationArgs,
                         instruction_examples: List[instruction_example.InstructionExample] = None,
                         game_examples: List[cereal_bar_game.CerealBarGame] = None,
                         log: bool = True):

    logger: evaluation_logger.EvaluationLogger = evaluation_logger.EvaluationLogger(
        evaluation_arguments.get_evaluation_results_filename(), log)

    metric_dict: Dict[metric.Metric, List[float]] = {metric.Metric.SCORE: list(),
                                                     metric.Metric.CARD_ACCURACY: list(),
                                                     metric.Metric.SEQUENCE_ACCURACY: list(),
                                                     metric.Metric.RELAXED_ENVIRONMENT_ACCURACY: list(),
                                                     metric.Metric.AGENT_DISTANCE: list(),
                                                     metric.Metric.EXACT_ENVIRONMENT_ACCURACY: list(),
                                                     metric.Metric.PROPORTION_POINTS_CASCADING: list(),
                                                     metric.Metric.PROPORTION_FOLLOWED_CASCADING: list(),
                                                     metric.Metric.PROPORTION_VALID_CASCADING: list()}

    game_server_socket = None
    if evaluation_arguments.use_unity():
        game_server_socket: server.ServerSocket = server.ServerSocket(game_arguments.get_ip_address(),
                                                                      game_arguments.get_port())
        game_server_socket.start_unity()

    if instruction_examples:
        with util.get_progressbar('evaluating individual instructions...', len(instruction_examples)) as pbar:
            for i, example in enumerate(instruction_examples):
                pbar.update(i)

                logger.log('***** Example #' + example.get_id() + ' *****')
                logger.log('Instruction: ' + ' '.join(example.get_instruction()))

                # Set up the server and reset the state
                if evaluation_arguments.use_unity():
                    game_server: unity_game.UnityGame = unity_game.UnityGame(game_arguments,
                                                                             game_server_socket,
                                                                             seed=example.get_seed(),
                                                                             auto_end_turn=True)
                else:
                    game_server: python_game.PythonGame = python_game.PythonGame(game_arguments,
                                                                                 example.get_hexes(),
                                                                                 example.get_objects(),
                                                                                 example.get_initial_state(),
                                                                                 leader_actions=None)

                game_server.reset_state(leader_actions=example.get_leader_actions(),
                                        state=example.get_initial_state(),
                                        expected_sets=example.get_expected_sets(),
                                        num_steps_remaining=example.get_number_of_moves_in_first_turn())
                game_server.send_command(' '.join(example.get_instruction()))

                # Run inference
                predicted_sequence, auxiliary_predictions, _, _ = \
                    model.get_predictions(example, game_server=game_server, evaluation_arguments=evaluation_arguments,
                                          logger=logger)

                predicted_sequence = [str(action) for action in predicted_sequence]

                if game_server.valid_state():
                    game_server.finish_all_leader_actions()

                # Compute the metrics
                metric_dict[metric.Metric.SCORE].append(game_server.get_score())
                for metric_name in metric.INSTRUCTION_METRICS:
                    resulting_metric: float = metric.compute_instruction_metric(
                        metric_name, example, predicted_sequence, game_server.get_game_info(),
                        evaluation_arguments.get_distance_threshold())

                    metric_dict[metric_name].append(resulting_metric)

    if game_examples:
        metric_dict[metric.Metric.PROPORTION_FOLLOWED_CASCADING] = list()
        metric_dict[metric.Metric.PROPORTION_POINTS_CASCADING] = list()
        with util.get_progressbar('running full game inference', len(game_examples)) as pbar:
            for num_games, evaluated_game in enumerate(game_examples):
                pbar.update(num_games)
                average_number_instructions_followed, average_score_increase = \
                    sample_for_game_without_reset(game_arguments,
                                                  evaluation_arguments,
                                                  evaluated_game,
                                                  model,
                                                  logger)
                metric_dict[metric.Metric.PROPORTION_FOLLOWED_CASCADING].append(average_number_instructions_followed)
                metric_dict[metric.Metric.PROPORTION_POINTS_CASCADING].append(average_score_increase)

    means_dict: Dict[metric.Metric, float] = dict()
    for metric_name, values in metric_dict.items():
        if values:
            means_dict[metric_name] = np.mean(np.array(values)).item()

            if 'ACCURACY' in str(metric_name) or metric_name == metric.Metric.PROPORTION_FOLLOWED_CASCADING:
                means_dict[metric_name] = 100. * means_dict[metric_name]

    logger.close()

    if evaluation_arguments.use_unity():
        game_server_socket.close()

    return means_dict
