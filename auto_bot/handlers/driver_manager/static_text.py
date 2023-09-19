NAME, SECOND_NAME, EMAIL, PHONE_NUMBER = range(100, 104)
STATUS, DRIVER, CAR_NUMBERPLATE, RATE, NAME_VEHICLE, MODEL_VEHICLE, LICENCE_PLATE_VEHICLE = range(104, 111)
VIN_CODE_VEHICLE, JOB_APPLICATION, V_GPS, V_GPS_IMEI = range(111, 115)
START_EARNINGS, END_EARNINGS, START_EFFICIENCY, END_EFFICIENCY, START_DRIVER_EFF, END_DRIVER_EFF = range(115, 121)
SPENDING_CAR = 121
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
no_drivers_text = "У Вас немає звітів по водіях за цей період"
no_reports_text = "У Вас немає заробітків за цей період"
no_vehicles_text = "У Вас немає звітів по автомобілях за цей період"
no_manager_vehicles = "У Вас немає автомобілів"
no_manager_drivers = "У Вас немає водіїв"
choose_period_text = "Оберіть період звіту"
start_report_text = "Введіть з якої дати отримати звіт (ДД.MM.РРРР)"
end_report_text = "Введіть по яку дату отримати звіт (ДД.MM.РРРР)"
invalid_data_text = "Невірні дані, спробуйте ще раз"
invalid_end_data_text = "Невірна кінцева дата, введіть ще раз"
partner_vehicles = "Оберіть авто"
partner_drivers = "Оберіть водія"
choose_category_text = "Оберіть категорію витрат"
ask_spend_sum_text = "Вкажіть суму витрат"
wrong_sum_type = "Не вірна сума витрат. Введіть суму(число) ще раз"
spending_saved_text = "Витрати успішно записано."
generate_text = "Генеруємо звіт"
pin_vehicle_callback = "pin_vehicle"

manager_buttons = (
    "\U0001F504 Оновити базу водіїв",
    "\U0001FAA2 Привязати авто до водія",
    "\U0001F4B0 Звіт по заробітках",
    "\U0001F3AF Ефективність автомобілів",
    "\U0001F680 Ефективність водія",
    "\U0001F4B8 Витрати автомобіля"
)

report_period = ("Минулий тиждень",
                 "Поточний тиждень",
                 "Вибрати період")

spending_buttons = ("\U0001F4A6 Мийка",
                    "\u26FD Паливо",
                    "\U0001FA9B Обслуговування",
                    "\U0001F6E0 Ремонт")


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
