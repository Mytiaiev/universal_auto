web: bash ./entrypoint.sh
worker: celery -A auto worker --beat --loglevel=info --pool=solo
