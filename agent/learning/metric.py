"""Contains the class defining a metric in the CerealBar game."""

from enum import Enum


class Metric(Enum):
    # Exact sequence accuracy.
    SEQUENCE_ACCURACY: str = 'SEQUENCE_ACCURACY'

    # Card accuracy for the final state.
    CARD_ACCURACY: str = 'CARD_ACCURACY'

    # Relaxed environment accuracy -- thresholded distance from correct location and no rotation requirement
    RELAXED_ENVIRONMENT_ACCURACY: str = 'RELAXED_ENVIRONMENT_ACCURACY'

    # Exact environment accuracy -- exact location and rotation must be correct
    EXACT_ENVIRONMENT_ACCURACY: str = 'EXACT_ENVIRONMENT_ACCURACY'

    # Distance from correct state
    AGENT_DISTANCE: str = 'AGENT_DISTANCE'

    # Position prefix: what proportion of the correct sequences visited did it get right (prefix only)
    POSITION_PREFIX: str = 'POSITION_PREFIX'

    # Score for a game
    SCORE: str = 'SCORE'

    PROPORTION_FOLLOWED_CASCADING: str = 'PROPORTION_FOLLOWED_CASCADING'

    PROPORTION_VALID_CASCADING: str = 'PROPORTION_VALID_CASCADING'

    PROPORTION_POINTS_CASCADING: str = "PROPORTION_POINTS_CASCADING"

    def __str__(self) -> str:
        return self.value


