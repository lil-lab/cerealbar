import logging
import math
import random
from typing import Any, Dict, List, Set, Tuple

import torch
from pycrayon import crayon
from torch import nn

from agent import util
from agent.config import evaluation_args
from agent.config import game_args
from agent.config import model_args
from agent.config import training_args
from agent.data import aggregated_instruction_example
from agent.data import dataset_split
from agent.data import game_dataset
from agent.data import instruction_example
from agent.environment import agent_actions
from agent.learning import auxiliary
from agent.learning import batch_loss
from agent.learning import plan_losses
from agent.model.model_wrappers import model_wrapper
from agent.model.models import action_predictor_model

MAXIMUM_NUM_END_TO_END_EPOCHS = 25


class ActionGeneratorModelWrapper(model_wrapper.ModelWrapper):
    def __init__(self,
                 model_arguments: model_args.ModelArgs,
                 vocabulary: List[str],
                 logger: crayon.CrayonExperiment,
                 load_pretrained: bool = True,
                 end_to_end: bool = False):
        super(ActionGeneratorModelWrapper, self).__init__(model_arguments, logger)

        self._end_to_end = end_to_end or model_arguments.get_decoder_args().end_to_end()

        if self._end_to_end:
            raise ValueError('End-to-end training is not cleaned yet!')
        else:
            self._auxiliaries = dict()

        self._model: action_predictor_model.ActionPredictorModel = action_predictor_model.ActionPredictorModel(
            model_arguments, vocabulary, list(self._auxiliaries.keys()), load_pretrained, self._end_to_end)
        self._task: model_args.Task = model_arguments.get_task()

        self._put_on_device()

    def get_auxiliaries(self):
        return self._auxiliaries

    def state_dict(self):
        return self._model.state_dict()

    def loss(self, examples: List[instruction_example.InstructionExample]) -> Tuple[torch.Tensor, Any]:
        if self._parallelized:
            inputs = self._model.module.batch_inputs(examples)
        else:
            inputs = self._model.batch_inputs(examples)

        # Scores are size B x T x A, where A is the total number of possible actions.
        scores, auxiliaries = self._model(*inputs)

        auxiliary_losses: Dict[auxiliary.Auxiliary, Any] = dict()

        token_neglogprobs = -nn.functional.log_softmax(scores, dim=2)

        # Scores are size B x E x E, where E is the environment width/depth.
        losses: List[torch.Tensor] = []
        for i, example in enumerate(examples):
            for j, action in enumerate(example.get_action_sequence()):
                step_scores = token_neglogprobs[i][j]
                action_score: torch.Tensor = step_scores[agent_actions.AGENT_ACTIONS.index(agent_actions.AgentAction(
                    action))]
                losses.append(action_score)

            plan_losses.compute_per_example_auxiliary_losses(example,
                                                             i,
                                                             auxiliaries,
                                                             list(self._auxiliaries),
                                                             auxiliary_losses,
                                                             self._args.get_decoder_args().weight_trajectory_by_time(),
                                                             self._args.get_state_rep_args().full_observability())

        for auxiliary_name in self._auxiliaries:
            auxiliary_losses[auxiliary_name] = torch.mean(torch.stack(tuple(auxiliary_losses[auxiliary_name])))

        return torch.mean(torch.stack(tuple(losses))), auxiliary_losses

    def _train_epoch(self,
                     epoch_idx: int,
                     train_examples: Dict[str, instruction_example.InstructionExample],
                     batch_size: int,
                     optimizer: torch.optim.Optimizer,
                     experiment: crayon.CrayonExperiment,
                     aggregate_examples: bool,
                     aggregated_train_examples: List[Dict[str,
                                                          aggregated_instruction_example.AggregatedInstructionExample]],
                     compiled_example_set: Set[str],
                     game_arguments: game_args.GameArgs,
                     evaluation_argumentss: evaluation_args.EvaluationArgs,
                     aggregated_buffer: Set[Tuple[str, int]]):
        self.train()
        num_batches: int = 0
        train_loss_sum: float = 0

        # The train IDs set pairs example IDs with the epoch in which they were created (-1 for static data).
        # It is augmented during training to add new examples to this epoch index, so items are removed until it's empty
        train_ids_set = {(key, -1) for key in train_examples.keys()}

        losses_dict = dict()
        main_loss_sum: float = 0

        total_num_examples_seen: int = 0

        # Aggregate new training examples. Similar to Dagger (Ross et al. 2011), this first aggregates examples, then
        # trains on them (plus the new data).
        new_aggregated_examples = None
        if aggregate_examples:
            raise ValueError('Example aggregation not supported yet.')
            logging.info('Aggregated buffer has ' + str(len(aggregated_buffer)) + ' examples.')
            new_aggregated_examples: Dict[str, aggregated_instruction_example.AggregatedInstructionExample] = \
                perform_example_aggregation(train_examples,
                                            compiled_example_set,
                                            epoch_idx,
                                            game_args,
                                            eval_args,
                                            self,
                                            allow_duplicates=True)  # Allow duplicate examples during training
            new_ids: List[Tuple[str, int]] = [(key, epoch_idx) for key in new_aggregated_examples.keys()]
            logging.info('Generated ' + str(len(new_aggregated_examples)) + ' new examples.')

            # Add it to the compiled examples
            for example_id, new_example in new_aggregated_examples.items():
                # Remove the epoch at the end!
                compiled_example_set.add(new_example.hash_rep())

            # Add to the aggregated buffer
            aggregated_buffer = aggregated_buffer | set(new_ids)

            # Now randomly choose a subset, and combine with the train IDs
            # This doesn't guarantee that the most recently collected examples appear in this epoch
            train_ids_set = train_ids_set | set(random.sample(aggregated_buffer,
                                                              min(len(train_examples), len(aggregated_buffer))))

            example_ids = list(train_examples.keys())
            random.shuffle(example_ids)
            inorder_ids: List[str] = list()
            for ex_id in example_ids:
                inorder_ids.extend([ex for ex in train_ids_set if '-'.join(ex[0].split('-')[:2]) == ex_id])
            logging.info('IDs used for batch: ')
            logging.info(','.join([ex_id[0] for ex_id in inorder_ids]))
            if len(set(inorder_ids)) != len(inorder_ids):
                raise ValueError(
                    'Inorder IDs was not a set -- has duplicate members, ' + str(len(set(inorder_ids))) + ' vs. ' + str(
                        len(inorder_ids)))
            if set(inorder_ids) != set(train_ids_set):
                # These should just be examples that are too long because the original example is too long.
                logging.info('Train IDs not in inorder IDs:')
                logging.info(','.join([ex_id[0] for ex_id in set(train_ids_set) - set(inorder_ids)]))
                logging.info('Inorder IDs not in train IDs:')
                logging.info(','.join([ex_id[0] for ex_id in set(inorder_ids) - set(train_ids_set)]))
                logging.warn('Set of inorder IDs is not the same as the set of train ids')
        else:
            inorder_ids = list(train_ids_set)
            random.shuffle(inorder_ids)

        logging.info('Starting epoch #%r with %r examples.' % (epoch_idx, len(inorder_ids)))

        with util.get_progressbar('epoch ' + str(epoch_idx), len(inorder_ids)) as pbar:
            for start_idx in range(0, len(inorder_ids), batch_size):
                pbar.update(num_batches)
                sampled_ids = inorder_ids[start_idx:min(start_idx + batch_size, len(inorder_ids))]

                # Construct the list of examples that should be used to update the model parameters.
                update_examples: List[Union[AggregatedExample, Example]] = list()

                for identifier, epoch in sampled_ids:
                    # This example was sampled from the first epoch.
                    if epoch < 0:
                        update_examples.append(train_examples[identifier])
                    elif epoch == epoch_idx:
                        # This example was recently added (i.e., during this epoch).
                        update_examples.append(new_aggregated_examples[identifier])
                    else:
                        # Take from the aggregated dataset for the specified epoch.
                        update_examples.append(aggregated_train_examples[epoch][identifier])

                # Do an update, and log the performance of the metrics.
                loss, main_loss, auxiliary_losses = \
                    batch_loss.apply_batch_loss(self, update_examples, optimizer)

                for auxiliary_type, losses in auxiliary_losses.items():
                    loss_name = str(auxiliary_type)
                    if loss_name not in losses_dict:
                        losses_dict[loss_name] = 0.
                    losses_dict[loss_name] += losses.item()

                experiment.add_scalar_value('batch loss', loss)
                if math.isnan(loss):
                    raise ValueError('NaN Loss')

                train_loss_sum += loss
                main_loss_sum += main_loss.item()
                num_batches += 1

                total_num_examples_seen += len(sampled_ids)
                pbar.update(total_num_examples_seen)

        avg_loss: float = float(train_loss_sum / num_batches)
        logging.info('Average loss per batch: %f', avg_loss)
        experiment.add_scalar_value('train loss', avg_loss)
        experiment.add_scalar_value('train action prediction loss', float(main_loss_sum / num_batches))
        for loss, loss_sum in losses_dict.items():
            experiment.add_scalar_value('train ' + str(loss) + ' loss', float(loss_sum / num_batches))

        # Add the new aggregated examples to the training set.
        return new_aggregated_examples, aggregated_buffer

    def train_loop(self,
                   dataset: game_dataset.GameDataset,
                   game_arguments: game_args.GameArgs,
                   evaluation_arguments: evaluation_args.EvaluationArgs,
                   training_arguments: training_args.TrainingArgs,
                   experiment: crayon.CrayonExperiment) -> str:
        train_examples: Dict[str, instruction_example.InstructionExample] = dataset.get_examples(
            dataset_split.DatasetSplit.UPDATE)
        validation_examples: Dict[str, instruction_example.InstructionExample] = dataset.get_examples(
            dataset_split.DatasetSplit.VALIDATION)
        validation_games: Dict[str, instruction_example.InstructionExample] = dataset.get_games(
            dataset_split.DatasetSplit.VALIDATION)

        # Clip gradients
        optimizer: torch.optim.Optimizer = \
            training_arguments.get_optimizer(self.get_arguments().get_task(),
                                             self.get_arguments().get_decoder_args().end_to_end())(self.parameters())
        if training_arguments.get_max_gradient() > 0:
            torch.nn.utils.clip_grad_norm_(self.parameters(), training_arguments.get_max_gradient())
        batch_size: int = training_arguments.get_batch_size()

        num_epochs: int = 0

        maximum_card_state_accuracy = 0
        maximum_proportion_instructions_followed = 0
        maximum_proportion_points_scored = 0

        patience: float = training_arguments.get_initial_patience()
        countdown: int = int(patience)

        # Aggregated datasets
        aggregated_train_examples: List[Dict[str, aggregated_instruction_example.AggregatedInstructionExample]] = list()
        aggregated_validation_examples: List[Dict[str, aggregated_instruction_example.AggregatedInstructionExample]] = \
            list()

        compiled_example_set_train: Set[str] = set()
        for example_id, example in train_examples.items():
            # Need to use a string instead so it can be hashed.
            compiled_example_set_train.add(example.hash_representation())
        compiled_example_set_validation: Set[str] = set()
        for example_id, example in validation_examples.items():
            compiled_example_set_validation.add(example.hash_representation())

        best_filename: str = ''

        aggregated_buffer: Set[Tuple[str, int]] = set()

        while countdown > 0 and (not self._end_to_end or num_epochs < MAXIMUM_NUM_END_TO_END_EPOCHS):
            logging.info('Starting epoch (action predictor) ' + str(num_epochs))
            total_num_examples: int = (len(train_examples) +
                                       sum([len(epoch_examples) for epoch_examples in aggregated_train_examples]))
            total_num_validation_examples: int = \
                (len(validation_examples) + sum([len(epoch_examples) for epoch_examples in
                                                 aggregated_validation_examples]))

            if training_arguments.aggregate_examples():
                experiment.add_scalar_value('number of training examples', total_num_examples, step=num_epochs)
                experiment.add_scalar_value('number of validation examples', total_num_validation_examples,
                                            step=num_epochs)

            new_examples, aggregated_buffer = \
                self._train_epoch(num_epochs,
                                  train_examples,
                                  batch_size,
                                  optimizer,
                                  experiment,
                                  training_arguments.aggregate_examples(),
                                  aggregated_train_examples,
                                  compiled_example_set_train,
                                  game_arguments,
                                  evaluation_arguments,
                                  aggregated_buffer)

            if training_arguments.aggregate_examples():
                logging.info('Collected ' + str(len(new_examples)) + ' new training examples!')
                logging.info('Num marked as implicit: '
                             + str(len([ex for ex in new_examples.values() if ex.implicit()])))
                aggregated_train_examples.append(new_examples)

                num_card = 0
                num_pos = 0
                for example in new_examples.values():
                    if example.get_type() == Aggregatedinstruction_example.InstructionExampleType.INVALID_CARD_STATE:
                        num_card += 1
                    else:
                        num_pos += 1
                logging.info('Created ' + str(num_card) + ' incorrect card state examples; ' +
                             str(num_pos) + ' position examples.')
                experiment.add_scalar_value('new invalid card examples', num_card, step=num_epochs)
                experiment.add_scalar_value('new incorrect position examples', num_pos, step=num_epochs)

                # Save the examples under a file specific to this epoch.
                if new_examples:
                    with open(
                            os.path.join(training_arguments.get_save_dir(),
                                         'aggregated_train_examples_epoch' + str(num_epochs) + '.pkl'), 'wb') as ofile:
                        pickle.dump(new_examples, ofile)

            val_exact_acc, val_card_acc, val_follow_prop, val_score_prop = \
                self._eval(train_examples,
                           validation_examples,
                           aggregated_train_examples[0] if aggregated_train_examples else None,
                           validation_games,
                           game_args,
                           eval_args,
                           experiment,
                           num_epochs)

            suffix = ''
            better = False
            if val_card_acc > maximum_card_state_accuracy:
                logging.info('Best card acc at %f', val_card_acc)
                maximum_card_state_accuracy = val_card_acc
                suffix += '_card'
                better = True
            if val_follow_prop > maximum_proportion_instructions_followed:
                logging.info('Highest prop followed at %f', val_follow_prop)
                maximum_proportion_instructions_followed = val_follow_prop
                suffix += '_follow'
                better = True
            if val_score_prop > maximum_proportion_points_scored:
                logging.info('Highest prop score at %f', val_score_prop)
                maximum_proportion_points_scored = val_score_prop
                suffix += '_score'
                better = True

            if better:
                filename = os.path.join(training_arguments.get_save_dir(), 'model_' + str(num_epochs) + suffix + '.pt')
                best_filename = filename
                patience *= training_arguments.get_patience_update_ratio()
                countdown = int(patience)
                logging.info('Resetting countdown to ' + str(countdown))
                self.save(filename)

            num_epochs += 1
            countdown -= 1
            experiment.add_scalar_value('countdown', countdown)
        return best_filename
