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
LOCATION = "Поділитися місцезнаходженням"
INCREASE_PRICE = "Збільшити вартість"
PAYCARD = "Картка"
CASH = "Готівка"

already_ordered = "У вас вже є активне замовлення, бажаєте замовити ще одне авто?"
price_info = f"Ціна поїздки в місті {ParkSettings.get_value('TARIFF_IN_THE_CITY', 15)} грн/км\n" + \
             f"За містом - {ParkSettings.get_value('TARIFF_OUTSIDE_THE_CITY', 30)} грн/км"
AVERAGE_DISTANCE_PER_HOUR, COST_PER_KM = int(f"{ParkSettings.get_value('AVERAGE_DISTANCE_PER_HOUR', 25)}"), int(
    f"{ParkSettings.get_value('COST_PER_KM', 20)}")
complete_order_text = "Гарного дня. Дякуємо, що скористались нашими послугами"
choose_address_text = "Оберіть вашу адресу. Інакше натисніть - 'Немає вірної адреси'" \
                      " та вкажіть більш детально вашу адресу"
wrong_address_request = "Нам не вдалось обробити вашу адресу, спробуйте ще раз"
no_location_text = 'Нам не вдалось обробити ваше місце знаходження'
ask_spot_text = 'Оберіть статус посадки'
from_address_text = 'Введіть адресу місця посадки:'
arrival_text = 'Введіть адресу місця призначення:'
payment_text = 'Виберіть спосіб оплати:'
order_customer_text = "Коли водій буде на місці, ви отримаєте повідомлення." \
                      "На карті нижче ви можете спостерігати, де зараз ваш водій"
driver_accept_text = 'Замовлення прийнято.Шукаємо водія'
driver_arrived = "Машину подано. Водій вас очікує"
select_car_error = "Щоб приймати замовлення, скористайтесь спочатку командой /status," \
                   "щоб позначити на якому ви сьогодні авто"
driver_cancel = "Водій відхилив замовлення. Пошук іншого водія..."
client_cancel = "Ви відмовились від замовлення"
order_complete = "Ваше замовлення прийняте, очікуйте водія"
route_trip_text = "Поїздка була згідно маршруту?"
calc_price_text = 'Проводимо розрахунок вартості...'
wrong_time_format = 'Невірний формат.Вкажіть, будь ласка, час у форматі HH:MM(напр. 18:45)'
small_time_delta = 'Вкажіть, будь ласка, більш пізній час'
ask_time_text = 'Вкажіть, будь ласка, час для подачі таксі(напр. 18:45)'
already_accepted = "Це замовлення вже виконується."

search_driver = "Замовлення прийняте, шукаємо водія для вас..."
search_driver_1 = "Будь ласка, зачекайте, ми працюємо над вашим питанням."
search_driver_2 = "Ми все ще шукаємо водія для вас. Зачекайте, будь ласка."
no_driver_in_radius = "Зараз спостерігається підвищений попит бажаєте збільшити ціну для прискорення пошуку?"
order_inline_buttons = (
    "\u274c Відхилити",
    "\u2705 Прийняти замовлення",
    "\u2705 Розпочати поїздку",
    "\u2705 Так",
    "\u274c Ні",
    "\u2705 Розрахувати вартість і завершити поїздку",
    "\u274c Повернутися назад",
    "\u2705 Завершити поїздку",
    "\U0001F6A5 Побудувати маршрут",
    "\u2705 Залишити відгук",
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
        message += f"Загальна вартість: {price} грн\n" + f"Довжина маршруту: {distance}км"
    elif time is not None:
        message = time_message + message
    else:
        message = now_message + message
    return message


def driver_complete_text(price):
    message = f"Поїздку завершено\n" \
              f"Сума замовлення: {price} грн"
    return message


def client_order_text(driver, vehicle, plate, phone, price):
    message = f'Вас вітає Ninja-Taxi!\n' \
              f'Ваш водій: {driver}\n' \
              f'Назва: {vehicle}\n' \
              f'Номер машини: {plate}\n' \
              f'Номер телефону: {phone}\n' \
              f'Сума замовлення: {price} грн'
    return message
