import logging
import os

from slack_bolt import App, BoltResponse

from utils import ask_ai, get_json, get_username, is_question

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(levelname)s - %(asctime)s: %(message)s',
    datefmt='%H:%M:%S'  # Date format
)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

authorized = ["U07BU2HS17Z", "U07BLJ1MBEE"]

@app.event("message")
def handle_message_events(event, say, client):
    if event.get("parent_user_id", event["user"]) != event["user"]:
        print("Ignoring: Not the thread author")
        return

    if event.get("subtype"):
        print("Ignoring: Bot message or of subtype we don't care abt")

    if not is_question(event["text"]):
        print("Ignoring: Not likely a question")
        return

    text = event["text"] 

    text_lower = text.lower()
    print(text_lower)
    if not text_lower.startswith("ai"):
        print("User did not opt for AI to respond D:")
        block = get_json("json_data/consent_prompt.json")
        say(
            text="Press the button below to have AI respond if you need help!",
            blocks=block, 
            thread_ts=event["ts"]
        )
        return

    print(event)
    #response = app.client.conversations_replies(channel=event["channel"], ts=event["event_ts"])
    #print(response['messages'][0])
    
    client.reactions_add( # Loading emoji so user knows whats happening
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
    block = get_json("json_data/response_prompt.json")
    block[0]['text']['text'] = response_text["choices"][0]["message"]["content"]
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
def answer_question_events(ack, client, body, say, logger):
    ack()
    if body['user']['id'] != body['message']['parent_user_id']:
        logger.warn("Ignoring btn press, isn't author of the thread")
        return

    thread_ts = body["message"]['thread_ts']
    thread_channel = body['channel']['id']

    edit_block = get_json("json_data/consent_prompt.json")
    edit_block[:-1]['elements'][0]['disabled'] = True
    response = client.chat_update(
        channel=body['channel']['id'],
        ts=body['message']['ts'],
        blocks=edit_block
    )

    context_data: str = ""

    response = client.conversations_replies(channel=thread_channel, ts=thread_ts)

    for index, message in enumerate(response["messages"]):
        if index == 0: # Ignore first one, we'll use it later on
            continue
        context_data += f"{get_username(app, message['user'])} SAID: {message['text']} "

    client.reactions_add( # Loading emoji so user knows whats happening
        channel=thread_channel,
        name="spin-loading",
        timestamp=body['message']['ts']
    )

    response_text = ask_ai(response["messages"][0]['text'], context=context_data)
    
    block = get_json("json_data/response_prompt.json")
    block[0]['text']['text'] = response_text["choices"][0]["message"]["content"]

    say(
        text=response_text["choices"][0]["message"]["content"],
        blocks=block, 
        thread_ts=body['message']['ts']
    )
    client.reactions_remove(
        channel=thread_channel,
        name="spin-loading",
        timestamp=body['message']['ts']
    )


@app.middleware
def middleware_checks(context, next, logger):
    logger.info("Running checks")

    if context["channel_id"] != "C07JA93AMDZ": # Test channel
        logger.warning("Ignoring, Incorrect Channel")
        return BoltResponse(status=401, body="Incorrect channel")

    #if event.get("parent_user_id", event["user"]) != event["user"]:
    #    logger.warning("Ignoring: Not the thread author")
    #    return

    event = context.get('body', {}).get('event', {})
    if event.get('type') == 'message':
        subtype = event.get('subtype')
        if subtype:
            logger.warning("Ignoring, likely bot")
            print(subtype)
            return BoltResponse(status=401, body="Bot response, ignoring")

    if context["user_id"] not in authorized:
        logger.warning("Ignoring, not authorized to use bot")
        return BoltResponse(status=401, body="Unauthorized user")

    #print(context)

    return next()

if __name__ == "__main__":
    app.start(port=3000)