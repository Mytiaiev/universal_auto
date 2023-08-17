import requests
from decimal import Decimal, ROUND_HALF_UP
from app.models import Vehicle


def get_exchange_rate(currency_code):
    api_url = f'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={currency_code}&json'

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]['rate']
    return None


def convert_to_currency(amount_uah, to_currency):
    usd_rate = get_exchange_rate(to_currency)

    if usd_rate is not None:
        amount_usd = amount_uah / usd_rate
        rounded_value = Decimal(str(amount_usd)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
        return rounded_value, usd_rate
    return None
