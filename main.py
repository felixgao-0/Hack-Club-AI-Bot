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
    text = event["text"]
    if event["channel"] != "C07JA93AMDZ": # Test channel
        print("ignoring wrong channel")
        return

    if not is_question(text):
        print("Likely not a question, ignoring")
        return
    
    if event.get("parent_user_id", event["user"]) != event["user"]:
        print("Not author of a thread, ignoring")
        return

    if event.get("subtype"):
        print("Ignoring, bot")
        return

    text_lower = text.lower()
    print(text_lower)
    if not text_lower.startswith("ai"):
        print("User did not opt for AI to respond")
        return
    
    if event["user"] not in ["U07BU2HS17Z", "U07BLJ1MBEE"]:
        print("Ignoring, not authorized to use bot")
        print(event)
        return

    print(event)
    #response = app.client.conversations_replies(channel=event["channel"], ts=event["thread"])
    #print(response['messages'][0])
    
    response_text = ask_ai(text)
    print(response_text)
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
                    "text": "*This bot uses AI, take with a few grains of salt. Refer to the constitution for exact information.* Bot by Felíx. :D"
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