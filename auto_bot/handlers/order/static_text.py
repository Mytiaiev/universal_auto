from datetime import timedelta

from django.utils import timezone

from app.models import ParkSettings

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
info_address_text = "У Вас є опція вибору: використати кнопку або ввести адресу вручну"
ask_spot_text = 'Чи вірна ця адреса?'
from_address_text = 'Введіть, будь ласка, адресу Вашого місцезнаходження:'
arrival_text = 'Введіть, будь ласка, адресу місця призначення:'
payment_text = 'Виберіть, будь ласка, спосіб оплати:'
order_customer_text = "Коли водій буде на місці, ви отримаєте повідомлення." \
                      "На карті нижче ви можете спостерігати, де зараз ваш водій"
driver_accept_text = 'Ваше замовлення прийнято.Шукаємо водія'
driver_arrived = "Машину подано. Водій вас очікує"
select_car_error = "Для прийняття замовлень потрібно розпочати роботу."
accept_order_error = "Для прийняття замовлень потрібно стати водієм Ninja Taxi."
add_many_auto_text = 'Не вдається знайти авто для роботи зверніться до менеджера.'
driver_cancel = "На жаль, водій відхилив замовлення. Пошук іншого водія..."
client_cancel = "Ви відмовились від замовлення"
order_complete = "Ваше замовлення прийняте, очікуйте, будь ласка, водія"
route_trip_text = "Поїздка була згідно маршруту?"
calc_price_text = 'Проводимо розрахунок вартості...'
wrong_time_format = 'Невірний формат.Вкажіть, будь ласка, час у форматі HH:MM(напр. 18:45)'
ask_time_text = 'Вкажіть, будь ласка, бажану годину для прибуття таксі(напр. 18:45)'
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
order_not_payment = 'У Вас вже є неоплачене замовлення. ' \
                    'Ви зможете використовувати наш сервіс після закриття попереднього замовлення'
end_trip = 'Поїздка була оплачена заздалегіть.'
second_payment_info = 'Виставляємо рахунок клієнту, дочекайтесь оплати'
duty_of_user = 'За вами накопичений борг. ' \
               'Щоб продовжити сплатіть його'
success_duty = 'Ваш борг погашено'
return_money = 'Повернення коштів'
have_duty = 'Ми утримали ваші кошти, так як ви мали заборгованість перед нашим таксі'
return_money_from_system = 'Ваші кошти повернуться протягом доби.\n'
get_money = 'Ми утримали кошти за скасоване замовлення в розмірі'
get_money_cash = 'Та за попередні несплачені замовлення в розмірі'
put_on_bank = 'Та помістили їх на ваш рахунок. Вони будуть враховані при наступному замовлені'
choose_action = "Оберіть необхідну дію"
personal_order_text = "Основна ідея послуги <Персональний водій> полягає в наданні клієнту професійного водія," \
                       " який буде керувати автомобілем за його замовленням та вимогами." \
                       " Ця послуга спрямована на забезпечення комфорту, зручності, безпеки та гнучкості під час пересування." \
                       " Ви можете замовити цю послугу для бізнес-зустрічей, спеціальних подій, довгих поїздок.\n"

personal_terms_text = "Умови даної послуги від Ninja Taxi:\n" \
                      "1. Ціна послуги визначається залежно від тривалості подорожі.\n" \
                      "2. Мінімальний час замовлення 2 години або 50 км.\n" \
                      "3. Вартість послуги 500₴ за годину або 25км поїздки\n" \
                      "4. Тарифікація погодинна\n" \
                      "5. Водія не можна фізично чіпати та примушувати щось робити"
