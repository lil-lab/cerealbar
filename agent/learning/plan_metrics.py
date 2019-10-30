import random
from typing import Any, Dict, List

import numpy as np
import torch

from agent.data import aggregated_instruction_example
from agent.data import instruction_example
from agent.environment import position
from agent.learning import auxiliary
from agent.learning import plan_losses
from agent.learning import util as learning_util
from agent.model.model_wrappers import model_wrapper
from agent import util


def add_trajectory_metrics(metric_results: Dict[str, Any],
                           example: instruction_example.InstructionExample,
                           action_index: int,
                           predicted_map_distribution: torch.Tensor,
                           full_observability: bool,
                           weight_by_time: bool) -> None:
    """
    Computes and adds metrics for trajectory cross-entropy.
    :param metric_results: The dictionary to add the results to.
    :param example: The example to get the gold trajectory for.
    :param action_index: The index of the action to compute trajectory cross-entropy for.
    :param predicted_map_distribution: The predicted distribution over maps.
    :param weight_by_time: Whether points along the trajectory should be weighted by the time the agent spent in them.
    """
    metric_results[str(auxiliary.Auxiliary.TRAJECTORY) + ' xent'].append(
        plan_losses.compute_trajectory_loss(example,
                                            predicted_map_distribution,
                                            action_index,
                                            full_observability=full_observability,
                                            weight_by_time=weight_by_time).item())


def get_hexes_above_threshold(map_probabilities: torch.Tensor,
                              valid_positions: List[position.Position] = None) -> List[position.Position]:
    """
    :param map_probabilities: Tensor the size of the map containing probabilities for each hex of reaching that hex.
    :param valid_positions: A list containing the valid positions to return.
    :return: List of positions in the map with over 0.5 probability.
    """
    predicted_positions: List[position.Position] = list()
    width, depth = map_probabilities.size()
    for x_pos in range(width):
        for y_pos in range(depth):
            if map_probabilities[x_pos][y_pos].item() > 0.5:
                pos: position.Position = position.Position(x_pos, y_pos)
                if valid_positions is None or pos in valid_positions:
                    predicted_positions.append(pos)
    return predicted_positions


def add_card_metrics(metric_results: Dict[str, Any],
                     predicted_positions: List[position.Position],
                     gold_positions: List[position.Position],
                     prefix: str) -> None:
    """ Computes and adds metrics for card predictions.
    :param metric_results: The dictionary to add the results to.
    :param predicted_positions: The predicted positions.
    :param gold_positions: The gold positions.
    :param prefix: The prefix to log with.
    """
    accuracy, precision, recall = learning_util.evaluate_set_precision_recall(predicted_positions, gold_positions)
    metric_results[prefix + ' accuracy'].append(accuracy)
    metric_results[prefix + ' precision'].append(precision)
    metric_results[prefix + ' recall'].append(recall)


