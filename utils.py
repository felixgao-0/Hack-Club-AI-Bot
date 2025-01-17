import json
import os
import re
import threading
import time
from typing import Optional

import psycopg2 # Portgresql db driver
import requests

shop_data = None

# Start settings for utils.py
conn_params = {
    "dbname": "",
    "user": "",
    "password": os.environ['DB_PASSWORD'],
    "host": "",
    "port": ""
}
open_ai_url = "https://jamsapi.hackclub.dev/openai/chat/completions"
arcade_shop_url = "https://hackclub.com/api/arcade/shop/"
api_token = os.environ["OPEN_AI_ARCADE"]
# End settings for utils.py

def ask_ai(question: str, *, context: Optional[list] = None) -> dict:
    """
    Ask ChatGPT a Arcade related question!
    """
    global shop_data
    if not shop_data:
        print("No shop data, lets go fetch it!")
        shop_data = _get_data() # Get data if its somehow missing D:
    headers = {'Authorization': f'Bearer {api_token}'}

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
    r = requests.post(open_ai_url, json=req_data, headers=headers)
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
    url = arcade_shop_url
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Request failed with status code {r.status_code}")

    data_txt = "ITEMS: "

    for item in r.json():
        name = item['name']
        small_name = item.get('smallName', '')
        tickets = item['hours']
        stock = item['stock'] if item['stock'] is not None else 'infinite'

        data_txt += re.sub(' +', ' ', f"{name} {small_name} for {tickets} tickets, {stock} left. ")
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

def get_opt_out() -> list[int]:
    # save for later: SELECT COUNT(*) FROM opt_out WHERE user_id = 'insert id here'
    with psycopg2.connect(**conn_params) as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM opt_out;")
        result = [item[0] for item in cur.fetchall()]
        conn.commit()
    return result

def add_opt_out(user_id: str) -> None:
    with psycopg2.connect(**conn_params) as conn, conn.cursor() as cur:
        cur.execute(f"""
        INSERT INTO opt_out (user_id)
        VALUES ('{user_id}');
        """)

        conn.commit()