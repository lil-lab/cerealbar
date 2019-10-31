from __future__ import annotations

import logging
import torch

from agent import util
from agent.environment import agent_actions
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List


def constrained_argmax_sampling(probabilities: torch.Tensor,
                                possible_actions: List[agent_actions.AgentAction] = None) -> agent_actions.AgentAction:
    """ Samples the most probable action according to the probability distribution.

    Assumes that the probabilities are ordered the same way as AGENT_ACTIONS.
    """
    if possible_actions:
        mask: List[float] = []
        for action in agent_actions.AGENT_ACTIONS:
            if action in possible_actions:
                mask.append(1.)
            else:
                mask.append(0.)
        masked_probabilities = torch.tensor(mask).to(util.DEVICE) * probabilities
        highest_probability_action = agent_actions.AGENT_ACTIONS[masked_probabilities.max(0)[1]]

        if highest_probability_action not in possible_actions:
            # This is AFTER masking, so will only happen if this distribution is zeros.
            logging.warn('Action %r had highest masked probability, but was not possible.' % highest_probability_action)
            logging.warn('Masked probabilities: ' + str(masked_probabilities))

            # Just choose a safe action, e.g., RR.
            highest_probability_action = agent_actions.AgentAction.RR
        return highest_probability_action
    return agent_actions.AGENT_ACTIONS[probabilities.squeeze().max(0)[1]]
