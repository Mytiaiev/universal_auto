import io
from datetime import datetime

from google.cloud import storage
from auto import settings


def validate_date(date_str):
    try:
        check_date = datetime.strptime(date_str, '%d.%m.%Y')
        today = datetime.today()
        future_date = datetime(2077, 12, 31)
        if check_date < today:
            return False
        elif check_date > future_date:
            return False
        else:
            return True
    except ValueError:
        return False


def save_storage_photo(image, filename):
    image_data = io.BytesIO()
    image.download(out=image_data)
    image_data.seek(0)
    storage_client = storage.Client(credentials=settings.GS_CREDENTIALS)
    bucket = storage_client.bucket(settings.GS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_file(image_data, content_type='image/jpeg')
