""" Contains a model wrapper for a model which predicts distributions over hexes.
"""
from __future__ import annotations

import logging
import math
import os
import random
from typing import TYPE_CHECKING

import torch

from agent import util
from agent.config import model_args
from agent.data import dataset_split
from agent.data import instruction_example
from agent.learning import auxiliary
from agent.learning import batch_loss
from agent.learning import plan_losses
from agent.learning import plan_metrics
from agent.model.model_wrappers import model_wrapper
from agent.model.models import plan_predictor_model

if TYPE_CHECKING:
    from agent.config import evaluation_args
    from agent.config import game_args
    from agent.config import training_args
    from agent.data import game_dataset
    from pycrayon import crayon
    from typing import Any, Dict, List, Tuple


class PlanPredictorWrapper(model_wrapper.ModelWrapper):
    """ Wrapper for a hex predictor model.

    Attributes:
        self._model: HexPredictorModel. The model being wrapped.
        self._criterion: A criterion for computing loss.
        self._traj_craterion: Another criterion for computing loss.
    """

    def __init__(self,
                 model_arguments: model_args.ModelArgs,
                 training_arguments: training_args.TrainingArgs,
                 vocabulary: List[str],
                 logger: crayon.CrayonExperiment,
                 model: plan_predictor_model.PlanPredictorModel = None):
        super(PlanPredictorWrapper, self).__init__(model_arguments, logger)
        if self._parallelized:
            raise ValueError('The plan predictor model cannot be parallelized anymore. '
                             'Adapt the forward methods to take and return only tensors.')

        self._auxiliaries = plan_losses.get_auxiliaries_from_args(training_arguments, False)

        if model:
            self._model = model
        else:
            self._model: plan_predictor_model.PlanPredictorModel = plan_predictor_model.PlanPredictorModel(
                model_arguments, vocabulary, list(self._auxiliaries.keys()))
        self._put_on_device()

    def get_auxiliaries(self) -> Dict[auxiliary.Auxiliary, float]:
        """ Returns the auxiliary losses and their associated coefficients. """
        return self._auxiliaries

    def loss(self,
             examples: List[Tuple[instruction_example.InstructionExample,
                                  int]]) -> Tuple[torch.Tensor, Dict[auxiliary.Auxiliary, Any]]:

        # First, batch the model inputs.
        if self._parallelized:
            inputs: List[torch.Tensor] = \
                self._model.module.batch_inputs(examples,
                                                put_on_device=torch.cuda.device_count() == 1 and not self._parallelized)
        else:
            inputs: List[torch.Tensor] = \
                self._model.batch_inputs(examples,
                                         put_on_device=torch.cuda.device_count() == 1 and not self._parallelized)

        auxiliary_dict = self._model(*inputs)
        auxiliary_loss_dict: Dict[auxiliary.Auxiliary, Any] = dict()

        # The action index doesn't affect anything about this loss computation, as the gold trajectory distribution
        # and card distribution should remain the same throughout.
        for i, (example, action_idx) in enumerate(examples):
            plan_losses.compute_per_example_auxiliary_losses(
                example, i, auxiliary_dict, list(self._auxiliaries.keys()), auxiliary_loss_dict,
                self._args.get_decoder_args().weight_trajectory_by_time(),
                self.get_arguments().get_state_rep_args().full_observability())

        # Now compute the means for each of the auxiliary losses
        for specified_auxiliary in list(self._auxiliaries.keys()):
            auxiliary_loss_dict[specified_auxiliary] = torch.mean(torch.stack(tuple(auxiliary_loss_dict[
                                                                                        specified_auxiliary])))

        # Technically, no main loss here
        return torch.tensor(0.).to(util.DEVICE), auxiliary_loss_dict

    def _train_epoch(self,
                     train_ids: List[Tuple[str, int]],
                     epoch_index: int,
                     train_examples: Dict[str, instruction_example.InstructionExample],
                     batch_size: int,
                     optimizer: torch.optim.Optimizer,
                     experiment: crayon.CrayonExperiment):
        self.train()
        num_batches: int = 0
        train_loss_sum: float = 0

        # TODO: Should this be shuffled randomly so that action indices for the same instruction are likely in
        #   different batches? Or prefer to have them in the same batch to have the batch be more useful?
        random.shuffle(train_ids)

        losses_dict = dict()
        with util.get_progressbar('epoch ' + str(epoch_index), int(len(train_examples) / batch_size)) as pbar:
            for start_idx in range(0, len(train_examples), batch_size):
                pbar.update(num_batches)
                examples_in_batch: List[Any] = list()
                for ex_id, idx in train_ids[start_idx:start_idx + batch_size]:
                    examples_in_batch.append((train_examples[ex_id], idx))

                loss_for_batch, _, losses_for_auxiliaries = batch_loss.apply_batch_loss(
                    self,
                    examples_in_batch,
                    optimizer)

                for auxiliary_type, losses in losses_for_auxiliaries.items():
                    loss_name = str(auxiliary_type)
                    if loss_name not in losses_dict:
                        losses_dict[loss_name] = 0.
                    losses_dict[loss_name] += losses.item()

                experiment.add_scalar_value('batch loss', loss_for_batch)
                if math.isnan(loss_for_batch):
                    raise ValueError('NaN Loss')

                train_loss_sum += loss_for_batch
                num_batches += 1

        epoch_average_loss: float = float(train_loss_sum / num_batches)
        logging.info('Average loss per batch: %f', epoch_average_loss)
        experiment.add_scalar_value('train loss', epoch_average_loss)
        for loss, loss_sum in losses_dict.items():
            experiment.add_scalar_value('train ' + str(loss) + ' loss', float(loss_sum / num_batches))

    def _eval(self,
              train_examples: Dict[str, Any],
              validation_examples: Dict[str, Any],
              experiment: crayon.CrayonExperiment,
              train_evaluation_proportion: float):
        self.eval()
        with torch.no_grad():

            # Evaluate on training sample
            train_sample = list(train_examples.values())[:int(len(train_examples) * train_evaluation_proportion)]
            train_results_dict: Dict[str, Any] = \
                plan_metrics.plan_metric_results(self, train_sample)

            for name, float_value in train_results_dict.items():
                experiment.add_scalar_value('train ' + str(name), float_value)

            # Evaluating on the validation subset
            validation_results_dict: Dict[str, Any] = \
                plan_metrics.plan_metric_results(self, list(validation_examples.values()))

            for name, float_value in validation_results_dict.items():
                experiment.add_scalar_value('val ' + str(name), float_value)

        if str(auxiliary.Auxiliary.TRAJECTORY) + ' xent' not in validation_results_dict:
            validation_results_dict[str(auxiliary.Auxiliary.TRAJECTORY) + ' xent'] = 0.

        if auxiliary.Auxiliary.FINAL_GOALS in self._auxiliaries:
            return validation_results_dict[str(auxiliary.Auxiliary.FINAL_GOALS) + ' accuracy']
        return 0.

    def state_dict(self):
        return self._model.state_dict()

    def train_loop(self,
                   dataset: game_dataset.GameDataset,
                   game_arguments: game_args.GameArgs,
                   evaluation_arguments: evaluation_args.EvaluationArgs,
                   training_arguments: training_args.TrainingArgs,
                   experiment: crayon.CrayonExperiment) -> str:
        train_examples: Dict[str, instruction_example.InstructionExample] = dataset.get_examples(
            dataset_split.DatasetSplit.UPDATE)

        # TODO: The second value here is the index in the action sequence that the state is being observed.
        # for now, it is only training on data for the 0th action: i.e., at the beginning of the instruction.
        # However, when moving to partial observability, this should include ALL actions in every sequence.

        train_ids = instruction_example.get_example_action_index_pairs(
            train_examples, self._args.get_state_rep_args().full_observability(),
            self._args.get_state_rep_args().observability_refresh_rate())

        validation_examples: Dict[str, instruction_example.InstructionExample] = dataset.get_examples(
            dataset_split.DatasetSplit.VALIDATION)

        # Clip gradients
        optimizer: torch.optim.Optimizer = training_arguments.get_optimizer(model_args.Task.PLAN_PREDICTOR)(
            self.parameters())
        if training_arguments.get_max_gradient() > 0:
            torch.nn.utils.clip_grad_norm_(self.parameters(), training_arguments.get_max_gradient())

        num_epochs: int = 0
        maximum_accuracy: float = 0.

        patience: float = training_arguments.get_initial_patience()
        countdown: int = int(patience)

        best_epoch_filename: str = ''

        while countdown > 0:
            logging.info('Starting epoch (plan predictor) ' + str(num_epochs))
            self._train_epoch(train_ids,
                              num_epochs,
                              train_examples,
                              training_arguments.get_batch_size(),
                              optimizer,
                              experiment)

            exit()
            validation_goal_accuracy = self._eval(train_examples, validation_examples, experiment,
                                                  training_arguments.get_proportion_of_train_for_accuracy())

            save_description: str = ''

            if validation_goal_accuracy > maximum_accuracy:
                logging.info('Best accuracy: ' + str(validation_goal_accuracy))
                maximum_accuracy = validation_goal_accuracy
                save_description += '_bestacc'

            if save_description:
                filename: str = \
                    os.path.join(training_arguments.get_save_directory(),
                                 'model_' + str(num_epochs) + save_description + '.pt')
                best_epoch_filename = filename

                patience *= training_arguments.get_patience_update_factor()
                countdown = int(patience)
                logging.info('Resetting countdown to %d, patience is %d', countdown, patience)

                self.save(filename)

            num_epochs += 1
            countdown -= 1
            experiment.add_scalar_value('countdown', countdown)

        return best_epoch_filename
