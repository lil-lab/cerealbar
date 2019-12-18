"""Logs evaluation."""


class EvaluationLogger:
    def __init__(self, filename: str, log: bool = True):
        self._filepointer = None
        self._active = bool(filename and log)
        if filename and log:
            self._filepointer = open(filename, 'w')

    def close(self) -> None:
        if self._filepointer:
            self._filepointer.close()

    def log(self, message: str) -> None:
        if self._filepointer and self._active:
            self._filepointer.write(message + '\n')
            self._filepointer.flush()

    def active(self) -> bool:
        return bool(self._filepointer and self._active)

    def disable_logging(self):
        self._active = False

    def enable_logging(self):
        self._active = True


def quick_log(filename, message):
    logger = EvaluationLogger(filename)
    logger.log(message)
    logger.close()