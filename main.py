import os

from slack_bolt import App

from utils import ask_ai, is_question, get_username

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

authorized = ["U07BU2HS17Z", "U07BLJ1MBEE"]

@app.event("message")
def handle_message_events(event, say, client):
    try:
        text = event["text"]
    except KeyError as e:
        print(f"Well we got an error D:\n{e}\n{event}")
        return
    if event["channel"] != "C07JA93AMDZ": # Test channel
        print("Ignoring: Incorrect Channel")
        return

    if not is_question(text):
        print("Ignoring: Not likely a question")
        return

    if event.get("parent_user_id", event["user"]) != event["user"]:
        print("Ignoring: Not the thread author")
        return

    if event.get("subtype"):
        print("Ignoring: Bots don't respond to bots")

    if event["user"] not in authorized:
        print("Ignoring, not authorized to use bot")
        print(event)
        return

    text_lower = text.lower()
    print(text_lower)
    if not text_lower.startswith("ai"):
        print("User did not opt for AI to respond D:")
        block = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hello :wave:! I'm an AI help bot developed by Felíx. Press the button below to have me answer your question!"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "plain_text",
                        "text": "Pro Tip: Start your message with 'AI' to get a response instantly!",
                        "emoji": True
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":blob_help: Answer My Question!",
                            "emoji": True
                        },
                        "value": "yes",
                        "action_id": "answer_question"
                    }
                ]
            }
        ]
        say(
            text="Press the button below to have an AI bot answer your question!",
            blocks=block, 
            thread_ts=event["ts"]
        )
        return

    print(event)
    #response = app.client.conversations_replies(channel=event["channel"], ts=event["event_ts"])
    #print(response['messages'][0])
    
    client.reactions_add(
        channel=event["channel"],
        name="spin-loading",
        timestamp=event["event_ts"]
    )
    client.reactions_add(
        channel=event["channel"],
        name="bartosz",
        timestamp=event["event_ts"]
    )

    response_text = ask_ai(text)
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
                    "text": "*This bot uses AI, take with a few grains of salt. Refer to the constitution as always.* Bot by Felíx. :D"
                }
            ]
        }
    ]
    say(
        text=response_text["choices"][0]["message"]["content"],
        blocks=block, 
        thread_ts=event["ts"]
    )
    client.reactions_remove(
        channel=event["channel"],
        name="spin-loading",
        timestamp=event["event_ts"]
    )


@app.action("answer_question")
def answer_question_events(ack, client, body, say):
    ack()
    if body['user']['id'] != body['message']['parent_user_id']:
        print("Ignoring btn press, doesn't own action :/")
        return

    if body['user']['id'] not in authorized:
        print("Ignoring btn press, not authorized")
        return

    context_data: str = ""

    thread_ts = body["message"]['thread_ts']
    thread_channel = body['channel']['id']
    response = client.conversations_replies(channel=thread_channel, ts=thread_ts)

    for index, message in enumerate(response["messages"]):
        if index == 0: # Ignore first one, we'll use it later on
            continue
        context_data += f"{get_username(app, message['user'])} SAID: {message['text']} "

    client.reactions_add(
        channel=thread_channel,
        name="spin-loading",
        timestamp=body['message']['ts']
    )

    response_text = ask_ai(response["messages"][0]['text'], context=context_data)
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
                    "text": "*This bot uses AI, take with a few grains of salt. Refer to the constitution as always.* Bot by Felíx. :D"
                }
            ]
        }
    ]
    say(
        text=response_text["choices"][0]["message"]["content"],
        blocks=block, 
        thread_ts=body['message']['ts']
    )
    client.reactions_remove(
        channel=thread_channel,
        name="spin-loading",
        timestamp=body['message']['ts']
    )



if __name__ == "__main__":
    print("Woah its working!")
    app.start(port=3000)