import requests
from decimal import Decimal, ROUND_HALF_UP

from selenium_ninja.synchronizer import AuthenticationError


def convert_to_currency(amount_uah, currency_code):
    api_url = f'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={currency_code}&json'

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        amount_usd = amount_uah / data[0]['rate']
        rounded_value = Decimal(str(amount_usd)).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
        return rounded_value, data[0]['rate']
    else:
        raise AuthenticationError(response.json())
