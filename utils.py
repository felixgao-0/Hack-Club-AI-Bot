import json
import os
import re
import threading
import time
from typing import Optional

import requests

shop_data = None

def ask_ai(question: str, *, context: Optional[list] = None) -> dict:
    """
    Ask ChatGPT a Arcade related question!
    """
    global shop_data
    if not shop_data:
        print("No shop data, lets go fetch it!")
        shop_data = _get_data() # Get data if its somehow missing D:
    return {'id': 'chatcmpl-9zaUbHwHybVcyQqwMJcjCwu72svn5', 'object': 'chat.completion', 'created': 1724465313, 'model': 'gpt-3.5-turbo-0125', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'This is a blank prompt for test purposes used to avoid wasting open ai credits. Hi!', 'refusal': None}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 1159, 'completion_tokens': 68, 'total_tokens': 1227}, 'system_fingerprint': None} # type: ignore
    url = "https://jamsapi.hackclub.dev/openai/chat/completions"
    headers = {'Authorization': f'Bearer {os.environ["OPEN_AI_ARCADE"]}'}

    prompt = get_json('json_data/messages.json')

    prompt.append({"role": "user", "content": f"USER QUESTION: {question}"})
    prompt.append({"role": "system", "content": shop_data})
    if context:
        for item in context:
            prompt.append(item)
    req_data = {
        'model': 'gpt-3.5-turbo',
        'messages': prompt,
    }
    r = requests.post(url, json=req_data, headers=headers)
    return r.json()


def is_question(text: str) -> bool:
    """
    Detect questions.
    """
    # List of key words that indicate a question
    question_words = ["who", "what", "where", "when", "why", "how", "does", "is", "did", "help"]
    if text.strip().endswith('?'):
        return True

    # Check if text contains question words
    return any(word in text.lower() for word in question_words)


def _get_data():
    print("Getting shop data")
    url = "https://hackclub.com/api/arcade/shop/"
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Request failed with status code {r.status_code}")

    data_txt = "ITEMS: "

    for item in r.json():
        name = item['name']
        small_name = item.get('smallName', '')
        tickets = item['hours']
        stock = item['stock'] if item['stock'] is not None else 'infinite'

        data_txt += re.sub(' +', ' ', f"{name} {small_name} for {tickets} tickets, {stock} left.\n")
    return data_txt


def get_shop_data():
    global shop_data
    while True:
        shop_data = _get_data()

        print("Waiting 60sec")
        time.sleep(60)


def get_username(app, user_id: int) -> str:
    try:
        response = app.client.users_info(user=user_id)
    except Exception as e:
        print(f"Error retrieving user info: {e}")
        return "Unknown User"

    if not response["ok"]:
        return "Unknown User"
    if response["user"]["profile"]["display_name"] == "":
        return response["user"]["profile"]["real_name"]
    else:
        return response["user"]["profile"]["display_name"]

# Load shop data in the background every 60sec
thread = threading.Thread(target=get_shop_data, daemon=True)
thread.start()


def get_json(filepath: str): # TODO: I keep messing up the return type hint lol
    with open(filepath) as f:
        result = json.load(f)
    return result