import os
import redis
import logging


pool = redis.ConnectionPool.from_url(os.environ["REDIS_URL"], decode_responses=True)
redis_instance = redis.Redis(connection_pool=pool)


def get_logger():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    return logging.getLogger(__name__)
