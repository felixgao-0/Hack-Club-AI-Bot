import logging
import os

from slack_bolt import App, BoltResponse

from utils import ask_ai, get_json, get_username, is_question, get_opt_out, add_opt_out

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(levelname)s - %(asctime)s: %(message)s',
    datefmt='%H:%M:%S'  # Date format
)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Change this to an animated emoji of a loading wheel!
loading_emoji_name = "loading"

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
        elif message['user'] not in get_opt_out():
            reply_context.append(
                {"role": "user", "content": f"{reply_user} said '{message['text']}'"}
            )
        else:
            logger.warn(f"{message['user']} in opt-out list D:")
    return reply_context


@app.event("message")
def handle_message_events(event, say, client, logger):
    try:
        if event.get("parent_user_id", event["user"]) != event["user"]:
            logger.warning("Ignoring, not the thread author")
            return
    except KeyError:
        logger.error("Woah there we got an issue")
        raise KeyError(event) from None

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
        name=loading_emoji_name,
        timestamp=event["event_ts"]
    )

    if event.get("thread_ts"):
        response = client.conversations_replies(channel=event["channel"], ts=event["thread_ts"])
        consented_text_block = get_json('json_data/prompt_consented.json')[0]['text']['text']
        messages = response['messages']
        if not messages[0]['text'].lower().startswith("ai") and not messages[1]['text'].startswith(consented_text_block):
            # if in thread, and no top-level message consent D:
            logger.warn("Ignoring, no thread consent was received ( noo D: )")
            return

    if event.get("thread_ts"): # Get context data if thread
        response = client.conversations_replies(channel=event["channel"], ts=event["thread_ts"])
        thread_context = get_context(response['messages'])
    else: # Not in thread, no context to get so womp womp
        thread_context = None

    response_text = ask_ai(text, context=thread_context)
    block = get_json("json_data/response_prompt.json")
    block[0]['text']['text'] = response_text["choices"][0]["message"]["content"]

    say(
        text=response_text["choices"][0]["message"]["content"],
        blocks=block, 
        thread_ts=event["ts"]
    )

    client.reactions_remove(
        channel=event["channel"],
        name=loading_emoji_name,
        timestamp=event["event_ts"]
    )

@app.event("app_mention")
def handle_app_mention_events(event, say, logger):
    logger.info("We got mentioned!")
    say(
        text="Hi! I'm a bot which helps people with their Arcade questions!", # type: ignore
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

    client.reactions_add( # Loading emoji so user knows whats happening
        channel=thread_channel,
        name=loading_emoji_name,
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
        name=loading_emoji_name,
        timestamp=body['message']['ts']
    )


@app.command("/opt-out")
def opt_out_command(ack, respond, body):
    ack()
    try:
        add_opt_out(body['user_id'])
    except:
        respond(f"Something went wrong!")
    else:
        respond("You have been added to the opt-out list.")


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

    if context["user_id"] in get_opt_out(): # Noo they don't want the ai D:
        logger.warning("Ignoring, data opt out")
        return BoltResponse(status=401, body="Opt out")

    logger.info("Checks passed, moving to function :D")
    return next()

if __name__ == "__main__":
    app.start(port=3000)