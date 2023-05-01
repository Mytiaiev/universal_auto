from app.models import ParkSettings

FROM_ADDRESS, TO_THE_ADDRESS, COMMENT, TIME_ORDER, START_TIME_ORDER = range(1, 6)
U_NAME, U_SECOND_NAME, U_EMAIL, FIRST_ADDRESS_CHECK, SECOND_ADDRESS_CHECK = range(6, 11)
LOCATION_WRONG = "Місце посадки - невірне"
LOCATION_CORRECT = "Місце посадки - вірне"
NOT_CORRECT_ADDRESS = 'Немає вірної адреси'
CONTINUE = 'Продовжити замовлення'
CANCEL = 'Скасувати замовлення'
TOMORROW = "Замовити на завтра"
TODAY = "Замовити на інший час"

PAYCARD = 'Картка'
CASH = 'Готівка'

already_ordered = "У вас вже є активне замовлення бажаєте замовити ще одне авто?"
price_info = f"Ціна поїздки в місті {ParkSettings.get_value('TARIFF_IN_THE_CITY', 15)}грн/км\n" +\
             f"Ціна поїздки за містом {ParkSettings.get_value('TARIFF_OUTSIDE_THE_CITY', 30)}грн/км"
AVERAGE_DISTANCE_PER_HOUR, COST_PER_KM = int(f"{ParkSettings.get_value('AVERAGE_DISTANCE_PER_HOUR', 25)}"), int(
            f"{ParkSettings.get_value('COST_PER_KM', 20)}")
continue_ask = 'Чи бажаєте ви продовжити?'
timeorder_ask = "Бажаєте замовити на зараз чи на певний час?"
canceled_order_text = 'Гарного дня. Дякуємо, що скористались нашими послугами'
choose_address_text = "Оберіть вашу адресу. Інакше натисніть - 'Немає вірної адреси'" \
                      " та вкажіть більш детально вашу адресу"
wrong_address_request = 'Нам не вдалось обробити вашу адресу, спробуйте ще раз'
order_customer_text = 'Коли водій буде на місці, ви отримаєте повідомлення.' \
                      ' На карті нижче ви можете спостерігати, де зараз ваш водій'
select_car_error = 'Щоб приймати замовлення, скористайтесь спочатку командой /status,' \
                   ' щоб позначити на якому ви сьогодні авто'
