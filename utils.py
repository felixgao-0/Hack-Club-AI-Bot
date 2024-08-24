import json
import os
import threading
import time

import requests


def ask_ai(question: str) -> dict:
    """
    Ask ChatGPT a Arcade related question!
    """
    if not shop_data:
        ... # Make a request incase the data doesn't exist somehow
    url = "https://jamsapi.hackclub.dev/openai/chat/completions"
    headers = {'Authorization': f'Bearer {os.environ["OPEN_AI_ARCADE"]}'}

    with open('messages.json') as f:
        prompt = json.load(f)

    prompt.append({"role": "user", "content": f"USER QUESTION: {question}"})
    prompt.append({"role": "system", "content": shop_data})
    req_data = {
        'model': 'gpt-3.5-turbo',
        'messages': prompt,
    }
    r = requests.post(url, json=req_data, headers=headers)
    print(shop_data)
    return r.json()


def is_question(text: str) -> bool:
    """
    Detect questions.
    """
    # List of key words that indicate a question
    question_words = ["who", "what", "where", "when", "why", "how", "does", "is", "did"]
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


# Load shop data in the background every 60sec
thread = threading.Thread(target=get_shop_data, daemon=True)
thread.start()