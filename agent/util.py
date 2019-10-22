"""Generic utilities useful for the agent code."""
import progressbar


def get_progressbar(name: str, size: int) -> progressbar.ProgressBar:
    return progressbar.ProgressBar(maxval=size,
                                   widgets=[name,
                                            progressbar.Bar('=', '[', ']'),
                                            ' ',
                                            progressbar.Percentage(),
                                            ' ',
                                            progressbar.ETA()])
