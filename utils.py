import json
import os
import threading
import time
from typing import Optional, Union

import requests

shop_data = None

def ask_ai(question: str, *, context: Optional[str] = None) -> dict:
    """
    Ask ChatGPT a Arcade related question!
    """
    global shop_data
    if not shop_data:
        shop_data = _get_data() # Get data if its somehow missing D:
    #return {'id': 'chatcmpl-9zaUbHwHybVcyQqwMJcjCwu72svn5', 'object': 'chat.completion', 'created': 1724465313, 'model': 'gpt-3.5-turbo-0125', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': 'I am an AI bot developed internally and do not use any specific LLM (Large Language Model). My purpose is to provide helpful information and assist users in understanding how to participate in the Arcade hackathon organized by Hack Club for high schoolers. If you have any questions about the hackathon or need further assistance, feel free to ask!', 'refusal': None}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 1159, 'completion_tokens': 68, 'total_tokens': 1227}, 'system_fingerprint': None} # type: ignore
    url = "https://jamsapi.hackclub.dev/openai/chat/completions"
    headers = {'Authorization': f'Bearer {os.environ["OPEN_AI_ARCADE"]}'}

    prompt = get_json('json_data/messages.json')

    prompt.append({"role": "user", "content": f"USER QUESTION: {question}"})
    prompt.append({"role": "system", "content": shop_data})
    if context:
        prompt.append({"role": "user", "content": context})
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
        name = item['name'].strip()
        tickets = item['hours']
        stock = item['stock'] if item['stock'] else 'infinite'
        data_txt += f"{name} for {tickets} tickets, {stock} left. "
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
    return response["user"]["profile"]["display_name"]

# Load shop data in the background every 60sec
thread = threading.Thread(target=get_shop_data, daemon=True)
thread.start()


def get_json(filepath: str) -> Union[dict, list]:
    with open(filepath) as f:
        result = json.load(f)
    return result