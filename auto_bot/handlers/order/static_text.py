from app.models import ParkSettings

FROM_ADDRESS, TO_THE_ADDRESS, COMMENT, TIME_ORDER, START_TIME_ORDER = range(1, 6)
U_NAME, U_SECOND_NAME, U_EMAIL, FIRST_ADDRESS_CHECK, SECOND_ADDRESS_CHECK = range(6, 11)
LOCATION_WRONG = "Місце посадки - невірне"
LOCATION_CORRECT = "Місце посадки - вірне"
NOT_CORRECT_ADDRESS = "Немає вірної адреси"
CONTINUE = "Продовжити замовлення"
CANCEL = "Скасувати замовлення"
TOMORROW = "Замовити на завтра"
TODAY = "Замовити на інший час"
NOW = "Замовити на зараз"
LOCATION = "Розшарити локацію"

PAYCARD = "Картка"
CASH = "Готівка"

already_ordered = "У вас вже є активне замовлення, бажаєте замовити ще одне авто?"
price_info = f"Ціна поїздки в місті {ParkSettings.get_value('TARIFF_IN_THE_CITY', 15)}грн/км\n" + \
             f"За містом - {ParkSettings.get_value('TARIFF_OUTSIDE_THE_CITY', 30)}грн/км"
AVERAGE_DISTANCE_PER_HOUR, COST_PER_KM = int(f"{ParkSettings.get_value('AVERAGE_DISTANCE_PER_HOUR', 25)}"), int(
    f"{ParkSettings.get_value('COST_PER_KM', 20)}")
complete_order_text = "Гарного дня. Дякуємо, що скористались нашими послугами"
choose_address_text = "Оберіть вашу адресу. Інакше натисніть - 'Немає вірної адреси'" \
                      " та вкажіть більш детально вашу адресу"
wrong_address_request = "Нам не вдалось обробити вашу адресу, спробуйте ще раз"
order_customer_text = "Коли водій буде на місці, ви отримаєте повідомлення." \
                      "На карті нижче ви можете спостерігати, де зараз ваш водій"
driver_arrived = "Машину подано. Водій вас очікує"
select_car_error = "Щоб приймати замовлення, скористайтесь спочатку командой /status," \
                   "щоб позначити на якому ви сьогодні авто"
driver_cancel = "Водій відхилив замовлення. Пошук іншого водія..."
order_complete = "Ваше замовлення прийняте, очікуйте водія"

order_inline_buttons = (
    "\u274c Відхилити",
    "\u2705 Прийняти замовлення",
    "\u2705 Клієнт на місці",
    "\u2705 Рухались по маршруту",
    "\u274c Відхилялись від маршрута",
    "\u2705 Розрахувати вартість і завершити поїздку",
    "\u274c Повернутися назад",
    "\u2705 Завершити поїздку",
    "\U0001F6A5 Побудувати маршрут"
    "\U0001f4f2 Дзвонити"
)


def order_info(number, address, to_address, payment, phone, price=None, distance=None, time=None):
    time_message = f"<u>Замовлення на певний час {number}:</u>\n" \
                  f"<b>Час подачі:{time}</b>\n"
    now_message = f"Отримано нове замовлення {number}:\n"
    message = f"Адреса посадки: {address}\n" \
              f"Місце прибуття: {to_address}\n" \
              f"Спосіб оплати: {payment}\n" \
              f"Номер телефону: {phone}\n"
    if price is not None:
        message += f"Загальна вартість: {price}грн\n" + f"Довжина маршруту: {distance}км"
    elif time is not None:
        message = time_message + message
    else:
        message = now_message + message
    return message

