NAME, SECOND_NAME, EMAIL, PHONE_NUMBER = range(100, 104)
STATUS, DRIVER, CAR_NUMBERPLATE, RATE, NAME_VEHICLE, MODEL_VEHICLE, LICENCE_PLATE_VEHICLE = range(104, 111)
VIN_CODE_VEHICLE, JOB_APPLICATION, V_GPS, V_GPS_IMEI = range(111, 115)
START_EARNINGS, END_EARNINGS, START_EFFICIENCY, END_EFFICIENCY, START_DRIVER_EFF, END_DRIVER_EFF = range(115, 121)
USER_DRIVER, USER_MANAGER_DRIVER = 'Водія', 'Менеджера водія'
CREATE_USER, CREATE_VEHICLE = 'Додати користувача', 'Додати автомобіль'
F_UKLON, F_UBER, F_BOLT = 'Uklon', 'Uber', 'Bolt'
not_manager_text = "Зареєструйтесь, як менеджер водіїв"
SEND_JOB = 'Подати заявку'
DECLINE_JOB = 'Відхилити заявку'
paid_inline_buttons = (
    "\u2705 Так",
    "\u274c Ні"
)
choose_func_text = "Оберіть функцію"
get_drivers_text = "Інформація оновиться протягом декількох хвилин."
update_finished = "Інформація оновлена"
no_drivers_text = "У вас ще немає водіїв"
no_reports_text = "У вас ще немає заробітків"
no_vehicles_text = "У вас ще немає автомобілів"
choose_period_text = "Оберіть період звіту"
start_report_text = "Введіть з якої дати отримати звіт (ДД.MM.РРРР)"
end_report_text = "Введіть по яку дату отримати звіт (ДД.MM.РРРР)"
invalid_data_text = "Невірні дані, спробуйте ще раз"
invalid_end_data_text = "Невірна кінцева дата, введіть ще раз"
partner_vehicles = "Оберіть авто"
partner_drivers = "Оберіть водія"
pin_vehicle_callback = "pin_vehicle"

manager_buttons = (
    "\U0001F504 Оновити базу водіїв",
    "\U0001FAA2 Привязати авто до водія",
    "\U0001F4B0 Звіт по заробітках",
    "\U0001F3AF Ефективність автомобілів",
    "\U0001F680 Ефективність водія"
)

report_period = ("Минулий тиждень",
                 "Поточний тиждень",
                 "Вибрати період")


def ask_driver_paid(driver):
    message = f"Чи розрахувався водій {driver} за минулий тиждень?"
    return message


def remove_cash_text(driver, enable):
    if enable == 'true':
        message = f"Розрахунок готівкою водію {driver} увімкнено."
    else:
        message = f"Готівка вимкнена {driver}."
    return message


def pin_vehicle_to_driver(driver, vehicle):
    return f"Водію - {driver} прикріплено авто {vehicle}"
