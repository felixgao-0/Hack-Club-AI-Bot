import os

from slack_bolt import App

from ai import ask_ai

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

    if event["user"] != "U07BU2HS17Z": # If not me, testing only
        print("ignoring not felix")
        print(event)
        return

    if event["text"] not in ["is", "how", "who", "what", "why", "when", "?"]:
        print("Likely not a question, ignoring")
        return

    if False: # TODO: Allow users to opt out
        return

    response_text = ask_ai(event["text"])
    #response_text = {'id': 'chatcmpl-9zTQ7V2uSlelxy89sckwaYTlRMYTf', 'object': 'chat.completion', 'created': 1724438127, 'model': 'gpt-3.5-turbo-0125', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'Welcome to Arcade, <@U0782516RDE>! If you have any questions about how to participate or any other queries, feel free to ask. Happy hacking!', 'refusal': None}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 1098, 'completion_tokens': 36, 'total_tokens': 1134}, 'system_fingerprint': None} # type: ignore
    block = [
        {
          "type": "context",
          "text": {
            "type": "mrkdwn",
            "text": response_text
          }
        },
        {
          "type": "divider"
        },
        {
          "type": "section",
          "elements": [
            {
              "type": "mrkdwn",
              "text": "This bot sources information from ChatGPT with additional data for accuracy. **Take with a grain of salt. This bot is not the sole truth.** When in doubt, Bartosz will likely respond right after this, trust him over some silly AI. Developed by Felix to beat Bartosz lol." # type: ignore
            }
          ]
        }
      ]
    say(
        text=response_text["choices"][0]["message"]["content"], 
        thread_ts=event["ts"]
    )


if __name__ == "__main__":
    print("Woah its working!")
    app.start(port=3000)