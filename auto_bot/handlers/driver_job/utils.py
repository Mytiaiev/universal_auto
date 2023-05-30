import io
from google.cloud import storage
from auto import settings


def save_storage_photo(image, filename):
    image_data = io.BytesIO()
    image.download(out=image_data)
    image_data.seek(0)
    storage_client = storage.Client(credentials=settings.GS_CREDENTIALS)
    bucket = storage_client.bucket(settings.GS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_file(image_data, content_type='image/jpeg')
