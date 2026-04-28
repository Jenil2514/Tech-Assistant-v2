import hashlib
import json
from typing import Any

from app.config.settings import settings

try:
    import redis
except ImportError:
    redis = None


class CacheService:
    def __init__(self):
        self.enabled = bool(settings.CACHE_ENABLED and settings.REDIS_URL and redis)
        self.client = None

        if self.enabled:
            try:
                self.client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
                self.client.ping()
                print("Redis cache enabled")
            except Exception:
                self.enabled = False
                self.client = None

        if not self.enabled:
            if not settings.CACHE_ENABLED:
                print("Redis cache disabled by CACHE_ENABLED=false")
            elif not settings.REDIS_URL:
                print("Redis cache disabled because REDIS_URL is not set")
            elif not redis:
                print("Redis cache disabled because redis package is not installed")
            else:
                print("Redis cache disabled because Redis connection failed")

    def make_key(self, namespace: str, *parts: Any) -> str:
        raw = json.dumps(parts, sort_keys=True, default=str)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"onboardmind:{namespace}:{digest}"

    def get_json(self, key: str):
        if not self.enabled or not self.client:
            return None

        value = self.client.get(key)
        if not value:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def set_json(self, key: str, value, ttl_seconds: int):
        if not self.enabled or not self.client:
            return

        self.client.setex(key, ttl_seconds, json.dumps(value, default=str))

    def list_range(self, key: str, start: int = 0, end: int = -1):
        if not self.enabled or not self.client:
            return []

        return self.client.lrange(key, start, end)

    def list_prepend(self, key: str, value: str, ttl_seconds: int, max_items: int):
        if not self.enabled or not self.client:
            return

        pipe = self.client.pipeline()
        pipe.lpush(key, value)
        pipe.ltrim(key, 0, max_items - 1)
        pipe.expire(key, ttl_seconds)
        pipe.execute()


cache = CacheService()
