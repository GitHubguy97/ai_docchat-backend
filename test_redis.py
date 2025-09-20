import redis
from app.config import settings

r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db)

r.set("test_key", "Hello, Redis!")
value = r.get("test_key")

print(f"value: {value.decode('utf-8')}")

r.setex("temp_key", 10, "This expires in 10 seconds")
print(f"TTL: {r.ttl('temp_key')} seconds")