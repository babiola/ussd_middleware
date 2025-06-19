
import logging
import redis.asyncio as redis
logger = logging.getLogger(__name__)

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Example usage
async def set_cache(key: str, value: str, ttl: int = 300):
    logger.info(f"Setting cache for key: {key} with TTL: {ttl} seconds")
    if not key or not value:
        logger.warning("Key or value is empty, cannot set cache.")
        return
    await redis_client.set(key, value, ex=ttl)

async def get_cache(key: str):
    logger.info(f"Fetching cache for key: {key}")
    if not key:
        logger.warning("Key is empty, cannot fetch cache.")
        return None
    logger.info(f"Attempting to get value for key: {key}")
    return await redis_client.get(key)