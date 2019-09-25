"""Contains an enum defining all the actions an agent can take.

Classes:
    AgentAction (Enum): All actions an agent can take.

Consts:
    AGENT_ACTIONS (List): A list of AgentActions in a specified order.

"""
from enum import Enum


class AgentAction(Enum):
    """ Agent actions are all actions that an agent can execute in the state.

        MF = Move forward
        MB = Move backwards
        RR = Rotate right
        RL = Rotate left

        START = Action that indicates the agent is starting to follow an instruction. The Unity game does not execute
                it.
        STOP = Action that indicates the agent has finished following an instruction and can move onto the next one.
    """
    MF: str = 'MF'
    MB: str = 'MB'
    RR: str = 'RR'
    RL: str = 'RL'
    START: str = 'START'
    STOP: str = 'STOP'

    def __str__(self):
        return self.value


# This stores all of the actions in an ordered list that can be used as a vocabulary for the model.
AGENT_ACTIONS = [data for data in AgentAction]
