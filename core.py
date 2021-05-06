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
import pandas

bot = telebot.TeleBot(TOKEN)

def find_vax_pincode(pincode):
    found = []
    try:
        URL = meta.CoWIN_URL.replace('@pincode', pincode)
        ddata = None
        response = requests.get(url=URL, headers={
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
        })
        if response.status_code == 200:
            ddata = response.json()
            for center in ddata['centers']:
                for session in center['sessions']:
                    if session['available_capacity'] > 0 and str(center['pincode']) == pincode:
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
                    # No slots found
                    else:
                        logger.log(logging.INFO,'No slots for pincode ' + pincode)
        # BAD response
        else:
            logger.log(logging.INFO, 'CoWIN API response code: ' + str(response.status_code))
            bot.send_message(chat_id=1799512726, text='CoWIN API response code: ' + str(response.status_code))
            if response.status_code >= 400:
                bot.send_message(chat_id=1799512726, text='Terminating core app on i-06b163809a4e35535')
                exit(0)
    except Exception as er:
        logger.log(logging.WARN, er.__repr__())
    return found

def send_msg(match):
    capacity = match['capacity']
    vaccine = 'vaccines' if len(match['vaccine']) == 0 else match['vaccine'] + ' vaccines'
    center = match['center']
    block = match['block']
    pincode = match['pincode']
    date = match['date']
    age = match['age']
    user = match['user']
    state_n = match['state_name']
    text = f'Hey!\n{capacity} {vaccine} available at {center}.\nLocation: {center}, {block} {pincode} {state_n}.\nDate: {date}.\nAges {age}.\nReserve your spot now! Visit https://selfregistration.cowin.gov.in/'
    status_code = 200
    chat_id = match['user']
    try:
        text = msg['text']
        logger.log(logging.INFO, 'Send message to userID: ' + str(chat_id) + ' text: ' + text)
        bot.send_message(chat_id=chat_id, text=text)

        chat_data = {
            'request_id': match['request_id'],
            'user': user,
            'name' : match['name'],
            'pincode': pincode,
            'age': age, 
            'sent_status': 'new', 
            'alert_time': None
        }
        set_processed(chat_data)
        ask_feedback(chat_data)
    except Exception as er:
        logger.log(logging.INFO, er.__repr__())
        status_code = 400
    return status_code


def match_vax_slots(avail_slots, vax_pincode, pincode):
    slots = pandas.DataFrame(data=avail_slots, columns=['center', 'block', 'pincode', 'capacity', 'vaccine', 'date', 'min_age_limit', 'state_name'])
    vax_req = pandas.DataFrame(data=vax_pincode, columns=['pincode', 'alert_time', 'request_id', 'user', 'name', 'sent_status', 'age'])

    logger.log(logging.INFO, 'Available slots for pincode: ' + pincode + ' -> ' + str(len(slots.index)))
    # logger.log(logging.INFO, '\n' + slots.to_string())
    # print('Vaccination requests for pincode:' + pincode)
    logger.log(logging.INFO, 'Vaccination requests for pincode: ' + pincode  + ' -> ' +  str(len(slots.index)))
    # logger.log(logging.INFO, '\n' + vax_req.to_string())
    slots.loc[slots['min_age_limit'] == 18, 'min_age_limit'] = '18-44'
    slots.loc[slots['min_age_limit'] == 45, 'min_age_limit'] = '45+'
    slots.loc[slots['min_age_limit'] == 18, 'min_age_limit'] = '18-44'
    slots['pincode'] = str(slots['pincode'])
    match = pandas.merge(slots, vax_req, left_on = ['pincode', 'min_age_limit'], right_on = ['pincode', 'age'])
    # logger.log(logging.INFO, '\n' + match.to_string())
    logger.log(logging.INFO, 'Age group match for pincode: ' + pincode + ' -> ' + str(len(match.index)))
    match.apply(send_msg, axis=1)

def ask_feedback(chat_data):
    try:
        set_processed(chat_data)
        q_booking_ok = dialogs['consolation']
        chat_id = chat_data['user']
        bot.send_message(chat_id=chat_id, text=q_booking_ok)
    except Exception as er:
        logger.log(logging.WARN, er.__repr__())

# MAIN
WAIT_MIN = 5 
while True:
    try:
        logger.log(logging.INFO, 'Checking at: '+ datetime.now().isoformat())
        for item in get_all_pincodes():
            slots = find_vax_pincode(item['pincode'])
            vax_req = get_request_pincode(item['pincode'])
            match_vax_slots(slots, vax_req, item['pincode']) 
            time.sleep(2)

        logger.log(logging.INFO, 'Waiting...')
        time.sleep(WAIT_MIN*60)
    except KeyboardInterrupt as er: 
        logger.log(logging.WARN, "Bye!")
        exit(0)

# Test code
# item = {'pincode': '411057'}
# slots = find_vax_pincode(item['pincode'])
# vax_req = get_request_pincode(item['pincode'])
# match_vax_slots(slots, vax_req) 

# Shutdown note
# for item in get_all_pincodes():
#     for req in get_request_pincode(item['pincode']):
#         user = req['user']
#         name = req['name']
#         text = f'Dear {name},\nI am shutting down this notification service as CoWIN is no longer allowing us to query for available slots.\nGood luck to you! Stay safe and wear masks around people even when you get vaccinated.\I will try to work around this but can\'t promise right now. But I promise to delete your information. Until then, bye!\n\n- Abhisek De'
#         print(text)