ask_client_accept = "Чи бажаєте продовжити?"
pd_time_text = "Вкажіть період на скільки потрібно авто?"
pd_update_time = "На скільки годин бажаєте подовжити поїздку?"
pd_order_not_accepted = "Замовлення персонального водія не прийнято"
driver_text_personal_end = "Замовлення завершено, спитайте клієнта чи буде він продовжувати, якщо ні завершіть замовлення за допомогою кнопки"
client_text_personal_end = "У вас завершився ліміт часу або кілометраж, бажаєте продовжити?"
client_finish_personal_order = "Замовлення завершиться автоматично після використання сплаченого часу/км."
back_time_route_end = "Замовлення завершується, оберіть потрібну дію"


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
    "\u2705 Змінити тип оплати",
    "\u2705 Сплатити борг",
)
personal_order_buttons = (
    "\u2139 Інформація про послугу",
    "\U0001F4DD Умови послуги",
    "\U0001F9CD Замовити персонального водія"
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

pd_time_buttons = (
    "\U000024F6 години (50км)",
    "\U000024F7 години (75км)",
    "\U000024F8 години (100км)",
    "\U000024F9 годин (125км)",
    "\U000027A1 Продовжити поїздку",
    "\U0001F645 Не продовжувати поїздку",
    "\U000023F9 Завершити зараз",
    "\U000024F5 годину (25км)"
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


def personal_order_info(order):
    time = timezone.localtime(order.order_time).strftime("%Y-%m-%d %H:%M")
    message = f"<u>Замовлення персонального водія {order.pk}:</u>\n" \
              f"<b>Час подачі:{time}</b>\n" \
              f"Адреса посадки: {order.from_address}\n" \
              f"Номер телефону: {order.phone_number}\n" \
              f"Кількість годин: {order.payment_hours}\n" \
              f"Загальна вартість: {order.sum} грн\n"
    if order.info:
        message += f"Коментар: {order.info}"
    return message


def client_order_info(order, time_update=None):
    if order.car_delivery_price:
        message = f"Замовлення оновлено\n" \
                  f"Нова сума замовлення: {order.sum} грн\n"
    elif time_update:
        message = f"Замовлення оновлено\n"
    else:
        message = f"Ваше замовлення {order.pk}:\n"
    message += f"Адреса посадки: {order.from_address}\n" \
               f"Місце прибуття: {order.to_the_address}\n" \
               f"Спосіб оплати: {order.payment_method}\n" \
               f"Номер телефону: {order.phone_number}\n" \
               f"Загальна вартість: {order.sum} грн\n" \
               f"Довжина маршруту: {order.distance_google} км\n"
    if order.info:
        message += f"Коментар: {order.info}\n"
    if order.order_time:
        time = timezone.localtime(order.order_time).strftime("%Y-%m-%d %H:%M")
        message += f"Час подачі:{time}\n"
    return message


def client_personal_info(order):
    time = timezone.localtime(order.order_time).strftime("%Y-%m-%d %H:%M")
    message = f"Ваше замовлення {order.pk}:\n" \
              f"Час подачі:{time}\n" \
              f"Адреса посадки: {order.from_address}\n" \
              f"Номер телефону: {order.phone_number}\n" \
              f"Сплачено: {order.payment_hours}год або " \
              f"{int(order.payment_hours) * int(ParkSettings.get_value('AVERAGE_DISTANCE_PER_HOUR'))}км \n" \
              f"Загальна вартість: {order.sum} грн\n"
    if order.info:
        message += f"Коментар: {order.info}"
    return message


def driver_complete_text(price):
    message = f"Поїздку завершено\n" \
              f"Сума замовлення: {price} грн"
    return message


def driver_duty(price, client=True):
    message_to = "Водій Вам винен: " if client else "Ви винні клієнту: "
    message = f"Поїздку завершено\n{message_to}{price}грн"
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


def small_time_delta(time, delta):
    format_time = (time + timedelta(minutes=delta)).time().strftime('%H:%M')
    message = f'Вкажіть, будь ласка, більш пізній час.\n' \
              f'Мінімальний час для передзамовлення: {format_time}'
    return message


def accept_order(sum, cancel=None):
    message = 'Сплатіть замовлення, щоб розпочати пошук водія:\n' \
              f'Cума замовлення {sum}грн\n'
    if cancel:
        message += 'Або скасуйте замовлення'

    return message


def complete_personal_order(price):
    return f'Замовлення сформоване, сума до сплати {price}грн.'


def update_hours_text(hours):
    return f'Замовлення успішно продовжено на {hours}год (' \
           f'{int(hours)*int(ParkSettings.get_value("AVERAGE_DISTANCE_PER_HOUR"))}км)'


def update_hours_driver_text(hours):
    return f'Кліент продовжив замовлення на {hours}год (' \
           f'{int(hours)*int(ParkSettings.get_value("AVERAGE_DISTANCE_PER_HOUR"))}км)'


def add_hours_text(price):
    return f'Замовлення оновлюється, сума до сплати {price}грн.'


def personal_time_route_end(end_time, route):
    format_time = end_time.time().strftime('%H:%M')
    not_negative_route = 0 if route < 0 else route
    return f'Замовлення завершується в {format_time} або через {not_negative_route}км'

