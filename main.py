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
        say(
            text="""
            Hi! I'm an AI bot that answers questions.
            To have me answer your question press the button below!

            (Pro tip: start your message with 'ai' to automatically get a response)
            """
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
    client.reactions_remove(
        channel=event["channel"],
        name="spin-loading",
        timestamp=event["event_ts"]
    )


if __name__ == "__main__":
    print("Woah its working!")
    app.start(port=3000)