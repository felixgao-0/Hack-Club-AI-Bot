import os

from slack_bolt import App

from utils import ask_ai, is_question

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

@app.event("app_mention")
def handle_app_mention_events(body, say):
    user = body["event"]["user"]
    say(f"Hello <@{user}>! How can I help you today?")


@app.event("message")
def handle_message_events(event, say):
    if event["channel"] != "C07JA93AMDZ": # Test channel
        print("ignoring wrong channel")
        return

    if not is_question(event["text"]):
        print("Likely not a question, ignoring")
        return
    
    if event.get("parent_user_id", event["user"]) != event["user"]:
        print("Not author of a thread, ignoring")
        return

    if event.get("subtype"):
        print("Ignoring, bot")
        return
    
    if event["user"] not in ["U07BU2HS17Z"]:
        print("ignoring not one of the felixs")
        print(event)
        return

    if event["user"] in ["opt-out-list"]: # TODO: Allow users to opt out
        return

    print(event)

    response_text = ask_ai(event["text"])
    block = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": response_text["choices"][0]["message"]["content"]
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "*This bot uses AI, take with a few grains of salt. Refer to the constitution for exact information.* Bot by Felíx. #ai-bartosz to opt out."
                }
            ]
        }
    ]
    say(
        text=response_text["choices"][0]["message"]["content"],
        blocks=block, 
        thread_ts=event["ts"]
    )


if __name__ == "__main__":
    print("Woah its working!")
    app.start(port=3000)