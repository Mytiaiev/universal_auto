import datetime
import threading
import time
from django.core.exceptions import ObjectDoesNotExist
from telegram.ext import ConversationHandler
from app.models import JobApplication, Client
from auto_bot.handlers.driver_job.keyboards import inline_ask_auto_kb, inline_job_name_kb, inline_ask_docs_kb
from auto_bot.handlers.driver_job.static_text import *
from auto_bot.handlers.driver_job.utils import save_storage_photo, validate_date
from scripts.redis_conn import redis_instance


def job_application(update, context):
    query = update.callback_query
    query.edit_message_text(text=choose_job)
    query.edit_message_reply_markup(reply_markup=inline_job_name_kb())


def restart_job_application(update, context):
    update.message.reply_text(start_again_text)
    update.message.reply_text(ask_name_text)
    return "JOB_USER_NAME"


# Update information for users
def update_name(update, context):
    query = update.callback_query
    user = Client.get_by_chat_id(update.effective_chat.id)
    redis_instance().hset(str(update.effective_chat.id), 'role', driver_job_name)
    if user:
        try:
            JobApplication.objects.get(phone_number=user.phone_number)
            query.edit_message_text(already_send_text)
        except ObjectDoesNotExist:
            query.edit_message_text(ask_name_text)
            return "JOB_USER_NAME"
    else:
        query.edit_message_text(no_phone_text)


def update_second_name(update, context):
    name = update.message.text
    clear_name = Client.name_and_second_name_validator(name=name)
    context.bot.send_message(chat_id=update.effective_chat.id, text=make_mistake_text)
    if clear_name is not None:
        redis_instance().hset(str(update.effective_chat.id), 'u_name', clear_name)
        update.message.reply_text(ask_lastname_text)
        return "JOB_LAST_NAME"
    else:
        update.message.reply_text(no_valid_name_text)
        return "JOB_USER_NAME"


def update_email(update, context):
    second_name = update.message.text
    clear_second_name = Client.name_and_second_name_validator(name=second_name)
    if clear_second_name is not None:
        redis_instance().hset(str(update.effective_chat.id), 'u_second_name', clear_second_name)
        update.message.reply_text(ask_email_text)
        return "JOB_EMAIL"
    else:
        update.message.reply_text()
        return "JOB_LAST_NAME"


def update_user_information(update, context):
    email = update.message.text
    chat_id = update.message.chat.id
    user = Client.get_by_chat_id(chat_id)
    clear_email = Client.email_validator(email=email)
    if clear_email is not None:
        user_data = redis_instance().hgetall(str(update.effective_chat.id))
        user.name = user_data['u_name']
        user.second_name = user_data['u_second_name']
        user.email = clear_email
        user.save()
        update.message.reply_text(updated_text, reply_markup=inline_ask_docs_kb())
        redis_instance().hset(str(update.effective_chat.id), 'phone', user.phone_number)
        return "WAIT_FOR_JOB_OPTION"
    else:
        update.message.reply_text(no_valid_email_text)
        return 'JOB_EMAIL'


def get_job_photo(update, context):
    update.callback_query.edit_message_text(text=ask_photo_text)
    return 'WAIT_FOR_JOB_PHOTO'


def upload_photo(update, context):
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'job/photo/{image["file_unique_id"]}.jpg'
        redis_instance().hset(str(update.effective_chat.id), 'photo_job', filename)
        save_storage_photo(image, filename)
        update.message.reply_text(saved_photo_text)
        context.bot.send_photo(update.effective_chat.id,
                               'https://kourier.in.ua/uploads/posts/2016-12/1480604684_1702.jpg')
        return 'WAIT_FOR_FRONT_PHOTO'
    else:
        update.message.reply_text(no_photo_text)
        return 'WAIT_FOR_JOB_PHOTO'


def upload_license_front_photo(update, context):
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'job/licenses/front/{image["file_unique_id"]}.jpg'
        redis_instance().hset(str(update.effective_chat.id), 'front_license', filename)
        save_storage_photo(image, filename)
        update.message.reply_text(front_licence_saved)
        context.bot.send_photo(update.effective_chat.id,
                               'https://www.autoconsulting.com.ua/pictures/_upload/1582561870fbTo_h.jpg')
        return 'WAIT_FOR_BACK_PHOTO'
    else:
        update.message.reply_text(ask_front_licence)
        return 'WAIT_FOR_FRONT_PHOTO'


def upload_license_back_photo(update, context):
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'job/licenses/back/{image["file_unique_id"]}.jpg'
        redis_instance().hset(str(update.effective_chat.id), 'back_license', filename)
        save_storage_photo(image, filename)
        update.message.reply_text(back_licence_saved)
        update.message.reply_text(no_date_licence)
        return 'WAIT_FOR_EXPIRED'
    else:
        update.message.reply_text(ask_back_licence)
        return 'WAIT_FOR_BACK_PHOTO'


