import requests
from uuid import uuid4


class Portmone():
    def __init__(self, sum, commission=None, **kwargs):
        self.sum = sum
        self.commission = commission
        self.url = 'https://www.portmone.com.ua/gateway/'
        self.login = '' # os.environ["PORTMONE_LOGIN"]
        self.password = '' # os.environ["PORTMONE_PASSWORD"]
        self.payee_id = '1185' # os.environ["PORTMONE_PAYEE_ID"]
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
                "shopOrderNumber": self.data.get('amount', str(uuid4())),
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
        return response

# url = 'https://www.portmone.com.ua/gateway/'
# payload = {
#     "method": "createLinkPayment",
#     "paymentTypes": {
#           "clicktopay": "Y",
#           "createtokenonly": "N",
#           "token": "N",
#           "privat": "Y",
#           "gpay": "Y",
#           "card": "Y"
#     },
#     "payee": {
#           "payeeId": "1185",
#           "login": "",
#           "dt": "",
#           "signature": "",
#           "shopSiteId": ""
#     },
#     "order": {
#           "description": "",
#           "shopOrderNumber": "578970",
#           "billAmount": "44",
#           "attribute1": "",
#           "attribute2": "",
#           "attribute3": "",
#           "attribute4": "",
#           "attribute5": "",
#           "successUrl": "",
#           "failureUrl": "",
#           "preauthFlag": "N",
#           "billCurrency": "UAH",
#           "encoding": ""
#     },
#     "token": {
#          "tokenFlag": "N",
#          "returnToken": "Y",
#          "token": "",
#          "cardMask": "",
#          "otherPaymentMethods": ""
#     },
#     "payer": {
#          "lang": "uk",
#          "emailAddress": "",
#          "showEmail": "N"
#     }
# }

a = Portmone(1, )
b = a.create_link()
print(b)
# response = requests.post(url, json=payload).json()
# print(response['linkPayment'])
            # try:
            #     result: dict = result['result']['linkInvoice']
            #     return result
            # except IndexError:
            #     logger.error(f"Failed to get link")
            #     return None