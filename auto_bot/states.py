import os
import re
import redis
from telegram import ChatAction

from auto_bot.handlers.comment.handlers import save_comment
from auto_bot.handlers.order.handlers import to_the_address, payment_method, first_address_check, second_address_check, \
    order_on_time
from auto_bot.handlers.order.static_text import FROM_ADDRESS, TO_THE_ADDRESS, FIRST_ADDRESS_CHECK, SECOND_ADDRESS_CHECK, \
    TIME_ORDER, COMMENT


def text(update, context):
    """ STATE - for all users, STATE_D - for drivers, STATE_O - for owner,
            STATE_DM - for driver manager, STATE_SSM - for service station manager"""
    global STATE_O
    global STATE_D
    global STATE_DM
    global STATE_SSM

    if context.user_data['state']:
        if context.user_data['state'] == FROM_ADDRESS:
            return to_the_address(update, context)
        elif context.user_data['state'] == TO_THE_ADDRESS:
            return payment_method(update, context)
        elif context.user_data['state'] == COMMENT:
            return save_comment(update, context)
        elif context.user_data['state'] == FIRST_ADDRESS_CHECK:
            return first_address_check(update, context)
        elif context.user_data['state'] == SECOND_ADDRESS_CHECK:
            return second_address_check(update, context)
        elif context.user_data['state'] == TIME_ORDER:
            return order_on_time(update, context)
    # elif STATE_D is not None:
    #     if STATE_D == NUMBERPLATE:
    #         return change_status_car(update, context)
    #     elif STATE_D == V_ID:
    #         return correct_choice(update, context)
    #     elif STATE_D == V_CAR:
    #         return add_vehicle_to_driver(update, context)
    # elif STATE_O is not None:
    #     if STATE_O == CARD:
    #         return get_sum(update, context)
    #     elif STATE_O == SUM:
    #         return transfer(update, context)
    #     elif STATE_O == PORTMONE_SUM:
    #         return generate_link_v1(update, context)
    #     elif STATE_O == PORTMONE_COMMISSION:
    #         return get_sum_for_portmone(update, context)
    #     elif STATE_O == GENERATE_LINK:
    #         return generate_link_v2(update, context)
    # elif STATE_DM is not None:
    #     if STATE_DM == STATUS:
    #         return viewing_status_driver(update, context)
    #     elif STATE_DM == NAME:
    #         return second_name(update, context)
    #     elif STATE_DM == SECOND_NAME:
    #         return email(update, context)
    #     elif STATE_DM == EMAIL:
    #         return phone_number(update, context)
    #     elif STATE_DM == PHONE_NUMBER:
    #         return create_user(update, context)
    #     elif STATE_DM == DRIVER:
    #         return get_list_vehicle(update, context)
    #     elif STATE_DM == CAR_NUMBERPLATE:
    #         return get_fleet(update, context)
    #     elif STATE_DM == RATE:
    #         return add_information_to_driver(update, context)
    #     elif STATE_DM == NAME_VEHICLE:
    #         return get_name_vehicle(update, context)
    #     elif STATE_DM == MODEL_VEHICLE:
    #         return get_model_vehicle(update, context)
    #     elif STATE_DM == LICENCE_PLATE_VEHICLE:
    #         return get_licence_plate_vehicle(update, context)
    #     elif STATE_DM == VIN_CODE_VEHICLE:
    #         return get_vin_code_vehicle(update, context)
    #     elif STATE_DM == JOB_APPLICATION:
    #         return get_fleet_for_job_application(update, context)
    #     elif STATE_DM == V_GPS:
    #         return get_n_vehicle(update, context)
    #     elif STATE_DM == V_GPS_IMEI:
    #         return get_gps_imea(update, context)
    # elif STATE_SSM is not None:
    #     if STATE_SSM == LICENCE_PLATE:
    #         return photo(update, context)
    #     elif STATE_SSM == PHOTO:
    #         return start_of_repair(update, context)
    #     elif STATE_SSM == START_OF_REPAIR:
    #         return end_of_repair(update, context)
    #     elif STATE_SSM == END_OF_REPAIR:
    #         return send_report_to_db_and_driver(update, context)
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
        update.message.reply_text('Боту не вдалось опрацювати ваше повідомлення. Спробуйте пізніше')