def upload_expired_date(update, context):
    date = update.message.text
    if validate_date(date):
        redis_instance().hset(str(update.effective_chat.id), 'expired_license', date)
        update.message.reply_text(ask_auto_text, reply_markup=inline_ask_auto_kb())
        return "WAIT_ANSWER"
    else:
        update.message.reply_text(f'{date} {no_valid_date_text}')
        return 'WAIT_FOR_EXPIRED'


def check_auto(update, context):
    query = update.callback_query
    query.edit_message_text(ask_autodoc_text)
    context.bot.send_photo(query.message.chat_id,
                           'https://protocol.ua/userfiles/tehpasport-na-avto.jpg')
    return 'WAIT_FOR_AUTO_YES_OPTION'


def upload_auto_doc(update, context):
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'job/car/{image["file_unique_id"]}.jpg'
        redis_instance().hset(str(update.effective_chat.id), 'auto_doc', filename)
        save_storage_photo(image, filename)
        update.message.reply_text(make_mistake_text)
        update.message.reply_text(autodoc_saved_text)
        context.bot.send_photo(update.effective_chat.id,
                               'https://rinokstrahovka.ua/img/content/2019/07/paper_client_green1.jpg')
        return 'WAIT_FOR_INSURANCE'
    else:
        update.message.reply_text(no_autodoc_text)
        return 'WAIT_FOR_AUTO_YES_OPTION'


def upload_insurance(update, context):
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'job/insurance/{image["file_unique_id"]}.jpg'
        redis_instance().hset(str(update.effective_chat.id), 'insurance', filename)
        save_storage_photo(image, filename)
        update.message.reply_text(insurance_saved_text)
        return 'WAIT_FOR_INSURANCE_EXPIRED'
    else:
        update.message.reply_text(ask_insurance_photo)
        return 'WAIT_FOR_INSURANCE'


def upload_expired_insurance(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    user = Client.get_by_chat_id(chat_id)
    user_data = redis_instance().hgetall(str(chat_id))
    job = {"first_name": user.name,
           "last_name": user.second_name,
           "email": user.email,
           "phone_number": user.phone_number,
           "chat_id": chat_id,
           "license_expired": datetime.datetime.strptime(user_data['expired_license'], '%d.%m.%Y').date(),
           "driver_license_front": user_data['front_license'],
           "driver_license_back": user_data['back_license'],
           "photo": user_data['photo_job'],
           "role": user_data['role'],
           }
    if query and query.data == 'no_auto':
        query.edit_message_text(text=sms_text(user.phone_number))
        JobApplication.objects.create(**job)
    else:
        date = update.message.text
        if validate_date(date):
            job.update(insurance_expired=datetime.datetime.strptime(date, '%d.%m.%Y').date(),
                       car_documents=user_data['auto_doc'],
                       insurance=user_data['insurance'])
            JobApplication.objects.create(**job)
            update.message.reply_text(text=sms_text(user.phone_number))
        else:
            update.message.reply_text(f'{date} {no_valid_insurance}')
            return 'WAIT_FOR_EXPIRED'
    redis_instance().hset(str(chat_id), "thread", 1)
    t = threading.Thread(target=code_timer, args=(update, context, 180, 30), daemon=True)
    t.start()
    return "JOB_UKLON_CODE"


def uklon_code(update, context):
    chat_id = update.message.chat.id
    user = Client.get_by_chat_id(chat_id)
    redis_instance().delete(str(chat_id))
    redis_instance().publish(f'{user.phone_number} code', update.message.text)
    update.message.reply_text(accept_code_text)
    return ConversationHandler.END


def code_timer(update, context, timer, sleep):
    def timer_callback(context):
        context.bot.send_message(update.effective_chat.id,
                                 f'Заявку відхилено.Ви завжди можете подати її повторно')
        phone = redis_instance().hget(str(update.effective_chat.id), "phone")
        JobApplication.objects.filter(phone_number=phone).first().delete()
        return ConversationHandler.END

    remaining_time = timer
    while remaining_time > 0:
        try:
            if redis_instance().hget(str(update.effective_chat.id), "thread"):
                if remaining_time < sleep + 1:
                    context.bot.send_message(update.effective_chat.id,
                                             f'Залишилось {int(remaining_time)} секунд.'
                                             f'Якщо ви не відправите код заявку буде скасовано')
                    time.sleep(remaining_time)
                    remaining_time = 0
                    timer_callback(context)
                else:
                    context.bot.send_message(update.effective_chat.id,
                                             f'Коду лишилось діяти {int(remaining_time)} секунд.Поспішіть будь-ласка')
                    time.sleep(sleep)
                    remaining_time = int(remaining_time - sleep)
            else:
                break
        except KeyError:
            break
