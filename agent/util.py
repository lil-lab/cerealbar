"""Generic utilities useful for the agent code."""
import progressbar
import torch

if torch.cuda.device_count() >= 1:
    DEVICE: torch.device = torch.device('cuda')
else:
    DEVICE: torch.device = torch.device('cpu')


def get_progressbar(name: str, size: int) -> progressbar.ProgressBar:
    return progressbar.ProgressBar(maxval=size,
                                   widgets=[name,
                                            progressbar.Bar('=', '[', ']'),
                                            ' ',
                                            progressbar.Percentage(),
                                            ' ',
                                            progressbar.ETA()])
