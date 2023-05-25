import os
import re
import redis
from telegram import ChatAction

from auto_bot.handlers.comment.handlers import save_comment
from auto_bot.handlers.driver.handlers import change_status_car
from auto_bot.handlers.driver_manager.handlers import get_gps_imea, get_n_vehicle, get_fleet_for_job_application, \
    get_vin_code_vehicle, get_licence_plate_vehicle, get_model_vehicle, get_name_vehicle, add_information_to_driver, \
    get_fleet, viewing_status_driver, second_name, email, phone_number, create_user, get_list_vehicle
from auto_bot.handlers.order.handlers import to_the_address, payment_method, order_on_time
from auto_bot.handlers.owner.handlers import get_sum, generate_link_v1, get_sum_for_portmone, transfer, generate_link_v2
from auto_bot.handlers.service_manager.handlers import send_report_to_db_and_driver, end_of_repair, start_of_repair, \
    photo
from auto_bot.handlers.status.handlers import correct_choice

from auto_bot.handlers.driver_manager.static_text import *
from auto_bot.handlers.owner.static_text import CARD, SUM, PORTMONE_SUM, PORTMONE_COMMISSION, GENERATE_LINK_PORTMONE
from auto_bot.handlers.service_manager.static_text import LICENCE_PLATE, PHOTO, START_OF_REPAIR, END_OF_REPAIR
from auto_bot.handlers.driver.static_text import V_ID, NUMBERPLATE
from auto_bot.handlers.order.static_text import FROM_ADDRESS, TO_THE_ADDRESS, TIME_ORDER, COMMENT


def text(update, context):
    if context.user_data.get('state'):
        if context.user_data['state'] == FROM_ADDRESS:
            return to_the_address(update, context)
        elif context.user_data['state'] == TO_THE_ADDRESS:
            return payment_method(update, context)
        elif context.user_data['state'] == COMMENT:
            return save_comment(update, context)
        elif context.user_data['state'] == TIME_ORDER:
            return order_on_time(update, context)
    elif context.user_data.get('driver_state') is not None:
        if context.user_data['driver_state'] == NUMBERPLATE:
            return change_status_car(update, context)
        elif context.user_data['driver_state'] == V_ID:
            return correct_choice(update, context)
    elif context.user_data.get('owner_state') is not None:
        if context.user_data['owner_state'] == CARD:
            return get_sum(update, context)
        elif context.user_data['owner_state'] == SUM:
            return transfer(update, context)
        elif context.user_data['owner_state'] == PORTMONE_SUM:
            return generate_link_v1(update, context)
        elif context.user_data['owner_state'] == PORTMONE_COMMISSION:
            return get_sum_for_portmone(update, context)
        elif context.user_data['owner_state'] == GENERATE_LINK_PORTMONE:
            return generate_link_v2(update, context)
    elif context.user_data.get('manager_state') is not None:
        if context.user_data['manager_state'] == STATUS:
            return viewing_status_driver(update, context)
        elif context.user_data['manager_state'] == NAME:
            return second_name(update, context)
        elif context.user_data['manager_state'] == SECOND_NAME:
            return email(update, context)
        elif context.user_data['manager_state'] == EMAIL:
            return phone_number(update, context)
        elif context.user_data['manager_state'] == PHONE_NUMBER:
            return create_user(update, context)
        elif context.user_data['manager_state'] == DRIVER:
            return get_list_vehicle(update, context)
        elif context.user_data['manager_state'] == CAR_NUMBERPLATE:
            return get_fleet(update, context)
        elif context.user_data['manager_state'] == RATE:
            return add_information_to_driver(update, context)
        elif context.user_data['manager_state'] == NAME_VEHICLE:
            return get_name_vehicle(update, context)
        elif context.user_data['manager_state'] == MODEL_VEHICLE:
            return get_model_vehicle(update, context)
        elif context.user_data['manager_state'] == LICENCE_PLATE_VEHICLE:
            return get_licence_plate_vehicle(update, context)
        elif context.user_data['manager_state'] == VIN_CODE_VEHICLE:
            return get_vin_code_vehicle(update, context)
        elif context.user_data['manager_state'] == JOB_APPLICATION:
            return get_fleet_for_job_application(update, context)
        elif context.user_data['manager_state'] == V_GPS:
            return get_n_vehicle(update, context)
        elif context.user_data['manager_state'] == V_GPS_IMEI:
            return get_gps_imea(update, context)
    elif context.user_data.get('state_ssm') is not None:
        if context.user_data['state_ssm'] == LICENCE_PLATE:
            return photo(update, context)
        elif context.user_data['state_ssm'] == PHOTO:
            return start_of_repair(update, context)
        elif context.user_data['state_ssm'] == START_OF_REPAIR:
            return end_of_repair(update, context)
        elif context.user_data['state_ssm'] == END_OF_REPAIR:
            return send_report_to_db_and_driver(update, context)
    else:
        return code(update, context)


def code(update, context):
    pattern = r'^\d{4}$'
    m = update.message.text
    if re.match(pattern, m) is not None:
        r = redis.Redis.from_url(os.environ["REDIS_URL"])
        r.publish('code', update.message.text)
        update.message.reply_text('Формування звіту...')
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
    else:
        update.message.reply_text('Боту не вдалось опрацювати ваше повідомлення.')