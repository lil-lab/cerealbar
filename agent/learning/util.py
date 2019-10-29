"""Utilities for training, e.g., for logging progress."""
from typing import List, Any, Tuple

import certifi
import slack
import ssl as ssl_lib

SLACK_TOKEN: str = ''


def send_slack_message(username, message, channel):
    """Sends a message to your Slack channel.
    Input:
        username (str): Username to send from.
        message (str): The message to send.
        channel (str): Channel to send the message to.
    """
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    client = slack.WebClient(SLACK_TOKEN, ssl=ssl_context)
    client.chat_postMessage(
        channel=channel,
        text=message,
        username=username,
        icon_emoji=':robot_face:')


def evaluate_set_precision_recall(predicted_set: List[Any], target_set: List[Any]) -> Tuple[float, float, float]:
    """ Evaluates the precision and recall of two sets of items.

    Arguments:
        predicted_set: List[Any]. The set of predictions.
        target_set: List[Any]. The correct set.

    Returns: tuple of floats (accuracy, precision, and recall).

    """
    accuracy: float = 1. if predicted_set == target_set else 0.

    num_overlap: int = len(set(target_set) & set(predicted_set))

    precision: float = 1.
    if predicted_set:
        precision = float(num_overlap) / len(predicted_set)
    recall: float = 1.
    if target_set:
        recall = float(num_overlap) / len(target_set)

    return accuracy, precision, recall
