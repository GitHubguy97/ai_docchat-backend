import redis

r = redis.Redis(host="localhost", port=6379, db=0)

r.set("test_key", "Hello, Redis!")
value = r.get("test_key")

print(f"value: {value.decode('utf-8')}")

r.setex("temp_key", 10, "This expires in 10 seconds")
print(f"TTL: {r.ttl('temp_key')} seconds")