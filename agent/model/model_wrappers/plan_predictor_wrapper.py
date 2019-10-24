""" Contains a model wrapper for a model which predicts distributions over hexes.
"""
from __future__ import annotations

import logging
import math
import os
import random
from typing import TYPE_CHECKING

import torch
import torch.nn as nn

from agent import util
from agent.data import dataset_split
from agent.learning import auxiliary_losses
from agent.model.model_wrappers import model_wrapper
from agent.model.models import plan_predictor_model

if TYPE_CHECKING:
    from agent.config import evaluation_args
    from agent.config import game_args
    from agent.config import model_args
    from agent.config import training_args
    from agent.data import game_dataset
    from agent.data import instruction_example
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

        self._auxiliaries = auxiliary_losses.get_auxiliaries_from_args(training_arguments, False)

        if model:
            self._model = model
        else:
            self._model: plan_predictor_model.PlanPredictorModel = plan_predictor_model.PlanPredictorModel(
                model_arguments, vocabulary, list(self._auxiliaries.keys()))
        self._put_on_device()

    def _compute_example_loss(self,
                              example_idx: int,
                              example: instruction_example.InstructionExample,
                              action_idx: int,
                              main_hex_reach_scores: torch.Tensor,
                              auxiliary_dict: Dict[Auxiliary, torch.Tensor],
                              final_loss_tensors: List[torch.Tensor],
                              auxiliary_losses: Dict[Auxiliary, List[torch.Tensor]]):
        intermediate_reach_scores: List[torch.Tensor] = list()
        avoid_scores: List[torch.Tensor] = list()
        final_reach_scores: List[torch.Tensor] = list()
        final_reach_labels: List[torch.Tensor] = list()

        avoid_labels: List[torch.Tensor] = list()

        # For all cards on the board at the beginning
        for card in example.get_state_deltas()[action_idx].cards:
            position = card.get_position()

            # If it's to be touched, give a 1 label
            if position in \
                    [card.get_position() for card in
                     example.get_touched_cards()]:
                final_reach_labels.append(torch.tensor(1.))
            else:
                final_reach_labels.append(torch.tensor(0.))

            if Auxiliary.INTERMEDIATE_CARDS in self._auxiliaries:
                intermediate_reach_scores.append(
                    auxiliary_dict[Auxiliary.INTERMEDIATE_CARDS][example_idx][position.x][position.y])

            final_reach_scores.append(main_hex_reach_scores.squeeze(1)[example_idx][position.x][position.y])

            # TODO: is it better to predict this only for cards, or over the whole map?
            if Auxiliary.AVOID_LOCS in self._auxiliaries:
                avoid_scores.append(auxiliary_dict[Auxiliary.AVOID_LOCS][example_idx][0][position.x][position.y])

                # Currently, should predict all cards except the one it's currently on
                if position in [card.get_position() for card in example.get_touched_cards(include_original=True)]:
                    avoid_labels.append(torch.tensor(0.))
                else:
                    avoid_labels.append(torch.tensor(1.))

        # To compute the loss, flatten everything first
        combined_labels = torch.stack(tuple(final_reach_labels)).to(DEVICE)

        if Auxiliary.INTERMEDIATE_CARDS in self._auxiliaries:
            if Auxiliary.INTERMEDIATE_CARDS not in auxiliary_losses:
                auxiliary_losses[Auxiliary.INTERMEDIATE_CARDS] = list()
            auxiliary_losses[Auxiliary.INTERMEDIATE_CARDS].append(
                nn.BCEWithLogitsLoss()(torch.stack(tuple(intermediate_reach_scores)), combined_labels))

        final_loss_tensors.append(nn.BCEWithLogitsLoss()(torch.stack(tuple(final_reach_scores)), combined_labels))

        # Then the trajectory loss
        if Auxiliary.TRAJECTORY in self._auxiliaries:
            if Auxiliary.TRAJECTORY not in auxiliary_losses:
                auxiliary_losses[Auxiliary.TRAJECTORY] = list()
            selected_times = None
            if auxiliary_dict[Auxiliary.TRAJECTORY][1] is not None:
                selected_times = auxiliary_dict[Auxiliary.TRAJECTORY][1][example_idx].unsqueeze(0)
            auxiliary_losses[Auxiliary.TRAJECTORY].append(
                compute_trajectory_loss(example,
                                        auxiliary_dict[Auxiliary.TRAJECTORY][0][example_idx].unsqueeze(0),
                                        selected_times,
                                        self._args.get_decoder_args().traj_weight_by_time()))

        if Auxiliary.IMPASSABLE_LOCS in self._auxiliaries:
            impassable_label: torch.Tensor = torch.zeros((ENV_WIDTH, ENV_DEPTH)).float()
            impassable_score: torch.Tensor = auxiliary_dict[Auxiliary.IMPASSABLE_LOCS][example_idx][0]

            for position in example.get_obstacle_positions():
                impassable_label[position.x][position.y] = 1.

            if Auxiliary.IMPASSABLE_LOCS not in auxiliary_losses:
                auxiliary_losses[Auxiliary.IMPASSABLE_LOCS] = list()
            auxiliary_losses[Auxiliary.IMPASSABLE_LOCS].append(
                nn.BCEWithLogitsLoss()(impassable_score.view(1, -1),
                                       impassable_label.view(1, -1).to(DEVICE)))

        if Auxiliary.AVOID_LOCS in self._auxiliaries:
            if Auxiliary.AVOID_LOCS not in auxiliary_losses:
                auxiliary_losses[Auxiliary.AVOID_LOCS] = list()
            auxiliary_losses[Auxiliary.AVOID_LOCS].append(
                nn.BCEWithLogitsLoss()(torch.stack(tuple(avoid_scores)),
                                       torch.stack(tuple(avoid_labels)).to(DEVICE)))

    def get_auxiliaries(self) -> Dict[Auxiliary, float]:
        """ Returns the auxiliary losses and their associated coefficients. """
        return self._auxiliaries

    def time_split(self) -> bool:
        return self._args.get_decoder_args().use_timewise_distributions()

    def time_normalized(self) -> bool:
        return self._args.get_decoder_args().normalize_over_time()

    def loss(self, examples: List[Tuple[instruction_example.InstructionExample, int]]) -> Tuple[
        torch.Tensor, Dict[Auxiliary, Any]]:
        # First, batch the model inputs.
        if self._parallelized:
            inputs: List[torch.Tensor] = \
                self._model.module.batch_inputs(examples,
                                                put_on_device=torch.cuda.device_count() == 1 and not self._parallelized)
        else:
            inputs: List[torch.Tensor] = \
                self._model.batch_inputs(examples,
                                         put_on_device=torch.cuda.device_count() == 1 and not self._parallelized)

        main_hex_reach_scores, auxiliary_dict = self._model(*inputs)

        auxiliary_losses: Dict[Auxiliary, Any] = dict()
        if Auxiliary.HEX_PROPERTIES in self._auxiliaries:
            auxiliary_losses[Auxiliary.HEX_PROPERTIES] = dict()
            for pred_scores, gold_indices, auxiliary_name \
                    in zip(auxiliary_dict[Auxiliary.HEX_PROPERTIES], inputs[4:], HEX_PROPERTY_NAMES):
                # Flatten the distribution. The softmax is over properties, not hexes.
                flattened_scores = pred_scores.view(len(examples) * ENV_WIDTH * ENV_DEPTH, -1)
                flattened_indices = gold_indices.view(len(examples) * ENV_WIDTH * ENV_DEPTH)

                auxiliary_losses[Auxiliary.HEX_PROPERTIES][auxiliary_name] = \
                    self._auxiliary_criteria[Auxiliary.HEX_PROPERTIES](flattened_scores, flattened_indices)

        # The action index doesn't affect anything about this loss computation, as the gold trajectory distribution
        # and card distribution should remain the same throughout.
        auxiliary_dict[Auxiliary.FINAL_CARDS] = main_hex_reach_scores
        for i, (example, action_idx) in enumerate(examples):
            compute_example_auxiliary_losses(example,
                                             i,
                                             auxiliary_dict,
                                             list(self._auxiliaries.keys()),
                                             # TODO: this should contain the final cards!
                                             auxiliary_losses,
                                             self._args.get_decoder_args().traj_weight_by_time())

        # Now compute the means for each of the auxiliary losses
        for auxiliary in list(self._auxiliaries.keys()):
            if auxiliary != Auxiliary.HEX_PROPERTIES:
                auxiliary_losses[auxiliary] = torch.mean(torch.stack(tuple(auxiliary_losses[auxiliary])))

        # Technically, no main loss here
        return 0., auxiliary_losses

    def _train_epoch(self,
                     train_ids: List[Tuple[str, int]],
                     epoch_idx: int,
                     train_examples: Dict[str, instruction_example.InstructionExample],
                     batch_size: int,
                     optimizer: torch.optim.Optimizer,
                     experiment: crayon.CrayonExperiment):
        self.train()
        num_batches: int = 0
        train_loss_sum: float = 0

        random.shuffle(train_ids)
        losses_dict = dict()
        with util.get_progressbar('epoch ' + str(epoch_idx), int(len(train_examples) / batch_size)) as pbar:
            for start_idx in range(0, len(train_examples), batch_size):
                pbar.update(num_batches)
                examples_in_batch: List[Any] = list()
                for ex_id, idx in train_ids[start_idx:start_idx + batch_size]:
                    examples_in_batch.append((train_examples[ex_id], idx))

                batch_loss, _, auxiliary_losses = train_aux_loss_batch(
                    self,
                    examples_in_batch,
                    optimizer)

                for auxiliary_type, losses in auxiliary_losses.items():
                    if auxiliary_type == Auxiliary.HEX_PROPERTIES:
                        for loss_name, loss in auxiliary_losses[auxiliary_type].items():
                            if loss_name not in losses_dict:
                                losses_dict[loss_name] = 0.
                            losses_dict[loss_name] += loss.item()
                    else:
                        loss_name = str(auxiliary_type)
                        if loss_name not in losses_dict:
                            losses_dict[loss_name] = 0.
                        losses_dict[loss_name] += losses.item()

                experiment.add_scalar_value('batch loss', batch_loss)
                if math.isnan(batch_loss):
                    raise ValueError('NaN Loss')

                train_loss_sum += batch_loss
                num_batches += 1

        avg_loss: float = float(train_loss_sum / num_batches)
        logging.info('Average loss per batch: %f', avg_loss)
        experiment.add_scalar_value('train loss', avg_loss)
        for loss, loss_sum in losses_dict.items():
            experiment.add_scalar_value('train ' + str(loss) + ' loss', float(loss_sum / num_batches))

    def _eval(self,
              train_examples: Dict[str, Any],
              val_examples: Dict[str, Any],
              experiment: crayon.CrayonExperiment):
        self.eval()
        with torch.no_grad():
            auxiliaries_train = dict()
            train_sample = list(train_examples.values())[:int(len(train_examples) * 0.1)]
            for example in train_sample:
                card_scores, auxiliaries = self.get_predictions(example)
                if Auxiliary.FINAL_CARDS in self._auxiliaries:
                    auxiliaries.update({Auxiliary.FINAL_CARDS: card_scores.squeeze()})
                auxiliaries_train[example.get_id()] = auxiliaries

            train_results_dict: Dict[str, Any] = \
                auxiliary_property_accuracies(self,
                                              train_sample,
                                              auxiliaries_train,
                                              self._args.get_decoder_args().traj_weight_by_time())

            for name, float_value in train_results_dict.items():
                experiment.add_scalar_value('train ' + str(name), float_value)

            auxiliaries_val = dict()
            for example in val_examples.values():
                card_scores, auxiliaries = self.get_predictions(example)
                if Auxiliary.FINAL_CARDS in self._auxiliaries:
                    auxiliaries.update({Auxiliary.FINAL_CARDS: card_scores.squeeze()})
                auxiliaries_val[example.get_id()] = auxiliaries
            val_results_dict: Dict[str, Any] = \
                auxiliary_property_accuracies(self,
                                              list(val_examples.values()),
                                              auxiliaries_val,
                                              self._args.get_decoder_args().traj_weight_by_time())
            for name, float_value in val_results_dict.items():
                experiment.add_scalar_value('val ' + str(name), float_value)

        if str(Auxiliary.TRAJECTORY) + ' xent' not in val_results_dict:
            val_results_dict[str(Auxiliary.TRAJECTORY) + ' xent'] = 0.
        return (val_results_dict[
                    str(Auxiliary.FINAL_CARDS) + ' accuracy'] if Auxiliary.FINAL_CARDS in self._auxiliaries else 0.,
                val_results_dict[str(Auxiliary.TRAJECTORY) + ' xent'])

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

        if self._args.use_all_trajectory():
            raise ValueError('Using the whole trajectory is not supported.')
            # Train IDs are a cross between training IDs and indices in the action sequence.
            # train_ids: List[Tuple[str, int]] = list()
            # for example_id, example in train_examples.items():
            #    for i in range(len(example.get_state_deltas())):
            #        train_ids.append((example_id, i))
        else:
            train_ids: List[Tuple[str, int]] = [(key, 0) for key in train_examples.keys()]

        val_examples: Dict[str, instruction_example.InstructionExample] = dataset.get_examples(
            dataset_split.DatasetSplit.VAL)

        # Clip gradients
        optimizer: torch.optim.Optimizer = training_arguments.get_optimizer('hex')(self.parameters())
        if training_arguments.get_max_gradient() > 0:
            torch.nn.utils.clip_grad_norm_(self.parameters(), training_arguments.get_max_gradient())

        num_epochs: int = 0
        max_acc = 0

        patience: float = training_arguments.get_initial_patience()
        countdown: int = int(patience)

        best_epoch_filename: str = ''

        while countdown > 0:
            logging.info('Starting epoch (hex predictor) ' + str(num_epochs))
            self._train_epoch(train_ids,
                              num_epochs,
                              train_examples,
                              training_arguments.get_batch_size(),
                              optimizer,
                              experiment)

            val_acc, val_xent = self._eval(train_examples, val_examples, experiment)

            save_desc: str = ''

            if val_acc > max_acc:
                logging.info('Best accuracy: ' + str(val_acc))
                max_acc = val_acc
                save_desc += '_bestacc'

            if save_desc:
                # Hacky: for now, always return the one who is best on card prediction only.
                # This seems to be better than xent.
                filename: str = \
                    os.path.join(training_arguments.get_save_dir(), 'model_' + str(num_epochs) + save_desc + '.pt')
                best_epoch_filename = filename

                patience *= training_arguments.get_patience_update_ratio()
                countdown = int(patience)
                logging.info('Resetting countdown to %d, patience is %d', countdown, patience)

                self.save(filename)

            num_epochs += 1
            countdown -= 1
            experiment.add_scalar_value('countdown', countdown)

        return best_epoch_filename
