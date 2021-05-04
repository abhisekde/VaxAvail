import json
import requests
from datetime import datetime
import time
import boto3
from dynamo import get_all_pincodes
from dynamo import get_request_pincode 
from dynamo import set_processed 
from secrets import TOKEN
from talk import dialogs
import logging
import threading
import meta
import telebot
logger = telebot.logger
telebot.logger.setLevel(logging.INFO) 

bot = telebot.TeleBot(TOKEN)

def find_vax_pincode(pincode):
    found = []
    try:
        URL = meta.CoWIN_URL.replace('@pincode', pincode)
        # d = datetime.now()
        ddata = None
        response = requests.get(URL)
        if response.status_code == 200:
            ddata = response.json()
            for center in ddata['centers']:
                for session in center['sessions']:
                    if session['available_capacity'] > 0 and str(center['pincode']) == pincode:
                        # logger.log(logging.INFO, center['name'], 'at', center['block_name'], center['pincode'], 'has', session['available_capacity'], session['vaccine'], 'vaccine on', session['date'])
                        found.append({
                            'center': center['name'], 
                            'block': center['block_name'],
                            'pincode': center['pincode'], 
                            'capacity': session['available_capacity'], 
                            'vaccine': session['vaccine'], 
                            'date': session['date'], 
                            'min_age_limit': session['min_age_limit'],
                            'state_name': center['state_name']
                        })
                    else:
                        # logger.log(logging.INFO, 'Center search mismatch.', 'Asked pincode', pincode, 'Found:', center['pincode'], 'having', session['available_capacity'], 'doses.')
                        pass
    except Exception as er:
        logger.log(logging.WARN, er.__repr__())
    
    return found

def parse_output(avail_slots):
    msg_queue = []
    n_count = 0
    pincode = avail_slots[0]['pincode']
    for slot in avail_slots:
        # logger.log(logging.INFO, 'Available', slot)
        pincode = slot['pincode']
        n_count = 0
        requests_pincode = get_request_pincode(str(pincode))
        if requests_pincode is None:
            return msg_queue
        for req in requests_pincode:
            available_capacity = str(slot['capacity'])
            if (slot['min_age_limit'] == 18 and req['age'] == '18-44') or (slot['min_age_limit'] == 45 and req['age'] == '45+'):
                n_count = n_count +1
                capacity = slot['capacity']
                vaccine = 'vaccines' if len(slot['vaccine']) == 0 else slot['vaccine'] + ' vaccines'
                center = slot['center']
                block = slot['block']
                pincode = slot['pincode']
                date = slot['date']
                age = req['age']
                user = req['user']
                state_n = slot['state_name']
                text = f'Hey!\n{capacity} {vaccine} available at {center}.\nLocation: {center}, {block} {pincode} {state_n}.\nDate: {date}.\nAges {age}.\nReserve your spot now! Visit https://selfregistration.cowin.gov.in/'
                # logger.log(logging.INFO, text)
                # msg_queue.append({'user': user, 'text' : text})
                logger.log(logging.INFO, text)
                send_msg({'user': user, 'text' : text})
                request_id = req['request_id']
                set_processed(req)
                ask_feedback(req)
            else:
                
                pass
                # logger.log(logging.INFO, 'Asked age:', req['age'], '; Available age:', age)
    logger.log(logging.INFO, 'Success hit for ' + str(pincode) + ': ' + str(n_count))
    return msg_queue

def send_msg(msg):
    status_code = 200
    try:
        chat_id = msg['user']
        text = msg['text']
        logger.log(logging.INFO, 'Send message to userID: ' + str(chat_id) + ' text: ' + text)
        bot.send_message(chat_id=chat_id, text=text)
    except Exception as er:
        logger.log(logging.INFO, er.__repr__())
        status_code = 400
    return status_code
    # return response.status_code


def run(pincode):
    reqs = find_vax_pincode(pincode)
    if len(reqs) == 0:
        return
    logger.log(logging.INFO, 'Tentitive hit for '+ str(pincode) + ': ' + str(len(reqs)))
    msg_queue = parse_output(reqs) 
    for msg in msg_queue:
        send_msg(msg)

def get_feedback(message):
    try:
        a_ok = dialogs['a_booking_ok']
        a_nok = dialogs['a_booking_nok']
        res = message.text 
        chat_id = message.chat.id
        if res == 'Yes':
            bot.send_message(chat_id=chat_id, text=a_ok, reply_markup=yn_kb)
        else:
            bot.send_message(chat_id=chat_id, text=a_nok, reply_markup=yn_kb)
            set_processed(message.chat)
    except Exception as er:
        logger.log(logging.WARN, er.__repr__())


def ask_feedback(chat_data):
    q_booking_ok = dialogs['q_booking_ok']
    yn_kb = telebot.types.ReplyKeyboardMarkup(row_width=2) 
    y_key = telebot.types.KeyboardButton("Yes")
    n_key = telebot.types.KeyboardButton("No")
    yn_kb.add(y_key, n_key)
    chat_id = chat_data['user']
    msg = bot.send_message(chat_id=chat_id, text=q_booking_ok, reply_markup=yn_kb)
    bot.register_next_step_handler(msg, get_feedback)

# MAIN
WAIT_MIN = 0.25
while True:
    try:
        logger.log(logging.INFO, 'Checking at: '+ datetime.now().isoformat())
        threads = []
        for item in get_all_pincodes():
            t = threading.Thread(target=run, args=(item['pincode'],))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()
        logger.log(logging.INFO, 'Wait...')
        time.sleep(WAIT_MIN*60)
    except KeyboardInterrupt as er: 
        logger.log(logging.WARN, "Bye!")
        exit(0)
