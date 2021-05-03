import telebot
from secrets import TOKEN
from talk import dialogs
import time
import logging
import requests
import re
import os
import dynamo
from meta import status

logger = telebot.logger
telebot.logger.setLevel(logging.INFO) 

bot = telebot.TeleBot(TOKEN)

chat_data = {
    'request_id': None,
    'user': None,
    'name' : None,
    'pincode': None,
    'age': None, 
    'sent_status': status.NEW, 
    'alert_time': None
}

def save_request(chat_data):
    try:
        chat_id = chat_data['user']
        db_fail = dialogs['db_fail']
        response = dynamo.add_request(chat_data)
        if response != 200:
            bot.send_message(chat_id, db_fail)
    except Exception as er:
        logging.log(logging.WARN, er.__repr__())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        chat_id = message.chat.id
        logger.log(logging.INFO, 'UserID: ' + str(chat_id))

        intro_text = dialogs['intro_text']
        intro_text = intro_text.replace('@first_name', message.chat.first_name)
        bot.send_message(chat_id, intro_text)

        action_text = dialogs['action_text']
        bot.send_message(chat_id, action_text)

        ask_pincode = dialogs['ask_pincode']
        msg = bot.send_message(chat_id, ask_pincode)

        chat_data['user'] = str(chat_id)
        chat_data['name'] = message.chat.first_name

        bot.register_next_step_handler(msg, get_pincode)
    except requests.exceptions.ReadTimeout as er:
        logging.log(logging.WARN, er.__repr__())
    except Exception as er:
        logging.log(logging.WARN, er.__repr__())

def get_pincode(message):
    try:
        chat_id = message.chat.id
        reg_exp = '^\d{6}$'
        pincode = message.text

        if None == re.match(reg_exp, pincode):
            pin_error = dialogs['pin_error']
            msg = bot.send_message(chat_id, pin_error)
            bot.register_next_step_handler(msg, get_pincode)
        else:
            chat_data['pincode'] = message.text

            ask_age = dialogs['ask_age']
            age_kb = telebot.types.ReplyKeyboardMarkup(row_width=2)
            age18 = telebot.types.KeyboardButton('18-44')
            age45 = telebot.types.KeyboardButton('45+')
            age_kb.add(age18, age45)
            msg = bot.send_message(chat_id=chat_id, text=ask_age, reply_markup=age_kb)
            bot.register_next_step_handler(msg, get_age_limit)
            logger.log(logging.INFO, 'Postal code: ' + pincode)
            
    except requests.exceptions.ReadTimeout as er:
        logging.log(logging.WARN, er.__repr__())
    except Exception as er:
        logging.log(logging.WARN, er.__repr__())

def get_pincode_again(message):
    try:
        chat_id = message.chat.id
        reg_exp = '^\d{6}$'
        pincode = message.text

        if None == re.match(reg_exp, pincode):
            pin_error = dialogs['pin_error']
            msg = bot.send_message(chat_id, pin_error)
            bot.register_next_step_handler(msg, get_pincode)
        else:
            chat_data['pincode'] = message.text
            chat_data['request_id'] = chat_data['user'] + chat_data['pincode']
            logger.log(logging.INFO, str(chat_data))
            save_request(chat_data) # Done

            other_pin = dialogs['other_pin']
            yn_kb = telebot.types.ReplyKeyboardMarkup(row_width=2) 
            y_key = telebot.types.KeyboardButton("Yes")
            n_key = telebot.types.KeyboardButton("No, I am done")
            yn_kb.add(y_key, n_key)
            msg = bot.send_message(chat_id=chat_id, text=other_pin, reply_markup=yn_kb)
            bot.register_next_step_handler(msg, get_other_pin)
            
    except requests.exceptions.ReadTimeout as er:
        logging.log(logging.WARN, er.__repr__())
    except Exception as er:
        logging.log(logging.WARN, er.__repr__())

def get_other_pin(message):
    chat_id = message.chat.id
    logger.log(logging.INFO, 'Flexible for other location: ' + message.text)
    try:
        if message.text == 'Yes': 
            ask_pincode = dialogs['ask_pincode']
            msg = bot.send_message(chat_id=chat_id, text=ask_pincode, reply_markup=telebot.types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, get_pincode_again)
        else:
            bot.send_message(chat_id=chat_id, text="In case you wish to receive more updates later, just send us a Hi/Hello and we will get back to you. Bye!", reply_markup=telebot.types.ReplyKeyboardRemove())
    except Exception as er:
        logging.log(logging.WARN, er.__repr__())

def get_age_limit(message):
    try:
        chat_id = message.chat.id
        age_limit = message.text
        chat_data['age'] = age_limit
        chat_data['request_id'] = chat_data['user'] + chat_data['pincode']

        logger.log(logging.INFO, 'Age group: ' + age_limit)

        msg = bot.send_message(chat_id=chat_id, text=dialogs["setup_ok"], reply_markup=telebot.types.ReplyKeyboardRemove())
        logger.log(logging.INFO, str(chat_data))
        save_request(chat_data) # Done

        other_pin = dialogs['other_pin']
        yn_kb = telebot.types.ReplyKeyboardMarkup(row_width=2) 
        y_key = telebot.types.KeyboardButton("Yes")
        n_key = telebot.types.KeyboardButton("No, I am done")
        yn_kb.add(y_key, n_key)
        msg = bot.send_message(chat_id=chat_id, text=other_pin, reply_markup=yn_kb)
        bot.register_next_step_handler(msg, get_other_pin)

    except requests.exceptions.ReadTimeout as er:
        logging.log(logging.WARN, er.__repr__())
        get_age_limit(message)
    except Exception as er:
        logging.log(logging.WARN, er.__repr__())
        get_age_limit(message)

@bot.message_handler(regexp="hello")
@bot.message_handler(regexp="Hello")
@bot.message_handler(regexp="Hi")
@bot.message_handler(regexp="hi")
@bot.message_handler(regexp="Hey")
@bot.message_handler(regexp="hey")
def reply_hello(message): 
    send_welcome(message)

bot.enable_save_next_step_handlers(delay=0.5)
bot.load_next_step_handlers(os.getcwd() + 'handler-saves\\step.save')
bot.polling()
