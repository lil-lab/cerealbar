from typing import Any, Dict, List, Union

import torch
from torch import nn

from agent import util
from agent.config import training_args
from agent.data import aggregated_instruction_example
from agent.data import instruction_example
from agent.environment import util as environment_util
from agent.learning import auxiliary


class SpatialSoftmax2d(nn.Module):

    def __init__(self, log=False):
        super(SpatialSoftmax2d, self).__init__()
        if log:
            self.softmax = nn.LogSoftmax(dim=1)
        else:
            self.softmax = nn.Softmax(dim=1)

    def forward(self, images):
        batch_size = images.size(0)
        num_channels = images.size(1)
        height = images.size(2)
        width = images.size(3)

        images = images.view([batch_size * num_channels, width * height])
        img_out = self.softmax(images)
        img_out = img_out.view([batch_size, num_channels, height, width])

        return img_out


class CrossEntropy2d(nn.Module):

    def __init__(self):
        super(CrossEntropy2d, self).__init__()
        self._logsoftmax = SpatialSoftmax2d(log=True)

    def forward(self, pred, labels):
        x = - labels * self._logsoftmax(pred)
        # Sum over spatial dimensions:
        x = x.sum(2).sum(2)
        # Average over channels and batches
        loss = torch.mean(x)
        return loss


def compute_trajectory_loss(example: Union[instruction_example.InstructionExample,
                                           aggregated_instruction_example.AggregatedInstructionExample],
                            predicted_map_distribution: torch.Tensor,
                            action_index: int,
                            weight_by_time: bool,
                            full_observability: bool):
    gold_map = example.get_correct_trajectory_distribution(weight_by_time=weight_by_time,
                                                           full_observability=full_observability,
                                                           action_index=action_index)
    return CrossEntropy2d()(predicted_map_distribution,
                            torch.tensor(gold_map).float().unsqueeze(0).unsqueeze(0).to(util.DEVICE))


def get_auxiliaries_from_args(args: training_args.TrainingArgs,
                              finetune: bool) -> Dict[auxiliary.Auxiliary, float]:
    auxiliaries: Dict[auxiliary.Auxiliary, float] = dict()

    trajectory_coefficient = args.get_auxiliary_coefficient_trajectory_distribution(finetune)
    if trajectory_coefficient > 0.:
        auxiliaries[auxiliary.Auxiliary.TRAJECTORY] = trajectory_coefficient

    intermediate_goal_coefficient = args.get_auxiliary_coefficient_intermediate_goal_probabilities(finetune)
    if intermediate_goal_coefficient > 0.:
        auxiliaries[auxiliary.Auxiliary.INTERMEDIATE_GOALS] = intermediate_goal_coefficient

    final_goal_coefficient = args.get_auxiliary_coefficient_final_goal_probabilities(finetune)
    if final_goal_coefficient > 0.:
        auxiliaries[auxiliary.Auxiliary.FINAL_GOALS] = final_goal_coefficient

    obstacle_coefficient = args.get_auxiliary_coefficient_obstacle_probabilities(finetune)
    if obstacle_coefficient > 0.:
        auxiliaries[auxiliary.Auxiliary.OBSTACLES] = obstacle_coefficient

    avoid_coefficient = args.get_auxiliary_coefficient_avoid_probabilities(finetune)
    if avoid_coefficient > 0.:
        auxiliaries[auxiliary.Auxiliary.AVOID_LOCS] = avoid_coefficient

    implicit_coefficient = args.get_auxiliary_coefficient_implicit_actions()
    if implicit_coefficient > 0.:
        auxiliaries[auxiliary.Auxiliary.IMPLICIT] = implicit_coefficient

    return auxiliaries


