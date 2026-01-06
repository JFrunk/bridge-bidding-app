import redis
import os

class RedisClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
            cls._instance = redis.from_url(redis_url)
        return cls._instance

def get_redis_client():
    """Returns a singleton instance of the Redis client."""
    return RedisClient.get_instance()
