from celery.signals import task_postrun

from app.models import Driver, ParkSettings
from auto.tasks import send_daily_into_group, download_weekly_report
from auto_bot.handlers.main.static_text import DEVELOPER_CHAT_ID
from auto_bot.main import bot


def report(update, context):
    update.message.reply_text('Ваш запит прийнято.\nМи надішлемо вам звіт, як тільки він сформується')
    update.message.reply_text("Введіть ваш Uber OTP код з SMS, якщо ви отримали його")
    download_weekly_report.delay()


@task_postrun.connect
def send_report(sender=None, **kwargs):
    if sender == download_weekly_report:
        rep = kwargs.get("retval")
        owner, totals = rep[0], rep[1]
        drivers = {f'{i}': i.chat_id for i in Driver.objects.all()}
        # sending report to owner
        message = f'Fleet Owner: {"%.2f" % owner["Fleet Owner"]}\n\n' + '\n'.join(totals.values())
        bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message)

        # sending report to driver
        if drivers:
            for driver in drivers:
                try:
                    message, chat_id = totals[f'{driver}'], drivers[f'{driver}']
                    bot.send_message(chat_id=chat_id, text=message)
                except:
                    pass


@task_postrun.connect
def send_report_daily_in_group(sender=None, **kwargs):
    if sender == send_daily_into_group:
        result = kwargs.get("retval")
        try:
            message = '\U0001f3c6' + result[0] + '\n'
            for num, driver in enumerate(result[1:], 2):
                message += f"{num}. {driver}\n"
            bot.send_message(chat_id=ParkSettings.get_value('DRIVERS_CHAT', -863882769), text=message)
        except IndexError:
            bot.send_message(chat_id=ParkSettings.get_value('DRIVERS_CHAT', -863882769), text="No reports")
