import os

from slack_bolt import App

from utils import ask_ai, is_question

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

@app.event("message")
def handle_message_events(event, say, client):
    text = event["text"]
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

    if event["user"] not in ["U07BU2HS17Z", "U07BLJ1MBEE"]:
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
    #response_text = {'id': 'chatcmpl-9zaUbHwHybVcyQqwMJcjCwu72svn5', 'object': 'chat.completion', 'created': 1724465313, 'model': 'gpt-3.5-turbo-0125', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'I am an AI bot developed internally and do not use any specific LLM (Large Language Model). My purpose is to provide helpful information and assist users in understanding how to participate in the Arcade hackathon organized by Hack Club for high schoolers. If you have any questions about the hackathon or need further assistance, feel free to ask!', 'refusal': None}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 1159, 'completion_tokens': 68, 'total_tokens': 1227}, 'system_fingerprint': None} # type: ignore
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
def update_message(ack, body, say):
    if body['user']['id'] != body['message']['parent_user_id']:
        print("Ignoring btn press, doesn't own action :/")
        return

    ack()

    thread_ts = body["message"]['thread_ts']
    thread_channel = body['channel']['id']
    response = app.client.conversations_replies(channel=thread_channel, ts=thread_ts)

    top_message = response["messages"]
    print(top_message)

    app.client.reactions_add(
        channel=thread_channel,
        name="spin-loading",
        timestamp=body['message']['ts']
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
    app.client.reactions_remove(
        channel=thread_channel,
        name="spin-loading",
        timestamp=body['message']['ts']
    )



if __name__ == "__main__":
    print("Woah its working!")
    app.start(port=3000)