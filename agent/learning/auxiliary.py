"""Types of auxiliaries."""

from enum import Enum


class Auxiliary(Enum):
    TRAJECTORY: str = 'TRAJECTORY'
    INTERMEDIATE_GOALS: str = 'INTERMEDIATE_GOALS'
    FINAL_GOALS: str = 'FINAL_GOALS'
    OBSTACLES: str = 'OBSTACLES'
    AVOID_LOCS: str = 'AVOID_LOCS'
    IMPLICIT: str = 'IMPLICIT'

    def __str__(self) -> str:
        return self.value
