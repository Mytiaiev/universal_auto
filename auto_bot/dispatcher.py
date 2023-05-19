import re

from telegram.ext import CommandHandler, MessageHandler, Filters, Dispatcher, CallbackQueryHandler, ConversationHandler, \
    RegexHandler

from auto_bot.handlers.driver_manager.handlers import add_job_application_to_fleet, get_licence_plate_for_gps_imei, \
    get_list_job_application, get_driver_external_id, get_list_drivers, name, name_vehicle, create, add, driver_status, \
    broken_car
from auto_bot.main import bot
from app.models import Driver
from auto_bot.states import text
# handlers
from auto_bot.handlers.comment.handlers import comment
from auto_bot.handlers.service_manager.handlers import numberplate_car
from auto_bot.handlers.driver.handlers import sending_report, get_debt_photo, save_debt_report, \
    take_a_day_off_or_sick_leave, option, numberplate, status_car
from auto_bot.handlers.owner.handlers import driver_total_weekly_rating, drivers_rating, payments, get_card, \
    correct_transfer, wrong_transfer, get_my_commission, get_sum_for_portmone, commission
from auto_bot.handlers.reports.handlers import report, download_report
from auto_bot.handlers.status.handlers import status, correct_or_not_auto, set_status, \
    get_imei, finish_job_main, get_vehicle_of_driver
from auto_bot.handlers.order.handlers import continue_order, to_the_address, from_address, time_order, send_time_orders, \
    cancel_order, order_create, location, time_for_order, handle_callback_order, increase_search_radius, \
    increase_order_price
from auto_bot.handlers.main.handlers import start, update_phone_number, helptext, get_id, cancel, error_handler
from auto_bot.handlers.driver_job.handlers import update_name, restart_job_application, update_second_name, \
    update_email, update_user_information, get_job_photo, upload_photo, upload_license_front_photo, \
    upload_license_back_photo, upload_expired_date, check_auto, upload_auto_doc, upload_insurance, \
    upload_expired_insurance, uklon_code, job_application
# text
from auto_bot.handlers.driver_manager.static_text import F_UBER, F_BOLT, F_UKLON, USER_MANAGER_DRIVER, USER_DRIVER, \
    CREATE_VEHICLE, CREATE_USER
from auto_bot.handlers.order.static_text import LOCATION_CORRECT, LOCATION_WRONG, CANCEL, CASH, PAYCARD, CONTINUE, \
    TODAY, NOW, LOCATION, complete_order_text, INCREASE_PRICE
from auto_bot.handlers.owner.static_text import THE_DATA_IS_WRONG, THE_DATA_IS_CORRECT, TRANSFER_MONEY, MY_COMMISSION, \
    COMMISSION_ONLY_PORTMONE, GENERATE_LINK_PORTMONE
from auto_bot.handlers.status.static_text import CORRECT_AUTO, NOT_CORRECT_AUTO, CORRECT_CHOICE, NOT_CORRECT_CHOICE
from auto_bot.handlers.driver.static_text import TAKE_SICK_LEAVE, TAKE_A_DAY_OFF, SERVICEABLE, BROKEN
from auto_bot.handlers.main.static_text import main_buttons
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="telegram.ext")

