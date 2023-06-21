NAME, SECOND_NAME, EMAIL, PHONE_NUMBER = range(100, 104)
STATUS, DRIVER, CAR_NUMBERPLATE, RATE, NAME_VEHICLE, MODEL_VEHICLE, LICENCE_PLATE_VEHICLE = range(104, 111)
VIN_CODE_VEHICLE, JOB_APPLICATION, V_GPS, V_GPS_IMEI = range(111, 115)
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


def ask_driver_paid(driver):
    message = f"Чи розрахувався водій {driver} за минулий тиждень?"
    return message


def remove_cash_text(driver):
    message = f"Розрахунок готівкою водію {driver} вимкнено"
    return message
