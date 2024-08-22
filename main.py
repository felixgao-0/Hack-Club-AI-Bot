import logging
import os

from flask import Flask

from slack_sdk import WebClient, rtm
from slack_sdk.errors import SlackApiError

from slackeventsapi import SlackEventAdapter


logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_token = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(token=slack_token)

slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events", app)


# An example of one of your Flask app's routes
@app.route("/")
def hello():
  return "Woah, hi there!"


@slack_events_adapter.on("message.channels")
def on_message(event_data):
    print("WOAH THERE!")

"""
try:
    response = client.chat_postMessage(
        channel="C0P5NE354",
        text="Hello from your app! :tada:"
    )
except SlackApiError as e:
    # You will get a SlackApiError if "ok" is False
    assert e.response["error"]    # str like 'invalid_auth', 'channel_not_found'
"""

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=3000)