def plan_metric_results(model: model_wrapper.ModelWrapper,
                        examples: Dict[str, instruction_example.InstructionExample]) -> Dict[str, float]:
    """ Evaluates a hex predictor model over a set of examples. """
    # TODO: if all trajectory, then evaluate for all positions along the path

    full_observability: bool = model.get_arguments().get_state_rep_args().full_observability()

    eval_ids = instruction_example.get_example_action_index_pairs(
        examples, full_observability,
        model.get_arguments().get_state_rep_args().observability_refresh_rate())

    auxiliary_predictions_dict = dict()
    with util.get_progressbar('evaluating...', len(examples)) as pbar:
        for i, (example_id, action_idx) in enumerate(eval_ids):
            pbar.update(i)
            auxiliaries = model.get_predictions(examples[example_id], action_idx)
            auxiliary_predictions_dict[(example_id, action_idx)] = auxiliaries

    metric_results: Dict[str, Any] = dict()

    if auxiliary.Auxiliary.INTERMEDIATE_GOALS in model.get_auxiliaries():
        metric_results[str(auxiliary.Auxiliary.INTERMEDIATE_GOALS) + ' precision'] = list()
        metric_results[str(auxiliary.Auxiliary.INTERMEDIATE_GOALS) + ' recall'] = list()
        metric_results[str(auxiliary.Auxiliary.INTERMEDIATE_GOALS) + ' accuracy'] = list()
    if auxiliary.Auxiliary.FINAL_GOALS in model.get_auxiliaries():
        metric_results[str(auxiliary.Auxiliary.FINAL_GOALS) + ' precision'] = list()
        metric_results[str(auxiliary.Auxiliary.FINAL_GOALS) + ' recall'] = list()
        metric_results[str(auxiliary.Auxiliary.FINAL_GOALS) + ' accuracy'] = list()

    if auxiliary.Auxiliary.TRAJECTORY in model.get_auxiliaries():
        metric_results[str(auxiliary.Auxiliary.TRAJECTORY) + ' xent'] = list()

    if auxiliary.Auxiliary.OBSTACLES in model.get_auxiliaries():
        metric_results[str(auxiliary.Auxiliary.OBSTACLES) + ' accuracy'] = list()
        metric_results[str(auxiliary.Auxiliary.OBSTACLES) + ' recall'] = list()
        metric_results[str(auxiliary.Auxiliary.OBSTACLES) + ' precision'] = list()

    if auxiliary.Auxiliary.AVOID_LOCS in model.get_auxiliaries():
        metric_results[str(auxiliary.Auxiliary.AVOID_LOCS) + ' accuracy'] = list()
        metric_results[str(auxiliary.Auxiliary.AVOID_LOCS) + ' recall'] = list()
        metric_results[str(auxiliary.Auxiliary.AVOID_LOCS) + ' precision'] = list()

    if auxiliary.Auxiliary.IMPLICIT in model.get_auxiliaries():
        for i in range(model.get_arguments().get_state_encoder_args().get_encoder_depth()):
            metric_results[str(auxiliary.Auxiliary.IMPLICIT) + ' accuracy layer ' + str(i)] = list()

    for example_id, action_index in eval_ids:
        example = examples[example_id]

        if full_observability:
            all_card_positions = [card.get_position() for card in example.get_initial_cards()]
        else:
            all_card_positions = sorted(list(set([card.get_position() for card in example.get_partial_observations()[
                action_index].get_card_beliefs()])))

        auxiliary_predictions = auxiliary_predictions_dict[(example.get_id(), action_index)]

        # TODO: Should this be computed differently? E.g. depending on whether the encoded information is updated
        gold_position_set = sorted(list(set([card.get_position() for card in example.get_touched_cards()])))

        if not full_observability:
            # Limit the gold set to be only the cards that are visible on the board
            gold_position_set = sorted(list(set(gold_position_set) & set(all_card_positions)))

        if auxiliary.Auxiliary.FINAL_GOALS in model.get_auxiliaries():
            add_card_metrics(metric_results,
                             sorted(list(set(get_hexes_above_threshold(
                                 auxiliary_predictions[auxiliary.Auxiliary.FINAL_GOALS][0],
                                 all_card_positions)))),
                             gold_position_set,
                             str(auxiliary.Auxiliary.FINAL_GOALS))

        if auxiliary.Auxiliary.INTERMEDIATE_GOALS in model.get_auxiliaries():
            add_card_metrics(metric_results,
                             sorted(list(set(get_hexes_above_threshold(
                                 auxiliary_predictions[auxiliary.Auxiliary.INTERMEDIATE_GOALS],
                                 all_card_positions)))),
                             gold_position_set,
                             str(auxiliary.Auxiliary.INTERMEDIATE_GOALS))

        if auxiliary.Auxiliary.AVOID_LOCS in model.get_auxiliaries():
            # These are all the positions where cards are except (1) the cards that should be touched and (2) the card
            # it starts on
            gold_positions: List[position.Position] = \
                sorted(list(set([card.get_position() for card in example.get_initial_cards()
                                 if card.get_position() not in
                                 [card.get_position() for card in example.get_touched_cards(
                                     include_start_position=True)]])))

            if not full_observability:
                # Limit the gold set to be only the cards that are visible on the board
                gold_positions = sorted(list(set(gold_positions) & set(all_card_positions)))

            pred_positions: List[position.Position] = \
                sorted(list(set(get_hexes_above_threshold(auxiliary_predictions[auxiliary.Auxiliary.AVOID_LOCS][0],
                                                          all_card_positions))))
            acc, prec, recall = learning_util.evaluate_set_precision_recall(pred_positions, gold_positions)
            metric_results[str(auxiliary.Auxiliary.AVOID_LOCS) + ' accuracy'].append(acc)
            metric_results[str(auxiliary.Auxiliary.AVOID_LOCS) + ' precision'].append(prec)
            metric_results[str(auxiliary.Auxiliary.AVOID_LOCS) + ' recall'].append(recall)

        if auxiliary.Auxiliary.TRAJECTORY in model.get_auxiliaries():
            add_trajectory_metrics(metric_results,
                                   example,
                                   action_index,
                                   auxiliary_predictions[auxiliary.Auxiliary.TRAJECTORY],
                                   full_observability,
                                   model.get_arguments().get_decoder_args().weight_trajectory_by_time())

        if auxiliary.Auxiliary.OBSTACLES in model.get_auxiliaries():
            gold_positions: List[position.Position] = sorted(list(set(example.get_obstacle_positions())))
            pred_positions: List[position.Position] = \
                sorted(list(set(get_hexes_above_threshold(auxiliary_predictions[auxiliary.Auxiliary.OBSTACLES][0]))))

            if not full_observability:
                # Limit the gold and predicted positions only to the visible positions.
                gold_positions = sorted(list(set(gold_positions)
                                             & example.get_partial_observations()[action_index].observed_positions()))
                pred_positions = sorted(list(set(pred_positions)
                                             & example.get_partial_observations()[action_index].observed_positions()))

            acc, prec, recall = learning_util.evaluate_set_precision_recall(pred_positions, gold_positions)
            metric_results[str(auxiliary.Auxiliary.OBSTACLES) + ' accuracy'].append(acc)
            metric_results[str(auxiliary.Auxiliary.OBSTACLES) + ' precision'].append(prec)
            metric_results[str(auxiliary.Auxiliary.OBSTACLES) + ' recall'].append(recall)

        if auxiliary.Auxiliary.IMPLICIT in model.get_auxiliaries():
            implicit_preds = auxiliary_predictions[auxiliary.Auxiliary.IMPLICIT].tolist()

            for i, pred in enumerate(implicit_preds):
                label = isinstance(example, aggregated_instruction_example.AggregatedInstructionExample) and \
                        example.implicit()
                pred_label = pred > 0.5

                if label == pred_label:
                    metric_results[str(auxiliary.Auxiliary.IMPLICIT) + ' accuracy layer ' + str(i)].append(1.)
                else:
                    metric_results[str(auxiliary.Auxiliary.IMPLICIT) + ' accuracy layer ' + str(i)].append(0.)

    # Compute the means
    final_results: Dict[str, float] = dict()
    for key, value in metric_results.items():
        final_results[key] = float(np.mean(np.array(value)))
    return final_results
