"""Computes the loss for a batch and applies updates."""
from typing import Any, Dict, List

import torch

from agent.learning import auxiliary
from agent.model.model_wrappers import model_wrapper


def apply_batch_loss(model: model_wrapper.ModelWrapper, examples: List[Any], optimizer: torch.optim.Optimizer):
    """ Trains a batch for a model with auxiliary losses. """
    optimizer.zero_grad()

    # Compute the main loss and auxiliary losses
    main_loss, auxiliary_losses = model.loss(examples)

    total_loss = main_loss

    # Apply the auxiliary losses
    auxiliary_coefficients: Dict[auxiliary.Auxiliary, float] = model.get_auxiliaries()

    for aux_type, coefficient in auxiliary_coefficients.items():
        total_loss += coefficient * auxiliary_losses[aux_type]

    total_loss.backward()
    optimizer.step()

    return total_loss.item(), main_loss, auxiliary_losses