# Conversations
debt_conversation = ConversationHandler(
    entry_points=[CommandHandler('sending_report', sending_report),
                  CommandHandler('cancel', cancel)],
    states={
        'WAIT_FOR_DEBT_OPTION': [CallbackQueryHandler(get_debt_photo, pattern='photo_debt')],
        'WAIT_FOR_DEBT_PHOTO': [MessageHandler(Filters.all, save_debt_report)]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

job_docs_conversation = ConversationHandler(
    entry_points=[MessageHandler(Filters.regex(r'^Водій$'), update_name),
                  CommandHandler("restart", restart_job_application),
                  MessageHandler(Filters.regex(r'^\/.*'), cancel)
                  ],
    states={
        "JOB_USER_NAME": [MessageHandler(Filters.text, update_second_name, pass_user_data=True)],
        "JOB_LAST_NAME": [MessageHandler(Filters.text, update_email, pass_user_data=True)],
        "JOB_EMAIL": [MessageHandler(Filters.text, update_user_information, pass_user_data=True)],
        'WAIT_FOR_JOB_OPTION': [CallbackQueryHandler(get_job_photo, pattern='job_photo', pass_user_data=True)],
        'WAIT_FOR_JOB_PHOTO': [MessageHandler(Filters.photo, upload_photo, pass_user_data=True)],
        'WAIT_FOR_FRONT_PHOTO': [MessageHandler(Filters.photo, upload_license_front_photo, pass_user_data=True)],
        'WAIT_FOR_BACK_PHOTO': [MessageHandler(Filters.photo, upload_license_back_photo, pass_user_data=True)],
        'WAIT_FOR_EXPIRED': [MessageHandler(Filters.text, upload_expired_date, pass_user_data=True)],
        'WAIT_ANSWER': [CallbackQueryHandler(check_auto, pass_user_data=True)],
        'WAIT_FOR_AUTO_YES_OPTION': [MessageHandler(Filters.photo, upload_auto_doc, pass_user_data=True)],
        'WAIT_FOR_INSURANCE': [MessageHandler(Filters.photo, upload_insurance, pass_user_data=True)],
        'WAIT_FOR_INSURANCE_EXPIRED': [MessageHandler(Filters.text, upload_expired_insurance, pass_user_data=True)],
        'JOB_UKLON_CODE': [MessageHandler(Filters.regex(r'^\d{4}$'), uklon_code)]
    },

    fallbacks=[MessageHandler(Filters.regex(r'^\/.*'), cancel), CommandHandler('cancel', cancel)],
    allow_reentry=True,
    per_user=True
)


def setup_dispatcher(dp):
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
    dp.add_handler(MessageHandler(Filters.regex(fr"^{GENERATE_LINK_PORTMONE}$"), commission))
    dp.add_handler(MessageHandler(Filters.regex(fr"^{COMMISSION_ONLY_PORTMONE}$"), get_sum_for_portmone))
    dp.add_handler(MessageHandler(Filters.regex(fr"^{MY_COMMISSION}$"), get_my_commission))
    # Publicly available commands
    # Getting id
    dp.add_handler(CommandHandler("id", get_id))
    # Information on commands
    dp.add_handler(CommandHandler("help", helptext))
    # Commands for Users
    # Ordering taxi
    dp.add_handler(CommandHandler("start", start))
    # incomplete auth
    dp.add_handler(MessageHandler(Filters.contact, update_phone_number))
    # ordering taxi
    dp.add_handler(MessageHandler(Filters.location, location))
    dp.add_handler(MessageHandler(Filters.regex(fr"^\{main_buttons[0]}$"), continue_order))
    dp.add_handler(MessageHandler(Filters.regex(fr"^\u2705 {LOCATION_CORRECT}$"), to_the_address))
    dp.add_handler(MessageHandler(Filters.regex(fr"^\u274c {LOCATION_WRONG}$"), from_address))
    dp.add_handler(MessageHandler(Filters.regex(fr"^\u2705 {NOW}$"), from_address))
    dp.add_handler(MessageHandler(Filters.regex(fr"^\u23F0 {TODAY}$"), time_order))
    dp.add_handler(MessageHandler(Filters.regex(fr"^\u274c {CANCEL}$"), cancel_order))
    dp.add_handler(MessageHandler(Filters.regex(fr"^\u2705 {CONTINUE}$"), time_for_order))
    dp.add_handler(MessageHandler(
        Filters.regex(fr"^\U0001f4b7 {CASH}$") |
        Filters.regex(fr"^\U0001f4b8 {PAYCARD}$"),
        order_create))
    dp.add_handler(MessageHandler(Filters.regex(fr"^\U0001f4b7 {INCREASE_PRICE}$"), increase_search_radius))
    dp.add_handler(MessageHandler(
        Filters.regex(fr"^\U0001f4b7 50 грн$") |
        Filters.regex(fr"^\U0001f4b7 100 грн$") |
        Filters.regex(fr"^\U0001f4b7 150 грн$"),
        increase_order_price))
    dp.add_handler(CallbackQueryHandler(handle_callback_order,
                                        pattern=re.compile(
                                            "^(Accept_order|Reject_order|Сlient_on_site|Along_the_route|Off_route|Accept|End_trip|Client_reject) [0-9]+$")))
    dp.add_handler(CallbackQueryHandler(comment, pattern="Comment client"))
    # sending comment
    dp.add_handler(MessageHandler(Filters.regex(fr"^\{complete_order_text}$") |
                                  Filters.regex(fr"^Відмовитись від замовлення$"),
                                  comment))
    dp.add_handler(CommandHandler("comment", comment))

    # Add job application
    dp.add_handler(MessageHandler(Filters.regex(fr"^\{main_buttons[2]}$"), job_application))
    # Commands for Drivers
    # Changing status of driver
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(MessageHandler(Filters.regex(fr"^\{main_buttons[4]}$"), status))
    dp.add_handler(MessageHandler(Filters.regex(fr"^\{main_buttons[5]}$"), finish_job_main))
    dp.add_handler(MessageHandler(
        Filters.regex(fr"^{Driver.ACTIVE}$") |
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
    dp.add_handler(MessageHandler(Filters.regex(fr'^{NOT_CORRECT_CHOICE}$'), get_vehicle_of_driver))
    # Get correct auto
    dp.add_handler(MessageHandler(
        Filters.regex(fr'^{CORRECT_AUTO}$') |
        Filters.regex(fr'^{NOT_CORRECT_AUTO}$'),
        correct_or_not_auto))

    # Correct choice change_auto
    dp.add_handler(MessageHandler(Filters.regex(fr'^{CORRECT_CHOICE}$'), get_imei))

    # Commands for Driver Managers
    # Returns status cars
    dp.add_handler(CommandHandler("car_status", broken_car))
    # Viewing status driver
    dp.add_handler(CommandHandler("driver_status", driver_status))
    # Add user and other
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(MessageHandler(Filters.regex(fr'^{CREATE_USER}$'), create))
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

    #
    # # System commands
    dp.add_handler(job_docs_conversation)
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(MessageHandler(Filters.text, text))
    dp.add_error_handler(error_handler)
    #
    # # need fix
    # dp.add_handler(CommandHandler('update', update_db, run_async=True))
    # dp.add_handler(CommandHandler("save_reports", save_reports))
    #
    # dp.add_handler(MessageHandler(Filters.text('Get all today statistic'), get_manager_today_report))
    # dp.add_handler(MessageHandler(Filters.text('Get today statistic'), get_driver_today_report))
    # dp.add_handler(MessageHandler(Filters.text('Choice week number'), get_driver_week_report))
    # dp.add_handler(MessageHandler(Filters.text('Update report'), get_update_report))

    return dp
