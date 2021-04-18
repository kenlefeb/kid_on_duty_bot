import settings
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import json
from datetime import datetime
import pytz
from icecream import ic

_version = "2.4"
STATE_FILE = "/home/kenlefeb/kid_on_duty_bot/state.json"
PEOPLE_FILE = "/home/kenlefeb/kid_on_duty_bot/people.json"

def reply_text(message, text):
    message.reply_text(text)
    ic(text)

def read_file(name):
    file = open(name)
    text = file.read()
    file.close()
    return text

def write_file(name, text):
    file = open(name, 'w')
    file.write(text)
    file.close()

def get_people():
    text = read_file(PEOPLE_FILE)
    people = json.loads(text)
    ic(people)
    return people

def save_people(people):
    text = json.dumps(people, default=lambda o: o.__dict__, indent=4)
    write_file(PEOPLE_FILE, text)
    ic(text)

def get_person(name):
    people = get_people()
    for this in people:
        ic(this)
        if this['name'].lower() == name.lower():
            return this

    print('not found')    
    return None

def get_first_by_hour(hour):
    is_even = is_it_even(hour)
    people = get_people()
    for this in people:
        ic(this)
        if this['is_even'] == is_even:
            return this

    print('not found')    
    return None

def get_state():
    text = read_file(STATE_FILE)
    state = json.loads(text)
    ic(state)
    return state

def save_state(state):
    ic(state)
    text = json.dumps(state, default=lambda o: o.__dict__, indent=4)
    if len(text) > 0:
        ic(text)
        write_file(STATE_FILE, text)
    else:
        print('text is empty!')

def get_hour():
    utc_now = pytz.utc.localize(datetime.utcnow())
    ic(utc_now)
    now = utc_now.astimezone(pytz.timezone("America/Detroit"))
    ic(now)
    if now.minute >= 45:
        return now.hour + 1
    else:
        return now.hour

def is_it_even(hour):
    return (hour / 2) == int(hour / 2)

def change_shift(update, context):
    before = get_state()
    words = update.message.text.split()
    if len(words) > 1:
        name = words[1]
        on_duty = get_person(name)
        if on_duty == None:
            reply_text(update.message, f'The name {name} was not found')
        else:
            reply_text(update.message, f'{on_duty["name"]} is taking over for {before["name"]}')
            save_state(on_duty)
        return
    else:
        hour = get_hour()
        on_duty = get_first_by_hour(hour)
        if on_duty == None:
            reply_text(update.message, f'A person on duty for the {hour} hour was not found')
        else:
            reply_text(update.message, f'{on_duty["name"]} is taking over for {before["name"]}')
            save_state(on_duty)
        return
    reply_text(update.message, f'{before["name"]} is still on duty')

def who(update, context):
    on_duty = get_state()
    if on_duty == None:
        reply_text(update.message, 'Nobody is on duty right now!')
    else:
        reply_text(update.message, f'{on_duty["name"]} is on duty right now.')

def help(update, context):
    reply_text(update.message, 'Here are the commands you may use:')
    reply_text(update.message, ' /who           - This will tell you who is currently on duty')
    reply_text(update.message, ' /duty          - This will change who is on duty based on the standard even/odd hour rule')
    reply_text(update.message, ' /duty name     - This will change the duty to a specific person')

def error(update, context):
    reply_text(update.message, update.message)
    reply_text(update.message, context)

def text(update, context):
    text_received = update.message.text
    reply_text(update.message, f'did you say "{text_received}" ?')

def version(update, context):
    reply_text(update.message, f'{__file__} v{_version}')


def main():
    print(f'\n\n{__file__} v{_version}')

    settings.load_environment()
    hour = get_hour()
    ic(hour)

    # create the updater, that will automatically create also a dispatcher and a queue to
    # make them dialoge
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # add handlers for start and help commands
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("version", version))
    dispatcher.add_handler(CommandHandler("duty", change_shift))
    dispatcher.add_handler(CommandHandler("who", who))

    # add an handler for normal text (not commands)
    dispatcher.add_handler(MessageHandler(Filters.text, text))

    # add an handler for errors
    dispatcher.add_error_handler(error)

    # start your shiny new bot
    updater.start_polling()

    # run the bot until Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