def compute_per_example_auxiliary_losses(example: Union[instruction_example.InstructionExample,
                                                        aggregated_instruction_example.AggregatedInstructionExample],
                                         example_idx: int,
                                         auxiliary_dict: Dict[auxiliary.Auxiliary, Any],
                                         auxiliaries: List[auxiliary.Auxiliary],
                                         auxiliary_losses: Dict[auxiliary.Auxiliary, List[torch.Tensor]],
                                         traj_weight_by_time: bool,
                                         full_observability: bool,
                                         action_idx: int = 0):
    intermediate_goal_scores: List[torch.Tensor] = list()
    avoid_scores: List[torch.Tensor] = list()
    final_goal_scores: List[torch.Tensor] = list()
    final_reach_labels: List[torch.Tensor] = list()

    avoid_labels: List[torch.Tensor] = list()

    # Get labels and matched predictions for goals and places to avoid
    touched_positions = [card.get_position() for card in example.get_touched_cards()]
    touched_plus_initial = [card.get_position() for card in example.get_touched_cards(include_start_position=True)]
    if full_observability:
        for card in example.get_state_deltas()[action_idx].cards:
            position = card.get_position()

            # If it's to be touched, give a 1 label
            if position in touched_positions:
                final_reach_labels.append(torch.tensor(1.))
            else:
                final_reach_labels.append(torch.tensor(0.))

            if auxiliary.Auxiliary.INTERMEDIATE_GOALS in auxiliaries:
                intermediate_goal_scores.append(
                    auxiliary_dict[auxiliary.Auxiliary.INTERMEDIATE_GOALS][example_idx][position.x][position.y])

            if auxiliary.Auxiliary.FINAL_GOALS in auxiliaries:
                final_goal_scores.append(
                    auxiliary_dict[auxiliary.Auxiliary.FINAL_GOALS].squeeze(1)[example_idx][position.x][position.y])

            if auxiliary.Auxiliary.AVOID_LOCS in auxiliaries:
                avoid_scores.append(
                    auxiliary_dict[auxiliary.Auxiliary.AVOID_LOCS][example_idx][0][position.x][position.y])

                # Currently, should predict all cards except the one it's currently on
                if position in touched_plus_initial:
                    avoid_labels.append(torch.tensor(0.))
                else:
                    avoid_labels.append(torch.tensor(1.))
    else:
        # Only compute loss over cards that are believed to exist. Other cards are impossible to predict.
        for card in example.get_partial_observations()[action_idx].get_card_beliefs():
            position = card.get_position()

            # If it is touched by the agent, give it a 1 label
            # Goals may not get a loss if:
            #   - If the card is a goal but hasn't been observed yet by the agent.
            #   - If the card disappeared already because a set was made.
            # The label may be "inconsistent" if:
            #   - The card was already touched by the agent (i.e., no longer a goal), the label will be 1 (it is a goal)

            # TODO: Do we want predict goals according to updated card information (including selection and existence
            #  of cards that might change as the agent is moving), or according to card information as it appeared at
            #  the beginning of the instruction? Two considerations:
            #       - Cards that have disappeared due to a set being made get no loss for actions after the card has
            #         disappeared. This might be bad because it's inconsistent wrt. the instruction, which might mention
            #         to get a card that is no longer on the board.
            #       - Cards whose selection has changed may look as though they are a goal even if they've been toggled
            #         already. This is also inconsistent wrt. the instruction (e.g., might say to select a card when
            #         already selected).
            # Currently, predictions are made wrt. updated information.
            if position in touched_positions:
                final_reach_labels.append(torch.tensor(1.))
            else:
                final_reach_labels.append(torch.tensor(0.))

            if auxiliary.Auxiliary.INTERMEDIATE_GOALS in auxiliaries:
                intermediate_goal_scores.append(
                    auxiliary_dict[auxiliary.Auxiliary.INTERMEDIATE_GOALS][example_idx][position.x][position.y])

            if auxiliary.Auxiliary.FINAL_GOALS in auxiliaries:
                final_goal_scores.append(
                    auxiliary_dict[auxiliary.Auxiliary.FINAL_GOALS].squeeze(1)[example_idx][position.x][position.y])

            # This is also currently updating wrt. newest card information, including if new cards appear,
            # which will (once they appear) get a label of 0.

            # TODO: Should this also be computed with most recent card information? (What it's doing now)
            if auxiliary.Auxiliary.AVOID_LOCS in auxiliaries:
                avoid_scores.append(
                    auxiliary_dict[auxiliary.Auxiliary.AVOID_LOCS][example_idx][0][position.x][position.y])

                # Currently, should predict all cards except the one it's currently on
                if position in touched_plus_initial:
                    avoid_labels.append(torch.tensor(0.))
                else:
                    avoid_labels.append(torch.tensor(1.))

    # To compute the loss, flatten everything first
    if final_reach_labels:
        combined_labels = torch.stack(tuple(final_reach_labels)).to(util.DEVICE)

        if auxiliary.Auxiliary.INTERMEDIATE_GOALS in auxiliaries:
            if auxiliary.Auxiliary.INTERMEDIATE_GOALS not in auxiliary_losses:
                auxiliary_losses[auxiliary.Auxiliary.INTERMEDIATE_GOALS] = list()
            auxiliary_losses[auxiliary.Auxiliary.INTERMEDIATE_GOALS].append(
                nn.BCEWithLogitsLoss()(torch.stack(tuple(intermediate_goal_scores)), combined_labels))

        if auxiliary.Auxiliary.FINAL_GOALS in auxiliaries:
            if auxiliary.Auxiliary.FINAL_GOALS not in auxiliary_losses:
                auxiliary_losses[auxiliary.Auxiliary.FINAL_GOALS] = list()
            auxiliary_losses[auxiliary.Auxiliary.FINAL_GOALS].append(
                nn.BCEWithLogitsLoss()(torch.stack(tuple(final_goal_scores)), combined_labels))

    if avoid_labels:
        if auxiliary.Auxiliary.AVOID_LOCS in auxiliaries:
            if auxiliary.Auxiliary.AVOID_LOCS not in auxiliary_losses:
                auxiliary_losses[auxiliary.Auxiliary.AVOID_LOCS] = list()
            auxiliary_losses[auxiliary.Auxiliary.AVOID_LOCS].append(
                nn.BCEWithLogitsLoss()(torch.stack(tuple(avoid_scores)),
                                       torch.stack(tuple(avoid_labels)).to(util.DEVICE)))

    if auxiliary.Auxiliary.IMPLICIT in auxiliaries:
        if auxiliary.Auxiliary.IMPLICIT not in auxiliary_losses:
            auxiliary_losses[auxiliary.Auxiliary.IMPLICIT] = list()

        # It's implicit if it's an aggregated example and was marked as implicit (start position was far enough away
        # from correct start position).
        implicit_value: float = (1. if
                                 isinstance(example, aggregated_instruction_example.AggregatedInstructionExample) and
                                 example.implicit() else 0.)

        # Label is all 1s if the example is aggregated, otherwise it's all zeros.
        avg_layer_implicit_loss = \
            nn.BCEWithLogitsLoss()(
                auxiliary_dict[auxiliary.Auxiliary.IMPLICIT][example_idx],
                torch.tensor([implicit_value for _ in range(auxiliary_dict[auxiliary.Auxiliary.IMPLICIT].size(1))]).to(
                    util.DEVICE))
        auxiliary_losses[auxiliary.Auxiliary.IMPLICIT].append(avg_layer_implicit_loss)

    # Then the trajectory loss
    if auxiliary.Auxiliary.TRAJECTORY in auxiliaries:
        if auxiliary.Auxiliary.TRAJECTORY not in auxiliary_losses:
            auxiliary_losses[auxiliary.Auxiliary.TRAJECTORY] = list()
        auxiliary_losses[auxiliary.Auxiliary.TRAJECTORY].append(
            compute_trajectory_loss(example,
                                    auxiliary_dict[auxiliary.Auxiliary.TRAJECTORY][0][example_idx].unsqueeze(0),
                                    action_idx,
                                    traj_weight_by_time,
                                    full_observability))

    # Obstacle loss
    if auxiliary.Auxiliary.OBSTACLES in auxiliaries:
        if auxiliary.Auxiliary.OBSTACLES not in auxiliary_losses:
            auxiliary_losses[auxiliary.Auxiliary.OBSTACLES] = list()

            impassable_label: torch.Tensor = torch.zeros((environment_util.ENVIRONMENT_WIDTH,
                                                          environment_util.ENVIRONMENT_DEPTH)).float()
            impassable_score: torch.Tensor = auxiliary_dict[auxiliary.Auxiliary.OBSTACLES][example_idx][0]

            for position in example.get_obstacle_positions():
                impassable_label[position.x][position.y] = 1.

            if not full_observability:
                # Mask the predictions and labels so they are both zero on pixels that are not observed (loss will be
                # zero)
                state_mask = torch.zeros((environment_util.ENVIRONMENT_WIDTH,
                                          environment_util.ENVIRONMENT_DEPTH)).float()
                for position in example.get_partial_observations()[action_idx].lifetime_observed_positions():
                    state_mask[position.x][position.y] = 1.
                state_mask = state_mask.to(util.DEVICE)
                impassable_label = impassable_label.to(util.DEVICE)

                impassable_label = impassable_label * state_mask
                impassable_score = impassable_score * state_mask

            auxiliary_losses[auxiliary.Auxiliary.OBSTACLES].append(
                nn.BCEWithLogitsLoss()(impassable_score.view(1, -1),
                                       impassable_label.view(1, -1).to(util.DEVICE)))
