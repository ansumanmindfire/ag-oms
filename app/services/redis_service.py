"""Synchronous Redis service class managing hot session memory, cache rehydration, and fast lookups."""

import json
from typing import Any, Dict, List, Optional
import redis
from app.config import settings, logger


class RedisService:
    """Synchronous Redis service managing hot chat session memory and query caching."""

    def __init__(self, host: str = settings.REDIS_HOST, port: int = settings.REDIS_PORT):
        self.host = host
        self.port = port
        self._pool: Optional[redis.ConnectionPool] = None

    def get_client(self) -> Optional[redis.Redis]:
        """Lazily initializes and returns a synchronous Redis client from the connection pool."""
        try:
            if self._pool is None:
                self._pool = redis.ConnectionPool(
                    host=self.host,
                    port=self.port,
                    decode_responses=True,
                    max_connections=20,
                    socket_connect_timeout=1.0,
                    socket_timeout=2.0,
                )
            client = redis.Redis(connection_pool=self._pool)
            # Lightweight ping test
            client.ping()
            return client
        except Exception as e:
            logger.debug(f"Redis is unavailable at {self.host}:{self.port} ({e}). Falling back to primary database.")
            return None

    def close(self) -> None:
        """Closes the Redis connection pool gracefully on application shutdown."""
        try:
            if self._pool is not None:
                self._pool.disconnect()
                self._pool = None
                logger.info("Redis connection pool disconnected gracefully.")
        except Exception as e:
            logger.warning(f"Error disconnecting Redis pool: {e}")

    # Session Chat Memory

    def get_session_memory(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Fetches the last `limit` messages from Redis RAM list `session:{session_id}`.

        Args:
            session_id: Unique session identifier.
            limit: Number of recent messages to return (default 10).

        Returns:
            List of message dictionaries with 'sender' and 'content'.
        """
        try:
            client = self.get_client()
            if client is None:
                return []
            key = f"session:{session_id}"
            raw_msgs = client.lrange(key, -limit, -1)
            return [json.loads(m) for m in raw_msgs]
        except Exception as e:
            logger.debug(f"Could not read session memory from Redis for session '{session_id}': {e}")
            return []

    def push_session_messages(self, session_id: str, user_msg: str, ai_msg: str) -> None:
        """Appends user and assistant messages to Redis RAM and resets TTL.

        Args:
            session_id: Unique session identifier.
            user_msg: User query text.
            ai_msg: Assistant response text.
        """
        try:
            client = self.get_client()
            if client is None:
                return
            key = f"session:{session_id}"
            user_payload = json.dumps({"sender": "user", "content": user_msg})
            ai_payload = json.dumps({"sender": "ai", "content": ai_msg})
            client.rpush(key, user_payload, ai_payload)
            client.ltrim(key, -20, -1)
            client.expire(key, settings.REDIS_SESSION_TTL)
        except Exception as e:
            logger.debug(f"Could not push session messages to Redis for session '{session_id}': {e}")

    def rehydrate_session_memory(self, session_id: str, messages: List[Dict[str, str]]) -> None:
        """Rehydrates Redis RAM from database messages and sets TTL.

        Args:
            session_id: Unique session identifier.
            messages: List of message dictionaries with 'sender' and 'content'.
        """
        try:
            if not messages:
                return
            client = self.get_client()
            if client is None:
                return
            key = f"session:{session_id}"
            client.delete(key)
            payloads = [json.dumps({"sender": m["sender"], "content": m["content"]}) for m in messages]
            client.rpush(key, *payloads)
            client.expire(key, settings.REDIS_SESSION_TTL)
            logger.info(f"Rehydrated Redis RAM for session '{session_id}' with {len(messages)} messages.")
        except Exception as e:
            logger.debug(f"Could not rehydrate session memory in Redis for session '{session_id}': {e}")


# Global Redis service instance
redis_service = RedisService()
