import queue
import re


from telegram.ext import CommandHandler, PreCheckoutQueryHandler, MessageHandler, Filters, CallbackQueryHandler, \
    ConversationHandler, Dispatcher
from app.models import Driver
from auto_bot.main import bot
from auto_bot.states import text
# handlers
from auto_bot.handlers.driver_manager.handlers import add_job_application_to_fleet, get_licence_plate_for_gps_imei, \
    get_list_job_application, name, name_vehicle, create, add, \
    driver_status, broken_car, remove_cash_by_manager, get_drivers_from_fleets, get_weekly_report, get_earning_report, \
    get_efficiency_report, get_report, get_efficiency_auto, get_partner_vehicles, get_partner_drivers, \
    pin_partner_vehicle_to_driver, statistic_functions, functions_with_drivers, get_drivers_statistics, \
    get_efficiency_for_drivers, functions_with_vehicles, choose_spending_category, ask_spending_sum
from auto_bot.handlers.comment.handlers import comment, save_comment
from auto_bot.handlers.service_manager.handlers import numberplate_car
from auto_bot.handlers.driver.handlers import sending_report, get_debt_photo, save_debt_report, \
    take_a_day_off_or_sick_leave, numberplate, status_car, choose_day_off_or_sick
from auto_bot.handlers.owner.handlers import driver_total_weekly_rating, drivers_rating, payments, get_card, \
    correct_transfer, wrong_transfer, get_my_commission, get_sum_for_portmone, commission
from auto_bot.handlers.status.handlers import correct_or_not_auto, get_imei, get_vehicle_of_driver
from auto_bot.handlers.order.handlers import continue_order, to_the_address, from_address, time_order, \
    order_create, get_location, handle_callback_order, increase_search_radius, \
    increase_order_price, first_address_check, second_address_check, client_reject_order, \
    ask_client_action, handle_order, choose_date_order, precheckout_callback, add_info_to_order, get_additional_info, \
    successful_payment, payment_duty, payment_method
from auto_bot.handlers.main.handlers import start, update_phone_number, helptext, get_id, cancel, error_handler, \
    more_function, start_query, get_about_us, celery_test
from auto_bot.handlers.driver_job.handlers import update_name, restart_job_application, update_second_name, \
    update_email, update_user_information, get_job_photo, upload_photo, upload_license_front_photo, \
    upload_license_back_photo, upload_expired_date, check_auto, upload_auto_doc, upload_insurance, \
    upload_expired_insurance, uklon_code, job_application
# text
from auto_bot.handlers.driver_manager.static_text import F_UBER, F_BOLT, USER_MANAGER_DRIVER, USER_DRIVER, \
    CREATE_VEHICLE, CREATE_USER
from auto_bot.handlers.owner.static_text import THE_DATA_IS_WRONG, THE_DATA_IS_CORRECT, TRANSFER_MONEY, MY_COMMISSION, \
    COMMISSION_ONLY_PORTMONE, GENERATE_LINK_PORTMONE
