import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

main_dir = os.path.dirname(os.getcwd())

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = f"{main_dir}/credentials.json"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('calendar', 'v3', credentials=credentials)
events_result = service.events().list(calendarId='primary', maxResults=10).execute()

event = {
    'summary': 'Тестове замовлення',
    'description': 'замовлення на Паті',
    'start': {
        'dateTime': '2023-07-21T10:00:00',
        'timeZone': 'Europe/Kiev',
    },
    'end': {
        'dateTime': '2023-07-21T11:00:00',
        'timeZone': 'Europe/Kiev',
    },
}

event = service.events().insert(calendarId='primary', body=event).execute()
print(f"Подія '{event['summary']}' була успішно зареєстрована.")
