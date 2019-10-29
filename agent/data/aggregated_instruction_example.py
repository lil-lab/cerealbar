class AggregatedInstructionExample:
    def __init__(self, implicit: bool):
        self._implicit: bool = implicit

    def implicit(self) -> bool:
        return self._implicit
