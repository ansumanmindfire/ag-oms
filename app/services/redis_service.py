"""Async Redis service class managing hot session memory, cache rehydration, and query answer caching."""

import hashlib
import json
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
from app.config import settings, logger


class RedisService:
    """Async Redis service managing hot chat session memory and query caching."""

    def __init__(self, host: str = settings.REDIS_HOST, port: int = settings.REDIS_PORT):
        self.host = host
        self.port = port
        self._pool: Optional[redis.ConnectionPool] = None

    def get_client(self) -> redis.Redis:
        """Lazily initializes and returns an async Redis client from the connection pool."""
        try:
            if self._pool is None:
                self._pool = redis.ConnectionPool(
                    host=self.host,
                    port=self.port,
                    decode_responses=True,
                    max_connections=20,
                )
            return redis.Redis(connection_pool=self._pool)
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise

    async def close(self) -> None:
        """Closes the Redis connection pool gracefully on application shutdown."""
        try:
            if self._pool is not None:
                await self._pool.disconnect()
                self._pool = None
                logger.info("Redis connection pool disconnected gracefully.")
        except Exception as e:
            logger.warning(f"Error disconnecting Redis pool: {e}")

    # Session Chat Memory

    async def get_session_memory(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Fetches the last `limit` messages from Redis RAM list `session:{session_id}`.

        Args:
            session_id: Unique session identifier.
            limit: Number of recent messages to return (default 10).

        Returns:
            List of message dictionaries with 'role' and 'content'.
        """
        try:
            client = self.get_client()
            key = f"session:{session_id}"
            raw_msgs = await client.lrange(key, -limit, -1)
            return [json.loads(m) for m in raw_msgs]
        except Exception as e:
            logger.warning(f"Error reading session memory from Redis for session '{session_id}': {e}")
            return []

    async def push_session_messages(self, session_id: str, user_msg: str, ai_msg: str) -> None:
        """Appends user and assistant messages to Redis RAM and resets TTL.

        Args:
            session_id: Unique session identifier.
            user_msg: User query text.
            ai_msg: Assistant response text.
        """
        try:
            client = self.get_client()
            key = f"session:{session_id}"
            user_payload = json.dumps({"role": "user", "content": user_msg})
            ai_payload = json.dumps({"role": "assistant", "content": ai_msg})
            await client.rpush(key, user_payload, ai_payload)
            await client.ltrim(key, -10, -1)
            await client.expire(key, settings.REDIS_SESSION_TTL)
        except Exception as e:
            logger.warning(f"Error pushing session messages to Redis for session '{session_id}': {e}")

    async def rehydrate_session_memory(self, session_id: str, messages: List[Dict[str, str]]) -> None:
        """Rehydrates Redis RAM from database messages and sets TTL.

        Args:
            session_id: Unique session identifier.
            messages: List of message dictionaries.
        """
        try:
            if not messages:
                return
            client = self.get_client()
            key = f"session:{session_id}"
            await client.delete(key)
            payloads = [json.dumps({"role": m["role"], "content": m["content"]}) for m in messages]
            await client.rpush(key, *payloads)
            await client.expire(key, settings.REDIS_SESSION_TTL)
            logger.info(f"Rehydrated Redis RAM for session '{session_id}' with {len(messages)} messages.")
        except Exception as e:
            logger.warning(f"Error rehydrating session memory in Redis for session '{session_id}': {e}")

    # Query Caching

    def _get_query_hash(self, context_id: str, question: str) -> str:
        """Generates deterministic MD5 hash for (context_id, question)."""
        raw = f"{context_id}:{question.strip().lower()}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    async def get_cached_answer(self, context_id: str, question: str) -> Optional[Dict[str, Any]]:
        """Checks Redis for a cached response for an exact question.

        Args:
            context_id: Context or Document ID.
            question: User question text.

        Returns:
            Cached answer dictionary or None on miss.
        """
        try:
            client = self.get_client()
            q_hash = self._get_query_hash(context_id, question)
            key = f"query_response:{context_id}:{q_hash}"
            cached_data = await client.get(key)
            if cached_data:
                result = json.loads(cached_data)
                logger.info(f"Redis Cache HIT for question in context '{context_id}'")
                return result
            return None
        except (TypeError, json.JSONDecodeError):
            return None
        except Exception as e:
            logger.warning(f"Error reading answer cache from Redis: {e}")
            return None

    async def set_cached_answer(self, context_id: str, question: str, response_data: Dict[str, Any]) -> None:
        """Caches generated response in Redis with TTL.

        Args:
            context_id: Context or Document ID.
            question: User query text.
            response_data: Response payload.
        """
        try:
            client = self.get_client()
            q_hash = self._get_query_hash(context_id, question)
            key = f"query_response:{context_id}:{q_hash}"
            payload = json.dumps(response_data)
            await client.setex(key, settings.REDIS_CACHE_TTL, payload)
            logger.info(f"Cached answer in Redis for context '{context_id}' (TTL: {settings.REDIS_CACHE_TTL}s)")
        except Exception as e:
            logger.warning(f"Error setting answer cache in Redis: {e}")


redis_service = RedisService()
