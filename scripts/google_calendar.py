import os
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from auto.settings import BASE_DIR


class GoogleCalendar:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    FILE_PATH = "credentials.json"

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
                                os.path.join(BASE_DIR, self.FILE_PATH), scopes=self.SCOPES)
        self.service = build('calendar', 'v3', credentials=credentials)

    def get_calendar_list(self):
        return self.service.calendarList().list().execute()

    @staticmethod
    def add_permission(email):
        permission = {
            'role': 'writer',  # Adjust the role as needed (e.g., 'reader', 'owner')
            'scope': {
                'type': 'user',
                'value': email,
            },
        }
        return permission

    def create_calendar(self, calendar_name="Розклад водіїв"):
        calendar = {
            'summary': calendar_name,
            'timeZone': 'Europe/Kiev',
        }

        created_calendar = self.service.calendars().insert(body=calendar).execute()
        return created_calendar['id']

    def add_calendar(self, calendar_id):
        calendar_list = {
            "id": calendar_id
        }
        return self.service.calendarList().insert(body=calendar_list).execute()

    def delete_calendar(self, calendar_id):
        calendar_list = {
            "id": calendar_id
        }
        return self.service.calendarList().delete(body=calendar_list).execute()

    def create_event(self, summary, description, s_date, e_date,
                     calendar_id, driver1: dict = None, driver2: dict = None):
        """
            Create event in Google Calendar
        summary: str
        description:str
        s_date: datetime
        e_date datetime
        calendar_id: str
        rv: str
        ex. date : '2023-07-31T10:00:00'
        """

        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': s_date,
                'timeZone': 'Europe/Kiev',
            },
            'end': {
                'dateTime': e_date,
                'timeZone': 'Europe/Kiev',
            },
            'attendees': [
                driver1,
                driver2,
            ],
        }
        event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
        return f"Подія '{event}' була успішно зареєстрована."

    def get_list_events(self, calendar_id, start, end):
        return self.service.events().list(calendarId=calendar_id,
                                          timeMin=start.isoformat(),
                                          timeMax=end.isoformat(),
                                          singleEvents=True,
                                          orderBy='startTime').execute()


def datetime_with_timezone(datetime_):
    """'2023-07-24 15:45:00+00:00' -> '2023-07-24T15:45:00'
    """
    input_datetime_str = datetime_
    input_datetime = datetime.fromisoformat(input_datetime_str.replace('Z', ''))
    output_datetime_str = input_datetime.strftime('%Y-%m-%dT%H:%M:%S')

    return output_datetime_str
