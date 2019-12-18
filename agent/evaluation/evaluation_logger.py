"""Logs evaluation."""


class EvaluationLogger:
    def __init__(self, filename: str, log: bool = True):
        self._filepointer = None
        if filename and log:
            self._filepointer = open(filename, 'w')

    def close(self) -> None:
        if self._filepointer:
            self._filepointer.close()

    def log(self, message: str) -> None:
        if self._filepointer:
            self._filepointer.write(message + '\n')
            self._filepointer.flush()

    def active(self) -> bool:
        return bool(self._filepointer)


def quick_log(filename, message):
    logger = EvaluationLogger(filename)
    logger.log(message)
    logger.close()