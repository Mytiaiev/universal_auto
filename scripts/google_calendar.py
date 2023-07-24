import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from auto.settings import BASE_DIR


def create_connect():
    # main_dir = os.path.dirname(os.getcwd())
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    # SERVICE_ACCOUNT_FILE = f"{main_dir}/credentials.json"

    credentials = service_account.Credentials.from_service_account_file(
                            os.path.join(BASE_DIR, "credentials.json"), scopes=SCOPES)

    service = build('calendar', 'v3', credentials=credentials)
    return service


def create_event(summary, description, s_date, e_date, calendar_id):
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
    service = create_connect()
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
    }
    print(event)
    event = service.events().insert(calendarId=calendar_id, body=event).execute()
    return f"Подія '{event['summary']}' {event['start']} була успішно зареєстрована."


def create_calendar(summary, description, service=create_connect()):
    """     Create calendar
    summary: str Calendar name
    description: str Description calendar
    rv: str Id calendar
    """

    calendar = {
        'summary': summary,
        'description': description
    }
    created_calendar = service.calendars().insert(body=calendar).execute()
    calendar_id = created_calendar['id']
    return calendar_id


def datetime_with_timezone(datetime):
    """'2023-07-24 15:45:00+00:00' -> '2023-07-24T15:45:00'
    """

