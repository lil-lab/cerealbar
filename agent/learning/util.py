"""Utilities for training, e.g., for logging progress."""
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
