""" An agent.

Classes:
    Agent (RotatableObject): The agent type.
"""
from typing import Optional

from agent.environment import environment_objects
from agent.environment import position
from agent.environment import rotation


class Agent(environment_objects.RotatableObject):
    def __init__(self,
                 agent_type: environment_objects.ObjectType,
                 agent_position: Optional[position.Position] = None,
                 agent_rotation: Optional[rotation.Rotation] = None):
        if not (agent_type == environment_objects.ObjectType.LEADER or
                agent_type == environment_objects.ObjectType.FOLLOWER):
            raise ValueError('Agent can only be created with type LEADER or FOLLOWER; ' +
                             'got type %r' % agent_type)

        super(Agent, self).__init__(agent_position, agent_rotation, agent_type)

    def update(self, agent_position: position.Position, agent_rotation: rotation.Rotation) -> None:
        self._position = agent_position
        self._rotation = agent_rotation

    def __eq__(self, other) -> bool:
        """ For equality of agents, just need to make sure they are of the same type (Leader vs. Follower)"""
        if isinstance(other, self.__class__):
            return self._type == other.get_type()
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __str__(self):
        return '%r \t %r \t %r' % (self._type, self.get_position(), self.get_rotation())
