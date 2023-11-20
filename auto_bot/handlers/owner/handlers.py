from telegram import ReplyKeyboardRemove

from app.models import Partner
from app.portmone.portmone import Portmone
from auto_bot.handlers.main.keyboards import markup_keyboard_onetime
from auto_bot.handlers.owner.keyboards import payments_buttons, data_buttons, commission_buttons
from auto_bot.handlers.owner.static_text import *
from scripts.driversrating import DriversRatingMixin
from selenium_ninja.privat import Privat24


# Transfer money
def payments(update, context):
    chat_id = update.message.chat.id
    owner = Partner.get_by_chat_id(chat_id)
    if owner:
        context.bot.send_message(chat_id=chat_id, text='Оберіть опцію:',
                                 reply_markup=markup_keyboard_onetime([payments_buttons]))
    else:
        update.message.reply_text('Ця команда тільки для власника')


def get_card(update, context):

    update.message.reply_text('Введіть номер картки отримувача', reply_markup=ReplyKeyboardRemove())
    context.user_data['owner_state'] = CARD


def get_sum(update, context):
    card = update.message.text
    card = Privat24.card_validator(card=card)
    if card is not None:
        context.user_data['card'] = card
        update.message.reply_text('Введіть суму в форматі DD.CC')
        context.user_data['owner_state'] = SUM
    else:
        update.message.reply_text('Введена карта невалідна')


def transfer(update, context):
    global p
    context.user_data['sum'] = update.message.text

    p = Privat24(card=context.user_data['card'], sum=context.user_data['sum'], driver=True, sleep=7, headless=True)
    p.login()
    p.password()
    p.money_transfer()

    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('privat_3.png', 'rb'))
    context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть опцію:',
                             reply_markup=markup_keyboard_onetime([data_buttons]))
    context.user_data['owner_state'] = None


def correct_transfer(update, context):
    p.transfer_confirmation()
    update.message.reply_text("Транзакція пройшла успішно")


def wrong_transfer(update, context):
    update.message.reply_text("Транзакція відмінена")
    p.quit()


# Generate link debt


def commission(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Виберіть, яку комісію бажаєте встановити:',
                             reply_markup=markup_keyboard_onetime([commission_buttons]))


def get_my_commission(update, context):
    update.message.reply_text(
        "Введіть суму комісії в форматі DD.CC (ваша комісія з комісієй сервісу Portmone буде вирахувана від загальної суми)")
    context.user_data['owner_state'] = PORTMONE_COMMISSION


def get_sum_for_portmone(update, context):
    if context.user_data['owner_state'] == PORTMONE_COMMISSION:
        commission = update.message.text
        commission = conversion_to_float(sum=commission)
        if commission is not None:
            context.user_data['commission'] = commission
            update.message.reply_text(f'Введіть суму на яку ви хочете виставити запит, в форматі DD.CC')
            context.user_data['owner_state'] = GENERATE_LINK
        else:
            update.message.reply_text('Не вдалось опрацювати суму вашої комісії, спробуйте ще раз')
    else:
        update.message.reply_text(f'Введіть суму на яку ви хочете виставити запит, в форматі DD.CC')
        context.user_data['owner_state'] = PORTMONE_SUM


def generate_link_v1(update, context):
    sum = update.message.text
    n_sum = conversion_to_float(sum=sum)
    if n_sum is not None:
        p = Portmone(sum=n_sum)
        result = p.get_link()
        update.message.reply_text(f'{result}')
        context.user_data['owner_state'] = None
    else:
        update.message.reply_text('Не вдалось обробити вашу суму, спробуйте ще раз')


def generate_link_v2(update, context):
    sum = update.message.text
    n_sum = conversion_to_float(sum=sum)
    if n_sum is not None:
        p = Portmone(sum=n_sum, commission=context.user_data['commission'])
        result = p.get_link()
        update.message.reply_text(f'{result}')
        context.user_data['owner_state'] = None
    else:
        update.message.reply_text('Не вдалось обробити вашу суму, спробуйте ще раз')


def drivers_rating(update, context):
    text = 'Рейтинг водіїв\n\n'
    for fleet in DriversRatingMixin().get_rating():
        text += fleet['fleet'] + '\n'
        for period in fleet['rating']:
            text += f"{period['start']:%d.%m.%Y} - {period['end']:%d.%m.%Y}" + '\n'
            if period['rating']:
                text += '\n'.join([f"{item['num']} {item['driver']} {item['amount']:15.2f} {- item['trips'] if item['trips']>0 else ''}" for item in period['rating']]) + '\n\n'
            else:
                text += 'Отримання даних... Спробуйте пізніше\n'
    update.message.reply_text(text)


def driver_total_weekly_rating(update, context):
    text = 'Рейтинг водіїв\n'
    totals = {}
    rate = DriversRatingMixin().get_rating()
    text += f"{rate[0]['rating'][0]['start']:%d.%m.%Y} - {rate[0]['rating'][0]['end']:%d.%m.%Y}" + '\n\n'
    for fleet in DriversRatingMixin().get_rating():
        for period in fleet['rating']:
            if period['rating']:
                for item in period['rating']:
                    totals.setdefault(item['driver'], 0)
                    totals[item['driver']] += round(item['amount'], 2)
            else:
                text += 'Отримання даних... Спробуйте пізніше\n'

    totals = dict(sorted(totals.items(), key=lambda item: item[1], reverse=True))

    id = 1
    for key, value in totals.items():
        text += f"{id} {key}: {value}\n"
        id += 1
    update.message.reply_text(text)