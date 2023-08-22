from datetime import timedelta

from django.utils import timezone

FROM_ADDRESS, TO_THE_ADDRESS, COMMENT, TIME_ORDER, START_TIME_ORDER, ADD_INFO = range(1, 7)
NOT_CORRECT_ADDRESS = "На жаль, немає вірної адреси"
LOCATION = "Поділитися місцезнаходженням"

already_ordered = "У вас вже є активне замовлення, бажаєте замовити ще одне авто?"
complete_order_text = "Гарного дня. Дякуємо, що скористались нашими послугами"
creating_order_text = "Обробляємо ваше замовлення зачекайте будь-ласка"
from_address_search = "Знайшов можливі варіанти."
choose_from_address_text = "Оберіть, будь ласка, Вашу адресу."
choose_to_address_text = "Оберіть, будь ласка, адресу призначення."
wrong_address_request = "Нам не вдалось обробити Вашу адресу, спробуйте ще раз"
no_location_text = 'Нам не вдалось обробити Ваше місце знаходження'
info_address_text = "Ви можете скористатись кнопкою або ввести адресу вручну"
ask_spot_text = 'Чи вірна ця адреса?'
from_address_text = 'Введіть, будь ласка, адресу місця посадки:'
arrival_text = 'Введіть, будь ласка, адресу місця призначення:'
payment_text = 'Виберіть, будь ласка, спосіб оплати:'
order_customer_text = "Коли водій буде на місці, ви отримаєте повідомлення." \
                      "На карті нижче ви можете спостерігати, де зараз ваш водій"
driver_accept_text = 'Ваше замовлення прийнято.Шукаємо водія'
driver_arrived = "Машину подано. Водій вас очікує"
select_car_error = "Для прийняття замовлень потрібно розпочати роботу."
add_many_auto_text = 'Не вдається знайти авто для роботи зверніться до менеджера.'
driver_cancel = "На жаль, водій відхилив замовлення. Пошук іншого водія..."
client_cancel = "Ви відмовились від замовлення"
order_complete = "Ваше замовлення прийняте, очікуйте, будь ласка, водія"
route_trip_text = "Поїздка була згідно маршруту?"
calc_price_text = 'Проводимо розрахунок вартості...'
wrong_time_format = 'Невірний формат.Вкажіть, будь ласка, час у форматі HH:MM(напр. 18:45)'
ask_time_text = 'Вкажіть, будь ласка, час для подачі таксі(напр. 18:45)'
already_accepted = "Це замовлення вже виконано або виконується."
decline_order = "Ви не прийняли замовлення, ваш рейтинг понизився на 1"
client_decline = "Ви відмовились від замовлення"
search_driver = "Шукаємо водія"
search_driver_1 = "Будь ласка, зачекайте, ми працюємо над вашим питанням."
search_driver_2 = "Ми все ще шукаємо водія для вас. Зачекайте, будь ласка."
no_driver_in_radius = "Зараз спостерігається підвищений попит бажаєте збільшити ціну для прискорення пошуку?"
increase_radius_text = "На скільки збільшити ціну?"
payment_title = 'Ninja Taxi'
payment_description = 'Ninja Taxi - це надійний та професійний провайдер послуг таксі'
payment_payload = 'Додаткові дані для ідентифікації користувача'
payment_currency = 'UAH'
payment_price = 'Ціна'
trip_paymented = 'Поїздка оплачена'
error_payment = "Дані по оплаті не співпали"
order_date_text = "Оберіть, коли Ви бажаєте здійснити поїздку"
update_text = "Оновлюємо інформацію"
add_info_text = "Бажаєте додати коментар до замовлення?"
ask_info_text = "Напишіть, будь ласка, Ваш коментар"
too_long_text = "Занадто великий коментар, вкажіть тільки найважливіше"
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
    "\U0001F4DD Додати коментар",
    "\u274c Ні, дякую",
    '\u2705 Змінити тип оплати',
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

date_inline_buttons = (
    "\U000023F1 Сьогодні",
    "\U0001F5D3 Завтра"
)


def price_info(in_city, out_city):
    message = f"Наші тарифи:\nВ місті - {in_city} грн/км\n" + \
              f"За містом - {out_city} грн/км"
    return message


def order_info(order, time=None):
    if order.order_time and time:
        time = timezone.localtime(order.order_time).strftime("%Y-%m-%d %H:%M")
        message = f"<u>Замовлення на певний час {order.pk}:</u>\n" \
                  f"<b>Час подачі:{time}</b>\n"
    else:
        message = f"Отримано нове замовлення {order.pk}:\n"
    message += f"Адреса посадки: {order.from_address}\n" \
               f"Місце прибуття: {order.to_the_address}\n" \
               f"Спосіб оплати: {order.payment_method}\n" \
               f"Номер телефону: {order.phone_number}\n" \
               f"Загальна вартість: {order.sum} грн\n" \
               f"Довжина маршруту: {order.distance_google} км\n"
    if order.info:
        message += f"Коментар: {order.info}"
    return message


def client_order_info(order):
    if order.order_time:
        time = timezone.localtime(order.order_time).strftime("%Y-%m-%d %H:%M")
        message = f"<u>Замовлення на певний час {order.pk}:</u>\n" \
                  f"<b>Час подачі:{time}</b>\n"
    else:
        message = f"Ваше замовлення {order.pk}:\n"
    message += f"Адреса посадки: {order.from_address}\n" \
               f"Місце прибуття: {order.to_the_address}\n" \
               f"Спосіб оплати: {order.payment_method}\n" \
               f"Номер телефону: {order.phone_number}\n" \
               f"Загальна вартість: {order.sum} грн\n" \
               f"Довжина маршруту: {order.distance_google} км\n"
    if order.info:
        message += f"Коментар: {order.info}"
    return message


def driver_complete_text(price):
    message = f"Поїздку завершено\n" \
              f"Сума замовлення: {price} грн"
    return message


def time_order_accepted(address, time):
    return f"Ви прийняли замовлення, за адресою {address} на {time}.\n" \
           f"Ми повідомимо вам, коли буде наближатись час до виконання."


def client_order_text(driver, vehicle, plate, phone, price):
    message = f'Вас вітає Ninja-Taxi!\n' \
              f'Ваш водій: {driver}\n' \
              f'Назва: {vehicle}\n' \
              f'Номер машини: {plate}\n' \
              f'Номер телефону: {phone}\n' \
              f'Сума замовлення: {price} грн\n'
    return message


def client_order_info(order):
    if order.car_delivery_price:
        message = f"Замовлення оновлено\n" \
                  f"Нова сума замовлення: {order.sum} грн\n"
    else:
        message = f"Ваше замовлення:\n" \
                  f"Адреса посадки: {order.from_address}\n" \
                  f"Місце прибуття: {order.to_the_address}\n" \
                  f"Спосіб оплати: {order.payment_method}\n" \
                  f"Номер телефону: {order.phone_number}\n" \
                  f"Сума замовлення: {order.sum} грн\n"
    return message


def manager_change_payments_info(order):
    message = f"Замовлення: {order.pk}\n" \
              f"Водій: {order.driver}\n" \
              f"Автомобіль: {order.driver.vehicle}\n" \
              f"Сума замовлення: {order.sum}\n" \
              f"Змінив спосіб оплати на: {order.payment_method}\n"
    return message

def small_time_delta(time, delta):
    format_time = (time + timedelta(minutes=delta)).time().strftime('%H:%M')
    message = f'Вкажіть, будь ласка, більш пізній час.\n' \
              f'Мінімальний час для передзамовлення: {format_time}'
    return message
