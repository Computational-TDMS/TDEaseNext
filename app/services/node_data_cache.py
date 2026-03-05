"""
Node Data Cache Service
Implements aggressive caching strategy for node data with LRU cache and invalidation
"""

import logging
import threading
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple
import time

logger = logging.getLogger(__name__)


class NodeDataCache:
    """
    LRU cache for node data with aggressive caching strategy

    Features:
    - LRU cache with configurable max size
    - TTL-based expiration
    - Execution-based invalidation
    - Thread-safe operations
    """

    def __init__(self, max_size: int = 128, default_ttl: int = 3600):
        """
        Initialize cache

        Args:
            max_size: Maximum number of cached entries
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: "OrderedDict[str, Tuple[Any, float]]" = OrderedDict()
        self._lock = threading.RLock()

    def _generate_key(self, execution_id: str, node_id: str, port_id: Optional[str] = None) -> str:
        """Generate cache key"""
        if port_id:
            return f"{execution_id}:{node_id}:{port_id}"
        return f"{execution_id}:{node_id}"

    def get(self, execution_id: str, node_id: str, port_id: Optional[str] = None) -> Optional[Any]:
        """
        Get cached data

        Args:
            execution_id: Execution ID
            node_id: Node ID
            port_id: Optional port ID

        Returns:
            Cached data or None if not found/expired
        """
        key = self._generate_key(execution_id, node_id, port_id)

        with self._lock:
            if key not in self._cache:
                return None

            data, timestamp = self._cache[key]
            age = time.time() - timestamp

            # Check if expired
            if age > self.default_ttl:
                del self._cache[key]
                logger.debug(f"Cache expired for key: {key}")
                return None

            # Move key to end to track recency for LRU eviction.
            self._cache.move_to_end(key)
            logger.debug(f"Cache hit for key: {key} (age: {age:.1f}s)")
            return data

    def set(self, execution_id: str, node_id: str, data: Any, port_id: Optional[str] = None) -> None:
        """
        Set cached data

        Args:
            execution_id: Execution ID
            node_id: Node ID
            data: Data to cache
            port_id: Optional port ID
        """
        key = self._generate_key(execution_id, node_id, port_id)

        with self._lock:
            if key in self._cache:
                # Preserve LRU ordering for updates.
                self._cache.move_to_end(key)
            elif len(self._cache) >= self.max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                logger.debug(f"Evicted cache entry: {oldest_key}")

            self._cache[key] = (data, time.time())
            logger.debug(f"Cached data for key: {key}")

    def invalidate_execution(self, execution_id: str) -> int:
        """
        Invalidate all cache entries for an execution

        Args:
            execution_id: Execution ID

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = [k for k in self._cache if k.startswith(f"{execution_id}:")]
            for key in keys_to_remove:
                del self._cache[key]

            count = len(keys_to_remove)
            if count > 0:
                logger.info(f"Invalidated {count} cache entries for execution: {execution_id}")
            return count

    def invalidate_node(self, execution_id: str, node_id: str) -> int:
        """
        Invalidate cache entries for a specific node

        Args:
            execution_id: Execution ID
            node_id: Node ID

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            prefix = f"{execution_id}:{node_id}"
            keys_to_remove = [k for k in self._cache if k.startswith(prefix)]

            for key in keys_to_remove:
                del self._cache[key]

            count = len(keys_to_remove)
            if count > 0:
                logger.debug(f"Invalidated {count} cache entries for node: {prefix}")
            return count

    def clear(self) -> int:
        """
        Clear all cache entries

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared {count} cache entries")
            return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Cache stats dictionary
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl": self.default_ttl,
                "keys": list(self._cache.keys())
            }


# Global cache instance
_cache: Optional[NodeDataCache] = None


def get_node_data_cache() -> NodeDataCache:
    """Get global node data cache instance"""
    global _cache
    if _cache is None:
        _cache = NodeDataCache()
    return _cache
