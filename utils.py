import json
import os

import requests
import spacy

nlp = spacy.load("en_core_web_sm")


def ask_ai(question: str) -> dict:
    shop_data = get_shop_data()
    url = "https://jamsapi.hackclub.dev/openai/chat/completions"
    headers = {'Authorization': f'Bearer {os.environ["OPEN_AI_ARCADE"]}'}
    with open('messages.json') as f:
        prompt = json.load(f)
    prompt.append({"role": "user", "content": question})
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

    This function was modified with code from ChatGPT.
    """
    doc = nlp(text)

    if text.strip().endswith('?'):
        return True

    return any(token.dep_ == "attr" and token.head.pos_ == "AUX" for token in doc)


def get_shop_data():
    url = "https://hackclub.com/api/arcade/shop/"
    r = requests.get(url)
    r.raise_for_status()

    data_txt = "ITEMS: "

    for item in r.json():
        name = item['name'].strip()
        tickets = item['hours']
        stock = item['stock'] if item['stock'] else 'infinite'
        data_txt += f"{name} for {tickets} tickets, {stock} left. "
    return data_txt