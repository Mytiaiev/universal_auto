import json
import os

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram.ext import Updater
from telegram import Update
import ast

from auto_bot.dispatcher import setup_dispatcher
from auto_bot.main import bot
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="telegram.ext")
PORT = int(os.environ.get('PORT', '8443'))
WEBHOOK_URL = os.environ['WEBHOOK_URL']
updater = Updater(os.environ['TELEGRAM_TOKEN'], use_context=True)
dp = setup_dispatcher(updater.dispatcher)


@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        json_string = request.body.decode('utf-8')
        update = Update.de_json(json.loads(json_string), bot)
        dp.process_update(update)
        return HttpResponse(status=200)


def main():
    bot_prod_env = os.environ.get('BOT_PROD_ENV')
    if bot_prod_env is not None:
        bot_prod_env = ast.literal_eval(bot_prod_env)
    if bot_prod_env:
        updater.start_webhook(
            listen='0.0.0.0',
            port=PORT,
            webhook_url=f'{WEBHOOK_URL}/webhook/'
        )
        updater.idle()
    else:
        updater.start_polling()
        updater.idle()


def run():
    main()

@task_postrun.connect
def send_report_daily_in_group(sender=None, **kwargs):
    if sender == send_daily_into_group:
        result = kwargs.get("retval")
        message = '\U0001f3c6' + result[0] + '\U0001f3c6' + '\n'
        for num, driver in enumerate(result[1:], 2):
            message += f"{num}. {driver}\n"
        bot.send_message(chat_id=ParkSettings.get_value('DRIVERS_CHAT', -863882769), text=message)



