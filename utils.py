import json
import os

import requests
import spacy

nlp = spacy.load("en_core_web_sm")


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
    #print(r.json())
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