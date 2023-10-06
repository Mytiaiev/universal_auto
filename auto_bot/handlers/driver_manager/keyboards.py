from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from app.models import Driver
from auto_bot.handlers.driver_manager.static_text import *
from auto_bot.handlers.order.static_text import order_inline_buttons
from auto_bot.handlers.main.keyboards import main


def inline_driver_paid_kb(pk):
    keyboard = [
        [InlineKeyboardButton(paid_inline_buttons[0], callback_data=f"Paid_driver true {pk}"),
         InlineKeyboardButton(paid_inline_buttons[1], callback_data=f"Paid_driver false {pk}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_func_with_driver_kb():
    keyboard = [
        [InlineKeyboardButton(manager_buttons[0], callback_data="Update_drivers")],
        [InlineKeyboardButton(manager_buttons[1], callback_data="Pin_vehicle_to_driver")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_func_with_vehicle_kb():
    keyboard = [
        [InlineKeyboardButton(manager_buttons[5], callback_data="Spending_car")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_statistic_kb():
    keyboard = [
        [InlineKeyboardButton(manager_buttons[2], callback_data="Get_report")],
        [InlineKeyboardButton(manager_buttons[3], callback_data="Get_efficiency_report")],
        [InlineKeyboardButton(manager_buttons[4], callback_data="Get_driver_efficiency")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_earning_report_kb(back_step):
    keyboard = [
        [InlineKeyboardButton(report_period[0], callback_data="Weekly_payment")],
        [InlineKeyboardButton(report_period[1], callback_data="Daily_payment")],
        [InlineKeyboardButton(report_period[3], callback_data="Custom_report")],
        [InlineKeyboardButton(report_period[2], callback_data="Daily_report")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data=back_step)],
        main
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_partner_vehicles(vehicles, callback, back_step):
    keyboard = [
        [InlineKeyboardButton(f"{vehicle}", callback_data=f"{callback} {vehicle.id}")] for vehicle in vehicles]
    keyboard.append([InlineKeyboardButton(order_inline_buttons[6], callback_data=back_step)])
    keyboard.append(main)

    return InlineKeyboardMarkup(keyboard)


def inline_partner_drivers(callback, drivers, back_step, pk_vehicle=None):
    keyboard = [
        [InlineKeyboardButton(f"{str(driver).split()[0][0]}.{str(driver).split()[1]}",
                              callback_data=f"{callback} {driver.id} {pk_vehicle}")] for driver in drivers]
    keyboard.append([InlineKeyboardButton(order_inline_buttons[6], callback_data=back_step)])
    keyboard.append(main)
    return InlineKeyboardMarkup(keyboard)


def inline_efficiency_report_kb(back_step):
    keyboard = [
        [InlineKeyboardButton(report_period[1], callback_data="Efficiency_daily")],
        [InlineKeyboardButton(report_period[2], callback_data="Efficiency_custom")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data=back_step)],
        main

    ]
    return InlineKeyboardMarkup(keyboard)


def inline_driver_eff_kb(back_step):
    keyboard = [
        [InlineKeyboardButton(report_period[1], callback_data="Driver_daily")],
        [InlineKeyboardButton(report_period[2], callback_data="Driver_custom")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data=back_step)],
        main

    ]
    return InlineKeyboardMarkup(keyboard)


def vehicle_spending_kb(back_step):
    keyboard = [
        [InlineKeyboardButton(spending_buttons[0], callback_data="WASHING"),
         InlineKeyboardButton(spending_buttons[1], callback_data="FUEL")],
        [InlineKeyboardButton(spending_buttons[2], callback_data="SERVICE"),
         InlineKeyboardButton(spending_buttons[3], callback_data="REPAIR")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data=back_step)],
        main

    ]
    return InlineKeyboardMarkup(keyboard)


create_user_keyboard = [KeyboardButton(f'{CREATE_USER}'),
                        KeyboardButton(f'{CREATE_VEHICLE}')]

role_keyboard = [KeyboardButton(text=f"{USER_DRIVER}"),
                 KeyboardButton(text=f"{USER_MANAGER_DRIVER}")]

fleets_keyboard = [[KeyboardButton(F_UBER)],
                   [KeyboardButton(F_UKLON)],
                   [KeyboardButton(F_BOLT)]]
fleet_job_keyboard = [[KeyboardButton(f'- {SEND_JOB}')],
                      [KeyboardButton(f'- {DECLINE_JOB}')]]

drivers_status_buttons = [[KeyboardButton(f'- {Driver.ACTIVE}')],
                          [KeyboardButton(f'- {Driver.WITH_CLIENT}')],
                          [KeyboardButton(f'- {Driver.WAIT_FOR_CLIENT}')],
                          [KeyboardButton(f'- {Driver.OFFLINE}')]
                   ]
