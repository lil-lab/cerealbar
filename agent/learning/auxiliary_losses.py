from __future__ import annotations

from typing import TYPE_CHECKING

from agent.learning import auxiliary


if TYPE_CHECKING:
    from agent.config import training_args
    from typing import Dict


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
