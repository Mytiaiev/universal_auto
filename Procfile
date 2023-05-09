web: bash ./entrypoint.sh
bot: python3 manage.py runscript bot
gps: python3 manage.py runscript async_gps_server
worker: CREATE_CHROME_INSTANCE=true celery -A auto worker --beat --loglevel=info --without-gossip --pool=solo -Q non_priority
worker2: celery -A auto worker --beat --loglevel=info --without-gossip --pool=solo -Q priority -n priority