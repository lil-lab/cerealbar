"""Contains arguments on training the model."""
import logging
import os
from argparse import ArgumentParser, Namespace
from distutils.util import strtobool
from enum import Enum
from typing import Any, Callable, List

import torch

from agent.config import args
from agent.config import model_args
from agent.evaluation import metric


class OptimizerType(Enum):
    ADAM: str = 'ADAM'
    ADAGRAD: str = 'ADAGRAD'
    RMSPROP: str = 'RMSPROP'
    SGD: str = 'SGD'

    def __str__(self) -> str:
        return self.value


class TrainingArgs(args.Args):
    def __init__(self, parser: ArgumentParser):
        super(TrainingArgs, self).__init__()

        # Bookkeeping
        parser.add_argument('--save_directory',
                            default='',
                            type=str,
                            help='Location to save model saves and other information.')
        parser.add_argument('--experiment_name',
                            default='',
                            type=str,
                            help='The experiment name. A directory will be created under save_directory for it.')
        parser.add_argument('--log_with_slack',
                            default=False,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to log experiment details (starting, epoch accuracies, and ending) to a '
                                 'Slack channel.')

        # TODO: Neither of the two following are actually used anywhere.
        parser.add_argument('--validation_metrics',
                            default=[metric.Metric.RELAXED_ENVIRONMENT_ACCURACY,
                                     metric.Metric.SEQUENCE_ACCURACY,
                                     metric.Metric.CARD_ACCURACY,
                                     metric.Metric.EXACT_ENVIRONMENT_ACCURACY,
                                     metric.Metric.AGENT_DISTANCE,
                                     metric.Metric.SCORE],
                            nargs='+',
                            type=metric.Metric,
                            help='The metrics to compute on the validation set each epoch.')
        parser.add_argument('--training_metrics',
                            default=[metric.Metric.RELAXED_ENVIRONMENT_ACCURACY,
                                     metric.Metric.SEQUENCE_ACCURACY,
                                     metric.Metric.CARD_ACCURACY,
                                     metric.Metric.EXACT_ENVIRONMENT_ACCURACY,
                                     metric.Metric.AGENT_DISTANCE,
                                     metric.Metric.SCORE],
                            nargs='+',
                            type=metric.Metric,
                            help='The metrics to compute on the training set each epoch.')

        # Data during training
        parser.add_argument('--proportion_of_train_for_accuracy',
                            default=0.1,
                            type=float,
                            help='The number of training games on which to run inference every epoch to compute an '
                                 'estimate of the accuracy on the training set.')
        parser.add_argument('--aggregate_examples',
                            default=False,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to aggregate training examples during training and validation inference as a '
                                 'way to improve recovery against error propagation during full game inference.')
        parser.add_argument('--batch_size',
                            default=16,
                            type=int,
                            help='The batch size to use for training.')
        # Training process
        parser.add_argument('--initial_patience',
                            default=10.,
                            type=float,
                            help='Initial patience.')
        parser.add_argument('--patience_update_factor',
                            default=1.,
                            type=float,
                            help='Factor to increase patience by when performance improves.')
        parser.add_argument('--stopping_metric',
                            default=metric.Metric.RELAXED_ENVIRONMENT_ACCURACY,
                            type=metric.Metric,
                            help='Which metric to stop on.')

        # Optimizer
        parser.add_argument('--optimizer',
                            default=OptimizerType.ADAM,
                            type=OptimizerType,
                            help='The optimizer type to use.')
        parser.add_argument('--plan_prediction_learning_rate',
                            default=0.0075,
                            type=float,
                            help='Learning rate to use for hex predictor.')
        parser.add_argument('--plan_prediction_l2_coefficient',
                            default=0.000001,
                            type=float,
                            help='Coefficient of the L2 norm for regularization.')
        parser.add_argument('--action_generation_learning_rate',
                            default=0.001,
                            type=float,
                            help='Learning rate to use for action predictor.')
        parser.add_argument('--action_generation_l2_coefficient',
                            default=0.,
                            type=float,
                            help='Coefficient of the L2 norm for regularization.')
        parser.add_argument('--finetune_learning_rate',
                            default=0.001,
                            type=float,
                            help='Learning rate to use for finetuning models.')
        parser.add_argument('--finetune_l2_coefficient',
                            default=0.,
                            type=float,
                            help='Coefficient of the L2 norm for regularization.')
        parser.add_argument('--max_gradient',
                            default=-1,
                            type=float,
                            help='Maximum gradient (for clipping)')

        # Coefficients for auxiliary losses.
        parser.add_argument('--pretrain_auxiliary_coefficient_intermediate_goal_probabilities',
                            default=0.,
                            type=float,
                            help='The coefficient for the card reaching loss intermediate in the network.')
        parser.add_argument('--pretrain_auxiliary_coefficient_trajectory_distribution',
                            default=0.,
                            type=float,
                            help='The coefficient for the trajectory distribution loss.')
        parser.add_argument('--pretrain_auxiliary_coefficient_final_goal_probabilities',
                            default=0.,
                            type=float,
                            help='The coefficient for the final card prediction.')
        parser.add_argument('--pretrain_auxiliary_coefficient_obstacle_probabilities',
                            default=0.,
                            type=float,
                            help='The coefficient of the prediction of hexes which cannot be passed through.')
        parser.add_argument('--pretrain_auxiliary_coefficient_avoid_probabilities',
                            default=0.,
                            type=float,
                            help='The coefficient of the prediction of hexes to avoid (e.g., card it should not pick '
                                 'up)')
        parser.add_argument('--finetune_auxiliary_coefficient_intermediate_goal_probabilities',
                            default=0.,
                            type=float,
                            help='The coefficient for the card reaching loss intermediate in the network.')
        parser.add_argument('--finetune_auxiliary_coefficient_trajectory_distribution',
                            default=0.,
                            type=float,
                            help='The coefficient for the trajectory distribution loss.')
        parser.add_argument('--finetune_auxiliary_coefficient_final_goal_probabilities',
                            default=0.,
                            type=float,
                            help='The coefficient for the final card prediction.')
        parser.add_argument('--finetune_auxiliary_coefficient_obstacle_probabilities',
                            default=0.,
                            type=float,
                            help='The coefficient of the prediction of hexes which cannot be passed through.')
        parser.add_argument('--finetune_auxiliary_coefficient_avoid_probabilities',
                            default=0.,
                            type=float,
                            help='The coefficient of the prediction of hexes to avoid (e.g., card it should not pick '
                                 'up)')
        parser.add_argument('--finetune_auxiliary_coefficient_implicit_actions',
                            default=0.,
                            type=float,
                            help='The coefficient on the implicit example prediction')

        self._batch_size: int = None
        self._log_with_slack: bool = None

        self._initial_patience: float = None
        self._patience_update_factor: float = None

        self._plan_prediction_learning_rate: float = None
        self._plan_prediction_l2_coefficient: float = None

        self._action_generation_learning_rate: float = None
        self._action_generation_l2_coefficient: float = None

        self._finetune_learning_rate: float = None
        self._finetune_l2_coefficient: float = None

        self._optimizer_type: OptimizerType = None
        self._max_gradient: float = None

        self._proportion_of_train_for_accuracy: int = None

        self._save_directory: str = None
        self._experiment_name: str = None

        self._stopping_metric: metric.Metric = None

        self._validation_metrics: List[metric.Metric] = None
        self._training_metrics: List[metric.Metric] = None

        self._pretrain_auxiliary_coefficient_intermediate_goal_probabilities: float = None
        self._pretrain_auxiliary_coefficient_trajectory_distribution: float = None
        self._pretrain_auxiliary_coefficient_final_goal_probabilities: float = None
        self._pretrain_auxiliary_coefficient_obstacle_probabilities: float = None
        self._pretrain_auxiliary_coefficient_avoid_probabilities: float = None
        self._finetune_auxiliary_coefficient_intermediate_goal_probabilities: float = None
        self._finetune_auxiliary_coefficient_trajectory_distribution: float = None
        self._finetune_auxiliary_coefficient_final_goal_probabilities: float = None
        self._finetune_auxiliary_coefficient_obstacle_probabilities: float = None
        self._finetune_auxiliary_coefficient_avoid_probabilities: float = None
        self._finetune_auxiliary_coefficient_implicit_actions: float = None

        self._aggregate_examples: bool = None

    def log_with_slack(self) -> bool:
        self.check_initialized()
        return self._log_with_slack

    def get_batch_size(self) -> int:
        self.check_initialized()
        return self._batch_size

    def aggregate_examples(self) -> bool:
        self.check_initialized()
        return self._aggregate_examples

    def get_auxiliary_coefficient_avoid_probabilities(self, finetune: bool) -> float:
        self.check_initialized()
        if finetune:
            return self._finetune_auxiliary_coefficient_avoid_probabilities
        return self._pretrain_auxiliary_coefficient_avoid_probabilities

    def get_auxiliary_coefficient_obstacle_probabilities(self, finetune: bool) -> float:
        self.check_initialized()
        if finetune:
            return self._finetune_auxiliary_coefficient_obstacle_probabilities
        return self._pretrain_auxiliary_coefficient_obstacle_probabilities

    def get_auxiliary_coefficient_trajectory_distribution(self, finetune: bool) -> float:
        self.check_initialized()
        if finetune:
            return self._finetune_auxiliary_coefficient_trajectory_distribution
        return self._pretrain_auxiliary_coefficient_trajectory_distribution

    def get_auxiliary_coefficient_final_goal_probabilities(self, finetune: bool) -> float:
        self.check_initialized()
        if finetune:
            return self._finetune_auxiliary_coefficient_final_goal_probabilities
        return self._pretrain_auxiliary_coefficient_final_goal_probabilities

    def get_auxiliary_coefficient_intermediate_goal_probabilities(self, finetune: bool) -> float:
        self.check_initialized()
        if finetune:
            return self._finetune_auxiliary_coefficient_intermediate_goal_probabilities
        return self._pretrain_auxiliary_coefficient_intermediate_goal_probabilities

    def get_auxiliary_coefficient_implicit_actions(self) -> float:
        return self._finetune_auxiliary_coefficient_implicit_actions

    def get_validation_metrics(self) -> List[metric.Metric]:
        self.check_initialized()
        return self._validation_metrics

    def get_training_metrics(self) -> List[metric.Metric]:
        self.check_initialized()
        return self._training_metrics

    def get_initial_patience(self) -> float:
        self.check_initialized()
        return self._initial_patience

    def get_patience_update_factor(self) -> float:
        self.check_initialized()
        return self._patience_update_factor

    def get_max_gradient(self) -> float:
        self.check_initialized()
        return self._max_gradient

    def get_stopping_metric(self) -> metric.Metric:
        self.check_initialized()
        return self._stopping_metric

    def get_save_directory(self) -> str:
        self.check_initialized()

        # Create the dir if it does not exist
        full_dir: str = os.path.join(self._save_directory, self._experiment_name)
        if not os.path.exists(full_dir):
            print('Created directory: ' + full_dir)
            os.mkdir(full_dir)

        return full_dir

    def get_proportion_of_train_for_accuracy(self) -> int:
        self.check_initialized()
        return self._proportion_of_train_for_accuracy

    def get_experiment_name(self) -> str:
        self.check_initialized()
        return self._experiment_name

    def get_optimizer(self, task: model_args.Task, finetune: bool = False) -> Callable[[Any], torch.optim.Optimizer]:
        self.check_initialized()

        learning_rate: float = 0.
        l2_coefficient: float = 0.
        if task == model_args.Task.PLAN_PREDICTOR:
            learning_rate = self._plan_prediction_learning_rate
            l2_coefficient = self._plan_prediction_l2_coefficient
        elif task == model_args.Task.ACTION_GENERATOR:
            if finetune:
                learning_rate = self._finetune_learning_rate
                l2_coefficient = self._finetune_l2_coefficient
            else:
                learning_rate = self._action_generation_learning_rate
                l2_coefficient = self._action_generation_l2_coefficient

        if self._optimizer_type == OptimizerType.ADAM:
            logging.info('Adam with lr = ' + str(learning_rate) + ', weight decay = ' + str(l2_coefficient))
            return lambda params: torch.optim.Adam(params, lr=learning_rate, weight_decay=l2_coefficient)
        elif self._optimizer_type == OptimizerType.ADAGRAD:
            logging.info('Adagrad with lr = ' + str(learning_rate) + ', weight decay = ' + str(l2_coefficient))
            return lambda params: torch.optim.Adagrad(params, lr=learning_rate, weight_decay=l2_coefficient)
        elif self._optimizer_type == OptimizerType.RMSPROP:
            logging.info('RMSProp with lr = ' + str(learning_rate) + ', weight decay = ' + str(l2_coefficient))
            return lambda params: torch.optim.RMSprop(params, lr=learning_rate, weight_decay=l2_coefficient)
        elif self._optimizer_type == OptimizerType.SGD:
            logging.info('SGD with lr = ' + str(learning_rate) + ', weight decay = ' + str(l2_coefficient))
            return lambda params: torch.optim.SGD(params, lr=learning_rate, weight_decay=l2_coefficient)

    def interpret_args(self, parsed_args: Namespace) -> None:
        self._batch_size = parsed_args.batch_size
        self._save_directory = parsed_args.save_directory
        self._experiment_name = parsed_args.experiment_name

        self._log_with_slack = parsed_args.log_with_slack

        self._proportion_of_train_for_accuracy = parsed_args.proportion_of_train_for_accuracy

        self._optimizer_type = parsed_args.optimizer

        self._stopping_metric = parsed_args.stopping_metric
        self._validation_metrics = parsed_args.validation_metrics
        self._training_metrics = parsed_args.training_metrics
        self._max_gradient = parsed_args.max_gradient

        self._plan_prediction_learning_rate = parsed_args.plan_prediction_learning_rate
        self._plan_prediction_l2_coefficient = parsed_args.plan_prediction_l2_coefficient
        self._action_generation_learning_rate = parsed_args.action_generation_learning_rate
        self._action_generation_l2_coefficient = parsed_args.action_generation_l2_coefficient
        self._finetune_l2_coefficient = parsed_args.finetune_l2_coefficient
        self._finetune_learning_rate = parsed_args.finetune_learning_rate

        self._pretrain_auxiliary_coefficient_intermediate_goal_probabilities = \
            parsed_args.pretrain_auxiliary_coefficient_intermediate_goal_probabilities
        self._pretrain_auxiliary_coefficient_trajectory_distribution = \
            parsed_args.pretrain_auxiliary_coefficient_trajectory_distribution
        self._pretrain_auxiliary_coefficient_final_goal_probabilities = \
            parsed_args.pretrain_auxiliary_coefficient_final_goal_probabilities
        self._pretrain_auxiliary_coefficient_obstacle_probabilities = \
            parsed_args.pretrain_auxiliary_coefficient_obstacle_probabilities
        self._pretrain_auxiliary_coefficient_avoid_probabilities = \
            parsed_args.pretrain_auxiliary_coefficient_avoid_probabilities
        self._finetune_auxiliary_coefficient_intermediate_goal_probabilities = \
            parsed_args.finetune_auxiliary_coefficient_intermediate_goal_probabilities
        self._finetune_auxiliary_coefficient_trajectory_distribution = \
            parsed_args.finetune_auxiliary_coefficient_trajectory_distribution
        self._finetune_auxiliary_coefficient_final_goal_probabilities = \
            parsed_args.finetune_auxiliary_coefficient_final_goal_probabilities
        self._finetune_auxiliary_coefficient_obstacle_probabilities = \
            parsed_args.finetune_auxiliary_coefficient_obstacle_probabilities
        self._finetune_auxiliary_coefficient_avoid_probabilities = \
            parsed_args.finetune_auxiliary_coefficient_avoid_probabilities
        self._finetune_auxiliary_coefficient_implicit_actions = \
            parsed_args.finetune_auxiliary_coefficient_implicit_actions

        self._initial_patience = parsed_args.initial_patience
        self._patience_update_factor = parsed_args.patience_update_factor

        self._aggregate_examples = parsed_args.aggregate_examples

        super(TrainingArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        str_rep: str = '***Training arguments ***' \
                       '\n\tSaving in directory: %r' \
                       '\n\tWith experiment name: %r\n' \
                       '\n\tBatch size: %r' \
                       '\n\tProportion of training examples used to compute accuracy: %r' \
                       '\n\tAggregate examples? %r\n' \
                       '\n\tInitial patience: %r' \
                       '\n\tPatience update ratio: %r' \
                       '\n\tStopping metric: %r\n' % (self.get_save_directory(), self.get_experiment_name(),
                                                      self.get_batch_size(),
                                                      self.get_proportion_of_train_for_accuracy(),
                                                      self.aggregate_examples(), self.get_initial_patience(),
                                                      self.get_patience_update_factor(), self.get_stopping_metric())
        str_rep += '\n\tPlan prediction LR/L2: %r/%r' \
                   '\n\tAction generation LR/L2: %r/%r' \
                   '\n\tFinetuning LR/L2: %r/%r' \
                   '\n\tMaximum gradient: %r' \
                   '\n\tOptimizer: %r\n' % (self._plan_prediction_learning_rate, self._finetune_l2_coefficient,
                                            self._action_generation_learning_rate,
                                            self._action_generation_l2_coefficient,
                                            self._finetune_learning_rate, self._finetune_l2_coefficient,
                                            self._max_gradient, self._optimizer_type)
        str_rep += '\n\tIntermediate goal auxiliary coefficient (pretraining/finetuning): %r/%r' \
                   '\n\tFinal goal auxiliary coefficient (pretraining/finetuning): %r/%r' \
                   '\n\tObstacle auxiliary coefficient (pretraining/finetuning): %r/%r' \
                   '\n\tAvoid location auxiliary coefficient (pretraining/finetuning): %r/%r' \
                   '\n\tTrajectory auxiliary coefficient (pretraining/finetuning): %r/%r' \
                   '\n\tImplicit action auxiliary coefficient: %r' % (
                        self._pretrain_auxiliary_coefficient_intermediate_goal_probabilities,
                        self._finetune_auxiliary_coefficient_intermediate_goal_probabilities,
                        self._pretrain_auxiliary_coefficient_final_goal_probabilities,
                        self._finetune_auxiliary_coefficient_final_goal_probabilities,
                        self._pretrain_auxiliary_coefficient_obstacle_probabilities,
                        self._finetune_auxiliary_coefficient_obstacle_probabilities,
                        self._pretrain_auxiliary_coefficient_avoid_probabilities,
                        self._finetune_auxiliary_coefficient_avoid_probabilities,
                        self._pretrain_auxiliary_coefficient_trajectory_distribution,
                        self._pretrain_auxiliary_coefficient_trajectory_distribution,
                        self._finetune_auxiliary_coefficient_implicit_actions)

        return str_rep

    def __eq__(self, other) -> bool:
        return True
