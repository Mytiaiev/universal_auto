import requests
import logging
import os

logger = logging.getLogger("portmone")


class GatewayError(Exception):
    """Raised when API http request failed."""
    pass


class StatusCodeError(Exception):
    """Raised when API returns non-200 status code."""


class Portmone():
    def __init__(self, sum=None, commission=None, **kwargs):
        self.sum = sum
        self.commission = commission
        self.url = 'https://www.portmone.com.ua/gateway/'
        self.login = os.environ["PORTMONE_LOGIN"]
        self.password = os.environ["PORTMONE_PASSWORD"]
        self.payee_id = os.environ["PORTMONE_PAYEE_ID"]
        self.data = kwargs

    def user_commission(self):
        return self.portmone_commission() - self.commission

    def portmone_commission(self):
        return self.sum - (self.sum * 0.01) - 5

    def get_commission(self):
        if self.commission is None:
            commission = self.portmone_commission()
            return commission
        else:
            commission = self.user_commission()
            return commission

    def response(self, payload):
        while True:
            response = requests.post(self.url, json=payload)
            if response.status_code == 200:
                return response.json()

    def create_link(self):
        payload = {
            "method": "createLinkPayment",
            "paymentTypes": {
                "clicktopay": "Y",
                "createtokenonly": "N",
                "token": "N",
                "privat": "Y",
                "gpay": "Y",
                "card": "Y"
            },
            "payee": {
                "payeeId": self.payee_id,
                "login": self.login,
                "dt": "",
                "signature": "",
                "shopSiteId": ""
            },
            "order": {
                "description": self.data.get('payment_description', ''),
                "shopOrderNumber": self.data.get('order_id'),
                "billAmount": self.sum,
                "attribute1": "",
                "attribute2": "",
                "attribute3": "",
                "attribute4": "",
                "attribute5": "",
                "successUrl": "",
                "failureUrl": "",
                "preauthFlag": "N",
                "billCurrency": "UAH",
                "encoding": ""
            },
            "token": {
                "tokenFlag": "N",
                "returnToken": "Y",
                "token": "",
                "cardMask": "",
                "otherPaymentMethods": ""
            },
            "payer": {
                "lang": "uk",
                "emailAddress": "",
                "showEmail": "N"
            }
        }

        response = self.response(payload)
        return response['linkPayment']

    def checkout_status(self):
        payload = {
        "paymentTypes": {
            "card": "Y",
            "portmone": "Y",
            "token": "N",
            "clicktopay": "Y",
            "createtokenonly": "N"
        },
         "payee": {
            "payeeId": self.payee_id,
            "login": self.login,
            "dt": "",
            "signature": "",
            "shopSiteId": ""
          },
         "order": {
             "description": self.data.get('payment_description', ''),
             "shopOrderNumber": self.data.get('order_id'),
             "billAmount": self.sum,
             "attribute1": "",
             "attribute2": "",
             "attribute3": "",
             "attribute4": "",
             "successUrl": "",
             "failureUrl": "",
             "preauthFlag": "N",
             "preauthConfirm": "",
             "billCurrency": "UAH",
             "expTime": "",
             "encoding": ""
           },
         "token":
           {
             "tokenFlag": "N",
             "returnToken": "Y",
             "token": "",
             "cardMask": "",
             "otherPaymentMethods": ""
           },
         "payer":
           {
             "lang": "uk",
             "emailAddress": "",
             "showEmail": "N"
           }
         }

        response = self.response(payload)
        return response.json()

    def return_amount(self, amount: int, order: str, message: str):
        payload = {
                    "method": "return",
                    "params":
                        {
                            "data":
                                {
                                    "login": self.login,
                                    "password": self.password,
                                    "payeeId": self.payee_id,
                                    "shopOrderNumber": order,
                                    "returnAmount": amount,
                                    "message": message
                                }
                        },
                    "id": "1"
                  }
        response = self.response(payload)
        return response

