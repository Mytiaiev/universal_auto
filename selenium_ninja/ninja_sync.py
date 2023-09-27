import requests

from scripts.redis_conn import redis_instance


class NinjaRequest:

    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.redis = redis_instance()

    def get_token(self):
        data = {
            "username": self.user,
            "password": self.password
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post('/api/token-auth/', json=data, headers=headers)

        if response.status_code == 200:
            token = response.json().get('token')
            redis_instance().set(f'token_{self.user}', token, ex=3600)
            return token

    def get_headers(self):
        if redis_instance().exists(f"token_{self.user}"):
            token = redis_instance().get(f"token_{self.user}")
        else:
            token = self.get_token()
        headers = {
            'Authorization': f'Bearer {token}',
        }
        return headers

    def get_vehicles_info(self):
        response = requests.get("/api/vehicle_info/", headers=self.get_headers())
        return response.json()

    def get_reports(self, start: str, end: str):
        response = requests.get(f"/api/reports/{start}/{end}", headers=self.get_headers())
        return response.json()

    def get_drivers_info(self, start: str, end: str):
        response = requests.get(f"/drivers_info/{start}/{end}", headers=self.get_headers())
        return response.json()

    def get_efficiency_info(self, start: str, end: str):
        response = requests.get(f"/car_efficiencies/{start}/{end}", headers=self.get_headers())
        return response.json()
