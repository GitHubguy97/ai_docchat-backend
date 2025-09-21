from app.config import settings
from app.redis_client import redis_client

def check_rate_limit(ip_address: str, limit: int = 10, ttl: int = 300) -> dict:
    """
    Check and enforce rate limiting for an IP address.
    
    Args:
        ip_address: The client's IP address
        limit: Maximum requests per time window (default: 60)
        ttl: Time window in seconds (default: 3600 = 1 hour)
    
    Returns:
        dict: {
            "allowed": bool,
            "remaining": int,
            "reset_time": int (timestamp)
        }
    """
    key = f"rate_limit:{ip_address}"
    
    # Lua script for atomic rate limiting
    lua_script = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local ttl = tonumber(ARGV[2])
    
    local current = redis.call('GET', key)
    if current == false then
        redis.call('SETEX', key, ttl, limit - 1)
        return {limit - 1, 1}  -- {remaining, allowed}
    else
        local count = tonumber(current)
        if count > 0 then
            redis.call('DECR', key)
            return {count - 1, 1}  -- {remaining, allowed}
        else
            return {0, 0}  -- {remaining, denied}
        end
    end
    """
    
    try:
        result = redis_client.eval(lua_script, 1, key, limit, ttl)
        remaining, allowed = result
        
        return {
            "allowed": bool(allowed),
            "remaining": int(remaining),
            "reset_time": int(redis_client.ttl(key))
        }
    except Exception as e:
        print(f"Rate limiting error: {e}")
        # Fail open - allow request if Redis is down
        return {
            "allowed": True,
            "remaining": limit - 1,
            "reset_time": 0
        }