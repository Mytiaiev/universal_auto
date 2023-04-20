web: bash ./entrypoint.sh
bot: python3 manage.py runscript bot
gps: python3 manage.py runscript async_gps_server
worker: celery -A auto worker --beat --loglevel=info --without-gossip --pool=threads