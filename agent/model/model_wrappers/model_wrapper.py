"""Abstract class for a model wrapper.

Model wrappers are required for training on multiple GPUs.
"""

from __future__ import annotations

import logging
import torch
import torch.nn as nn

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from agent.config import model_args

if TYPE_CHECKING:
    from typing import Any, List, Tuple
    from pycrayon import crayon
    from agent.data import instruction_example


class ModelWrapper(ABC):
    def __init__(self,
                 model_arguments: model_args.ModelArgs,
                 logger: crayon.CrayonExperiment = None):
        self._args: model_args.ModelArgs = model_arguments
        self._task: model_args.Task = model_arguments.get_task()

        self._parallelized: bool = False

        if torch.cuda.device_count() > 1:
            logging.info('Using %r GPUs' % torch.cuda.device_count())
            self._parallelized = True

        self._model: nn.Module = None
        self._logger: crayon.CrayonExperiment = logger

    def __str__(self):
        return str(self._model)

    def _put_on_device(self):
        if self._parallelized:
            self._model = nn.DataParallel(self._model)

        if torch.cuda.device_count() > 0:
            self._model: nn.Module = self._model.cuda()

    @abstractmethod
    def train_loop(self, dataset, game_args, eval_args, training_args, experiment) -> str:
        pass

    @abstractmethod
    def loss(self, examples: List[instruction_example.InstructionExample]) -> Tuple[torch.Tensor, Any]:
        pass

    def named_parameters(self):
        if self._parallelized:
            return self._model.module.named_parameters()
        else:
            return self._model.named_parameters()

    def parameters(self):
        return self._model.parameters()

    def train(self) -> nn.Module:
        return self._model.train()

    def eval(self) -> nn.Module:
        return self._model.eval()

    def load(self, filename: str) -> None:
        if self._parallelized:
            self._model.module.load(filename)
        else:
            self._model.load(filename)

    def save(self, filename: str) -> None:
        if self._parallelized:
            self._model.module.save(filename)
        else:
            self._model.save(filename)

    def get_predictions(self, *args, **kwargs) -> List[Any]:
        if self._parallelized:
            # This ignores parallelization because this only should be used for inference.
            return self._model.module.get_predictions(*args, **kwargs)
        else:
            return self._model.get_predictions(*args, **kwargs)

    def get_task(self) -> model_args.Task:
        return self._task