from auto_bot.handlers.status.static_text import CORRECT_AUTO, NOT_CORRECT_AUTO, CORRECT_CHOICE, NOT_CORRECT_CHOICE
from auto_bot.handlers.driver.static_text import SERVICEABLE, BROKEN
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
    entry_points=[CallbackQueryHandler(update_name, pattern='Job_driver'),
                  CommandHandler("restart", restart_job_application),
                  MessageHandler(Filters.regex(r'^\/.*'), cancel)
                  ],
    states={
        "JOB_USER_NAME": [MessageHandler(Filters.text, update_second_name, pass_user_data=True)],
        "JOB_LAST_NAME": [MessageHandler(Filters.text, update_email, pass_user_data=True)],
        "JOB_EMAIL": [MessageHandler(Filters.text, update_user_information, pass_user_data=True)],
        'WAIT_FOR_JOB_OPTION': [CallbackQueryHandler(get_job_photo, pattern="job_photo", pass_user_data=True)],
        'WAIT_FOR_JOB_PHOTO': [MessageHandler(Filters.photo, upload_photo, pass_user_data=True)],
        'WAIT_FOR_FRONT_PHOTO': [MessageHandler(Filters.photo, upload_license_front_photo, pass_user_data=True)],
        'WAIT_FOR_BACK_PHOTO': [MessageHandler(Filters.photo, upload_license_back_photo, pass_user_data=True)],
        'WAIT_FOR_EXPIRED': [MessageHandler(Filters.text, upload_expired_date, pass_user_data=True)],
        'WAIT_ANSWER': [CallbackQueryHandler(check_auto, pattern="have_auto", pass_user_data=True),
                        CallbackQueryHandler(upload_expired_insurance, pattern="no_auto", pass_user_data=True)],
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
    dp.add_handler(PreCheckoutQueryHandler(precheckout_callback))
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
    dp.add_handler(CommandHandler("test_celery", celery_test))
    dp.add_handler(CallbackQueryHandler(more_function, pattern="Other_user|Other_manager|More_driver"))
    # incomplete auth
    dp.add_handler(MessageHandler(Filters.contact, update_phone_number))
    # ordering taxi
    dp.add_handler(CallbackQueryHandler(start_query, pattern="Back_to_main"))
    dp.add_handler(CallbackQueryHandler(continue_order, pattern="Call_taxi"))
    dp.add_handler(MessageHandler(Filters.location, get_location))
    dp.add_handler(CallbackQueryHandler(from_address, pattern="Now_order|Wrong_place"))
    dp.add_handler(CallbackQueryHandler(to_the_address, pattern="Right_place"))
    dp.add_handler(CallbackQueryHandler(first_address_check, pattern="^From_address [0-9]+$"))
    dp.add_handler(CallbackQueryHandler(second_address_check, pattern="^To_the_address [0-9]+$"))
    dp.add_handler(CallbackQueryHandler(add_info_to_order, pattern="Add_information"))
    dp.add_handler(CallbackQueryHandler(get_additional_info, pattern="Choose_payment"))
    dp.add_handler(CallbackQueryHandler(order_create, pattern="Cash_payment|Card_payment"))
    dp.add_handler(CallbackQueryHandler(increase_search_radius, pattern="Increase_price"))
    dp.add_handler(CallbackQueryHandler(choose_date_order, pattern="On_time_order"))
    dp.add_handler(CallbackQueryHandler(time_order, pattern="Today_order|Tomorrow_order|No_driver_time_order"))
    dp.add_handler(CallbackQueryHandler(increase_order_price, pattern="30|50|100|150|Continue_search"))
    dp.add_handler(CallbackQueryHandler(ask_client_action, pattern="Ask_action"))
    dp.add_handler(CallbackQueryHandler(payment_duty, pattern="Duty"))
    dp.add_handler(CallbackQueryHandler(payment_method, pattern="Back_to_payment"))
    dp.add_handler(CallbackQueryHandler(handle_callback_order, pattern="^Accept_order [0-9]+$"))
    dp.add_handler(CallbackQueryHandler(handle_order,
                                        pattern=re.compile("^(Reject_order|Along_the_route|Off_route|"
                                                           "Accept|End_trip|Second_cash_payment|"
                                                           "Second_card_payment) [0-9]+$")))
    dp.add_handler(CallbackQueryHandler(handle_order, pattern="Client_on_site [0-9]+ [0-9]+"))
    dp.add_handler(CallbackQueryHandler(client_reject_order, pattern="^Client_reject [0-9]+$"))
    dp.add_handler(MessageHandler(Filters.successful_payment, successful_payment))
    # sending comment
    dp.add_handler(CallbackQueryHandler(comment, pattern="Cancel_order|Comment client"))
    dp.add_handler(CallbackQueryHandler(save_comment, pattern="5_Star|4_Star|3_Star|2_Star|1_Star"))

    # Add job application
    # Commands for Drivers
    dp.add_handler(CallbackQueryHandler(choose_day_off_or_sick, pattern="Off day_driver|Sick day_driver"))
    dp.add_handler(CallbackQueryHandler(take_a_day_off_or_sick_leave, pattern=re.compile(
        r"^Off|Sick \d{4}-\d{2}-\d{2}$")))

    # Updating status_car
    dp.add_handler(CommandHandler("status_car", status_car))
    dp.add_handler(MessageHandler(
        Filters.regex(fr'^{SERVICEABLE}$') |
        Filters.regex(fr'^{BROKEN}$'),
        numberplate))

    # Sending report(payment debt)
    dp.add_handler(debt_conversation)

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
    dp.add_handler(CallbackQueryHandler(remove_cash_by_manager,
                                        pattern=re.compile("^Paid_driver (true|false) [0-9]+$")))
    dp.add_handler(CallbackQueryHandler(functions_with_drivers, pattern="Setup_drivers"))
    dp.add_handler(CallbackQueryHandler(functions_with_vehicles, pattern="Setup_vehicles"))
    dp.add_handler(CallbackQueryHandler(statistic_functions, pattern="Get_statistic"))
    dp.add_handler(CallbackQueryHandler(get_drivers_from_fleets, pattern="Update_drivers"))
    dp.add_handler(CallbackQueryHandler(get_earning_report, pattern="Get_report"))
    dp.add_handler(CallbackQueryHandler(get_weekly_report, pattern="Weekly_report"))
    dp.add_handler(CallbackQueryHandler(get_report, pattern="Daily_report|Custom_report"))
    dp.add_handler(CallbackQueryHandler(get_efficiency_auto, pattern="Efficiency_daily|Efficiency_custom"))
    dp.add_handler(CallbackQueryHandler(get_efficiency_report, pattern="Get_efficiency_report"))
    dp.add_handler(CallbackQueryHandler(get_drivers_statistics, pattern="Get_driver_efficiency"))
    dp.add_handler(CallbackQueryHandler(get_efficiency_for_drivers, pattern="Driver_daily|Driver_custom"))
    dp.add_handler(CallbackQueryHandler(get_partner_vehicles, pattern="Pin_vehicle_to_driver|Spending_car"))
    dp.add_handler(CallbackQueryHandler(choose_spending_category,
                                        pattern=re.compile("^Spending_vehicle [0-9]+$")))
    dp.add_handler(CallbackQueryHandler(ask_spending_sum, pattern="WASHING|FUEL|SERVICE|REPAIR"))
    dp.add_handler(CallbackQueryHandler(get_partner_drivers,
                                        pattern=re.compile("^select_vehicle [0-9]+$")))
    dp.add_handler(CallbackQueryHandler(pin_partner_vehicle_to_driver,
                                        pattern=re.compile("^pin_vehicle [0-9]+ [0-9]+$")))

    dp.add_handler(CallbackQueryHandler(get_about_us, pattern="About_us"))

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
    dp.add_handler(CallbackQueryHandler(job_application, pattern='Job_application'))
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


update_queue = queue.Queue()
dispatcher = setup_dispatcher(Dispatcher(bot, update_queue))
