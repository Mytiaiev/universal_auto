import json
import os

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram.ext import Updater
from telegram import Update
import ast

from auto_bot.dispatcher import setup_dispatcher
from auto_bot.main import bot

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


dp.add_handler(CommandHandler("buy", payment_request))
# Command for Owner
dp.add_handler(CommandHandler("report", report))
dp.add_handler(CommandHandler("download_report", download_report))
dp.add_handler(CommandHandler("rating", drivers_rating))
dp.add_handler(CommandHandler("total_weekly_rating", driver_total_weekly_rating))

# Transfer money
dp.add_handler(CommandHandler("payment", payments))
dp.add_handler(MessageHandler(Filters.regex(fr"^{TRANSFER_MONEY}$"), get_card))
dp.add_handler(MessageHandler(Filters.regex(fr"^{THE_DATA_IS_CORRECT}$"), correct_transfer))
dp.add_handler(MessageHandler(Filters.regex(fr"^{THE_DATA_IS_WRONG}$"), wrong_transfer))

# Generate link debt
dp.add_handler(MessageHandler(Filters.regex(fr"^{_GENERATE_LINK}$"), commission))
dp.add_handler(MessageHandler(Filters.regex(fr"^{COMMISSION_ONLY_PORTMONE}$"), get_sum_for_portmone))
dp.add_handler(MessageHandler(Filters.regex(fr"^{MY_COMMISSION}$"), get_my_commission))

# Publicly available commands
# Getting id
dp.add_handler(CommandHandler("id", get_id))
# Information on commands
dp.add_handler(CommandHandler("help", help))

# Commands for Users
# Ordering taxi
dp.add_handler(CommandHandler("start", start))
# incomplete auth
dp.add_handler(MessageHandler(Filters.contact, update_phone_number))
# ordering taxi
dp.add_handler(MessageHandler(Filters.location, location))

dp.add_handler(MessageHandler(Filters.regex(fr"^\U0001f696 Викликати Таксі$"), continue_order))

dp.add_handler(MessageHandler(Filters.regex(fr"^\u2705 {LOCATION_CORRECT}$"), to_the_address))
dp.add_handler(MessageHandler(Filters.regex(fr"^\u274c {LOCATION_WRONG}$"), from_address))
dp.add_handler(MessageHandler(Filters.regex(fr"^Замовити на інший час$"), time_order))
updater.job_queue.run_repeating(send_time_orders, interval=int(ParkSettings.get_value('CHECK_ORDER_TIME_SEC', 100)))
dp.add_handler(MessageHandler(Filters.regex(fr"^\u274c {CANCEL}$"), cancel_order))
dp.add_handler(MessageHandler(Filters.regex(fr"^\u2705 {CONTINUE}$"), time_for_order))

dp.add_handler(MessageHandler(
    Filters.regex(fr"^\U0001f4b7 {CASH}$") |
    Filters.regex(fr"^\U0001f4b8 {_CARD}$"),
    order_create))

# sending comment
dp.add_handler(MessageHandler(Filters.regex(r"^\U0001f4e2 Залишити відгук$") |
                              Filters.regex(fr"^Відмовитись від замовлення$"),
                              comment))
# Add job application
dp.add_handler(MessageHandler(Filters.regex(r"^\U0001F4E8 Залишити заявку на роботу$"), job_application))

dp.add_handler(job_docs_conversation)

# Commands for Drivers
# Changing status of driver
dp.add_handler(CommandHandler("status", status))
dp.add_handler(MessageHandler(
    Filters.regex(fr"^{Driver.ACTIVE}$") |
    Filters.regex(fr"^{Driver.WITH_CLIENT}$") |
    Filters.regex(fr"^{Driver.WAIT_FOR_CLIENT}$") |
    Filters.regex(fr"^{Driver.OFFLINE}$") |
    Filters.regex(fr"^{Driver.RENT}$"),
    set_status))

# Updating status_car
dp.add_handler(CommandHandler("status_car", status_car))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{SERVICEABLE}$') |
    Filters.regex(fr'^{BROKEN}$'),
    numberplate))

# Sending report(payment debt)
dp.add_handler(debt_conversation)

# Take a day off/Take sick leave
dp.add_handler(CommandHandler("option", option))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{TAKE_A_DAY_OFF}$') |
    Filters.regex(fr'^{TAKE_SICK_LEAVE}$'),
    take_a_day_off_or_sick_leave))

# Сar registration for today
dp.add_handler(CommandHandler("car_change", get_vehicle_licence_plate))

# Get correct auto
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{CORRECT_AUTO}$') |
    Filters.regex(fr'^{NOT_CORRECT_AUTO}$'),
    correct_or_not_auto))

# Correct choice change_auto
dp.add_handler(MessageHandler(Filters.regex(fr'^{CORRECT_CHOICE}$'), get_imei))
dp.add_handler(MessageHandler(Filters.regex(fr'^{NOT_CORRECT_CHOICE}$'), get_vehicle_licence_plate))

# Commands for Driver Managers
# Returns status cars
dp.add_handler(CommandHandler("car_status", broken_car))
# Viewing status driver
dp.add_handler(CommandHandler("driver_status", driver_status))
# Add user and other
dp.add_handler(CommandHandler("add", add))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{CREATE_USER}$'),
    create))
# Add vehicle to db
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{CREATE_VEHICLE}$'),
    name_vehicle))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{USER_DRIVER}$') |
    Filters.regex(fr'^{USER_MANAGER_DRIVER}$'),
    name))
# Add vehicle to drivers
dp.add_handler(CommandHandler("add_vehicle_to_driver", get_list_drivers))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^{F_UKLON}$') |
    Filters.regex(fr'^{F_UBER}$') |
    Filters.regex(fr'^{F_BOLT}$'),
    get_driver_external_id))

# The job application on driver sent to fleet
dp.add_handler(CommandHandler("add_job_application_to_fleets", get_list_job_application))
dp.add_handler(MessageHandler(
    Filters.regex(fr'^- {F_BOLT}$') |
    Filters.regex(fr'^- {F_UBER}$'),
    add_job_application_to_fleet))

dp.add_handler(CommandHandler("add_imei_gps_to_driver", get_licence_plate_for_gps_imei))

# Commands for Service Station Manager
# Sending report on repair
dp.add_handler(CommandHandler("send_report", numberplate_car))

# dp.add_handler(CallbackQueryHandler(inline_buttons_for_driver, pattern='^(Accept order|Reject order|On the spot|Сlient on site|Along the route|Off route|End trip)$'))
dp.add_handler(CallbackQueryHandler(handle_callback_order))

# System commands
dp.add_handler(CommandHandler("cancel", cancel))
dp.add_handler(MessageHandler(Filters.text, text))
dp.add_error_handler(error_handler)

# need fix
dp.add_handler(CommandHandler('update', update_db, run_async=True))
dp.add_handler(CommandHandler("save_reports", save_reports))

dp.add_handler(MessageHandler(Filters.text('Get all today statistic'), get_manager_today_report))
dp.add_handler(MessageHandler(Filters.text('Get today statistic'), get_driver_today_report))
dp.add_handler(MessageHandler(Filters.text('Choice week number'), get_driver_week_report))
dp.add_handler(MessageHandler(Filters.text('Update report'), get_update_report))


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



