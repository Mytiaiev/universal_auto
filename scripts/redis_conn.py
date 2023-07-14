import os
import redis

# Create a global Redis instance
redis_instance = redis.Redis.from_url(os.environ["REDIS_URL"])
