import redis
import time


def run():
    r = redis.Redis(host="localhost")
    p = r.publish('code', '5501')

