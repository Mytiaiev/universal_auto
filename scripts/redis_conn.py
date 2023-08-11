import os
import redis
import logging


def redis_instance():
    return redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def get_logger():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    return logging.getLogger(__name__)
