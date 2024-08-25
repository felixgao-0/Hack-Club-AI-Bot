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

authorized = ["U07BU2HS17Z", "U07BLJ1MBEE", "U079VBNLTPD", "U05F4B48GBF"]
opt_out_list = [""]

def get_context(messages_list: list) -> list:
    """
    Generates a context string for the AI to use. 
    This allows the bot to add on to existing responses and help further.
    """
    reply_context = []
    for message in messages_list:
        reply_user = get_username(app, message['user'])
        if reply_user == "Bartosz AI Competitor":
            reply_context.append(
                {"role": "system", "content": f"You replied with '{message['text']}'"}
            )
            reply_user = "You" # Don't confuse the AI with itself haha
        elif message['user'] not in opt_out_list:
            reply_context.append(
                {"role": "user", "content": f"{reply_user} said '{message['text']}'"}
            )
    return reply_context


@app.event("message")
def handle_message_events(event, say, client, logger):
    if event.get("parent_user_id", event["user"]) != event["user"]:
        logger.warning("Ignoring, not the thread author")
        return

    if not is_question(event["text"]):
        logger.warning("Ignoring, not likely a question")
        return

    if event.get("subtype"):
        logger.warning("Ignoring: We don't need to respond to subtypes lol")
        print(event)
        return

    text = event["text"]
    text_lower = text.lower()

    if not text_lower.startswith("ai"): # or (event.get("parent_user_id") and ()):
        logger.warning("User did not opt for AI to responding")
        block = get_json("json_data/consent_prompt.json")
        if not event.get("parent_user_id"):
            logger.info("Sending consent prompt")
            say(
              text="Press the button below to have AI respond if you need help!",
              blocks=block, 
              thread_ts=event["ts"]
            )
        return

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

    if event.get("thread_ts"): # If we're in a thread
        logger.info("Question received, responding as thread w/ context")
        response = client.conversations_replies(channel=event["channel"], ts=event["thread_ts"])
        consented_text_block = get_json('json_data/prompt_consented.json')[0]['text']['text']
        print(consented_text_block) # TODO: Remove debug thingy lata
        print(response['messages'][1]['text'])
        if response['messages'][0]['text'].lower().startswith("ai") or response['messages'][1]['text'].startswith(consented_text_block): # WIP
            response_text = ask_ai(text, context=get_context(response['messages']))
            block = get_json("json_data/response_prompt.json")
            block[0]['text']['text'] = response_text["choices"][0]["message"]["content"]

            say(
                text=response_text["choices"][0]["message"]["content"],
                blocks=block, 
                thread_ts=event["ts"]
            )
    else:
        logger.info("Question received, responding as a new question")
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

@app.event("app_mention")
def handle_app_mention_events(event, say, logger):
    logger.info("We got mentioned!")
    say(
        text="Hi! I'm a bot which helps people with their Arcade questions! Made by Felíx. #ai-bartosz for more info!", # type: ignore
        thread_ts=event["ts"]
    )


@app.action("answer_question") # Consent btn
def answer_question_events(ack, client, body, say, logger):
    ack()
    if body['user']['id'] != body['message']['parent_user_id']:
        logger.warn("Ignoring btn press, isn't author of the thread")
        return

    thread_ts = body["message"]['thread_ts']
    thread_channel = body['channel']['id']

    edit_block = get_json("json_data/prompt_consented.json")
    response = client.chat_update(
        channel=body['channel']['id'],
        ts=body['message']['ts'],
        blocks=edit_block
    )

    response = client.conversations_replies(channel=thread_channel, ts=thread_ts)
    context_data = get_context(response['messages'])

    client.reactions_add(
        channel=thread_channel,
        name="bartosz",
        timestamp=thread_ts
    )
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

    if context["user_id"] in opt_out_list: # Noo they don't want the ai D:
        logger.warning("Ignoring, data opt out")
        return BoltResponse(status=401, body="Opt out")

    logger.info("Checks passed, moving to function :D")
    return next()

if __name__ == "__main__":
    app.start(port=3000)