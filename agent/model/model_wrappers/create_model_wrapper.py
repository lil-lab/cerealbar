"""Creates a model given a task."""
from typing import List

from pycrayon.crayon import CrayonExperiment

from agent.config import model_args
from agent.config import training_args
from agent.model.model_wrappers import model_wrapper
from agent.model.model_wrappers import action_generator_model_wrapper
from agent.model.model_wrappers import plan_predictor_wrapper


def get_model_wrapper(model_arguments: model_args.ModelArgs,
                      training_arguments: training_args.TrainingArgs,
                      vocabulary: List[str],
                      logger: CrayonExperiment = None,
                      load_pretrained: bool = True) -> model_wrapper.ModelWrapper:
    task: model_args.Task = model_arguments.get_task()
    if task == model_args.Task.PLAN_PREDICTOR:
        return plan_predictor_wrapper.PlanPredictorWrapper(model_arguments, training_arguments, vocabulary, logger)
    elif task == model_args.Task.ACTION_GENERATOR:
        return action_generator_model_wrapper.ActionGeneratorModelWrapper(model_arguments, vocabulary, logger,
                                                                          load_pretrained)
    elif task == model_args.Task.SEQ2SEQ:
        return Seq2SeqModelWrapper(model_arguments, vocabulary, logger)
