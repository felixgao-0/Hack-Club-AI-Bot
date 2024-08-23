import json
import os

from slack_bolt import App

# Initialize your app with your bot token and signing secret
app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

"""
def ask_ai(question: str) -> dict:
    url = "https://jamsapi.hackclub.dev/openai/chat/completions"
    headers = {'Authorization': f'Bearer {os.environ["OPEN_AI_ARCADE"]}'}
    with open('messages.json') as f:
        prompt = json.load(f)
    prompt.append({"role": "user", "content": question})
    req_data = {
        'model': 'gpt-3.5-turbo',
        'messages': prompt,
    }
    r = requests.post(url, json=req_data, headers=headers)
    return r.json()
"""
@app.message("hello")
def message_hello(message, say):
    # say() sends a message to the channel where the event was triggered
    say(f"Hey there <@{message['user']}>!")
"""
@app.message("hi")
def question_handler(message, say):
    print("hi, we got a message in the channel!")
    thread_ts = message["ts"]
    say(text=ask_ai(message["text"]), thread_ts=thread_ts) 
"""

if __name__ == "__main__":
    app.start(port=int(os.environ.get("0.0.0.0", 3000)))