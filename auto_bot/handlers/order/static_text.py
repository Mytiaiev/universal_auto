FROM_ADDRESS, TO_THE_ADDRESS, COMMENT, TIME_ORDER, START_TIME_ORDER = range(1, 6)
NOT_CORRECT_ADDRESS = "Немає вірної адреси"
LOCATION = "Поділитися місцезнаходженням"

already_ordered = "У вас вже є активне замовлення, бажаєте замовити ще одне авто?"
complete_order_text = "Гарного дня. Дякуємо, що скористались нашими послугами"
from_address_search = "Знайшов можливі варіанти."
choose_from_address_text = "Оберіть вашу адресу."
choose_to_address_text = "Оберіть адресу призначення."
wrong_address_request = "Нам не вдалось обробити вашу адресу, спробуйте ще раз"
no_location_text = 'Нам не вдалось обробити ваше місце знаходження'
info_address_text = "Ви можете скористатись кнопкою або ввести адресу вручну"
ask_spot_text = 'Чи правильна ця адреса?'
from_address_text = 'Введіть адресу місця посадки:'
arrival_text = 'Введіть адресу місця призначення:'
payment_text = 'Виберіть спосіб оплати:'
order_customer_text = "Коли водій буде на місці, ви отримаєте повідомлення." \
                      "На карті нижче ви можете спостерігати, де зараз ваш водій"
driver_accept_text = 'Замовлення прийнято.Шукаємо водія'
driver_arrived = "Машину подано. Водій вас очікує"
select_car_error = "Для прийняття замовлень потрібно розпочати роботу."
driver_cancel = "Водій відхилив замовлення. Пошук іншого водія..."
client_cancel = "Ви відмовились від замовлення"
order_complete = "Ваше замовлення прийняте, очікуйте водія"
route_trip_text = "Поїздка була згідно маршруту?"
calc_price_text = 'Проводимо розрахунок вартості...'
wrong_time_format = 'Невірний формат.Вкажіть, будь ласка, час у форматі HH:MM(напр. 18:45)'
small_time_delta = 'Вкажіть, будь ласка, більш пізній час'
ask_time_text = 'Вкажіть, будь ласка, час для подачі таксі(напр. 18:45)'
already_accepted = "Це замовлення вже виконано."
decline_order = "Ви не прийняли замовлення, ваш рейтинг понизився на 1"
client_decline = "Ви відмовились від замовлення"
search_driver_1 = "Будь ласка, зачекайте, ми працюємо над вашим питанням."
search_driver_2 = "Ми все ще шукаємо водія для вас. Зачекайте, будь ласка."
no_driver_in_radius = "Зараз спостерігається підвищений попит бажаєте збільшити ціну для прискорення пошуку?"
increase_radius_text = "На скільки збільшити ціну?"
time_order_accepted = "Ви прийняли замовлення, ми повідомимо вам, коли буде наближатись час до виконання"

order_inline_buttons = (
    "\u274c Відхилити",
    "\u2705 Прийняти замовлення",
    "\u2705 Розпочати поїздку",
    "\u2705 Так",
    "\u274c Ні",
    "\u2705 Розрахувати вартість і завершити поїздку",
    "\U0001F519 Повернутися назад",
    "\u2705 Завершити поїздку",
    "\U0001F6A5 Побудувати маршрут",
    "\u2705 Залишити відгук",
)

timeorder_inline_buttons = (
    "\u2705 Розпочати замовлення"
)


search_inline_buttons = (
    "\U0001f4b7 Збільшити вартість",
    "\U0001F50D Продовжити пошук",
    "\u274c Скасувати замовлення",
    "\u23F0 Замовити на інший час",
    "\u2705 Замовити на зараз",
    "\U0001F4CD Поділитися місцезнаходженням",
    "\u274c Місце - невірне",
    "\u2705 Місце - вірне"

)

price_inline_buttons = (
    "30 \U000020B4",
    "50 \U000020B4",
    "100 \U000020B4",
    "150 \U000020B4",
    "\U0001f4b7 Готівка",
    "\U0001f4b8 Картка"
)


def price_info(in_city, out_city):
    message = f"Наші тарифи:\nВ місті - {in_city} грн/км\n" + \
              f"За містом - {out_city} грн/км"
    return message


def order_info(number, address, to_address, payment, phone, price=None, distance=None, time=None):
    time_message = f"<u>Замовлення на певний час {number}:</u>\n" \
                   f"<b>Час подачі:{time}</b>\n"
    now_message = f"Отримано нове замовлення {number}:\n"
    message = f"Адреса посадки: {address}\n" \
              f"Місце прибуття: {to_address}\n" \
              f"Спосіб оплати: {payment}\n" \
              f"Номер телефону: {phone}\n"
    if price is not None:
        message += f"Загальна вартість: {price} грн\n" + f"Довжина маршруту: {distance} км"
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
              f'Сума замовлення: {price} грн\n'
    return message


def client_order_info(address, to_address, payment, phone, price, increase=None):
    message = f"Ваше замовлення:\n" \
              f"Адреса посадки: {address}\n" \
              f"Місце прибуття: {to_address}\n" \
              f"Спосіб оплати: {payment}\n" \
              f"Номер телефону: {phone}\n" \
              f"Сума замовлення: {price} грн\n" \
              f'Шукаємо водія...'
    if increase:
        message = f"Замовлення оновлено\nНова сума замовлення: {price} грн\n" \
                  f"Шукаємо водія..."
    return message
