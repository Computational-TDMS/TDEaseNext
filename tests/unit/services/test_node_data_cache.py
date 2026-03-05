"""
Unit tests for NodeDataCache service
"""
import pytest
import time
import threading
from app.services.node_data_cache import NodeDataCache, get_node_data_cache


class TestNodeDataCacheBasics:
    """Test basic cache operations"""

    @pytest.fixture
    def cache(self):
        """Fresh cache instance for each test"""
        return NodeDataCache(max_size=5, default_ttl=1)

    def test_get_cache_miss(self, cache):
        """Test get returns None for non-existent key"""
        result = cache.get("exec1", "node1")
        assert result is None

    def test_set_and_get(self, cache):
        """Test set and get basic operation"""
        data = {"key": "value", "numbers": [1, 2, 3]}
        cache.set("exec1", "node1", data)
        result = cache.get("exec1", "node1")
        assert result == data

    def test_get_with_port_id(self, cache):
        """Test cache key includes port_id"""
        data1 = {"port": "output1", "values": [1, 2]}
        data2 = {"port": "output2", "values": [3, 4]}

        cache.set("exec1", "node1", data1, port_id="output1")
        cache.set("exec1", "node1", data2, port_id="output2")

        assert cache.get("exec1", "node1", "output1") == data1
        assert cache.get("exec1", "node1", "output2") == data2
        assert cache.get("exec1", "node1") is None  # No port_id

    def test_update_existing_entry(self, cache):
        """Test updating existing cache entry"""
        cache.set("exec1", "node1", {"version": 1})
        cache.set("exec1", "node1", {"version": 2})

        result = cache.get("exec1", "node1")
        assert result == {"version": 2}


class TestNodeDataCacheTTL:
    """Test TTL-based expiration"""

    @pytest.fixture
    def cache(self):
        """Cache with short TTL for testing"""
        return NodeDataCache(max_size=10, default_ttl=0.5)

    def test_ttl_expiration(self, cache):
        """Test cache entries expire after TTL"""
        cache.set("exec1", "node1", {"data": "test"})
        time.sleep(0.6)  # Wait for TTL to expire

        result = cache.get("exec1", "node1")
        assert result is None

    def test_ttl_not_expired(self, cache):
        """Test cache entries don't expire before TTL"""
        cache.set("exec1", "node1", {"data": "test"})
        time.sleep(0.3)  # Less than TTL

        result = cache.get("exec1", "node1")
        assert result == {"data": "test"}


class TestNodeDataCacheLRU:
    """Test LRU eviction"""

    @pytest.fixture
    def cache(self):
        """Small cache for testing eviction"""
        return NodeDataCache(max_size=3, default_ttl=3600)

    def test_lru_eviction_when_full(self, cache):
        """Test LRU eviction when cache reaches max size"""
        # Fill cache to max_size
        for i in range(3):
            cache.set(f"exec{i}", f"node{i}", {"data": i})

        # Add one more - should evict oldest (exec0)
        cache.set("exec3", "node3", {"data": 3})

        # Oldest entry should be evicted
        assert cache.get("exec0", "node0") is None

        # Other entries should still exist
        assert cache.get("exec1", "node1") == {"data": 1}
        assert cache.get("exec2", "node2") == {"data": 2}
        assert cache.get("exec3", "node3") == {"data": 3}

    def test_lru_access_refreshes_recency(self, cache):
        """Most recently accessed entries should not be evicted first."""
        cache.set("exec0", "node0", {"data": 0})
        cache.set("exec1", "node1", {"data": 1})
        cache.set("exec2", "node2", {"data": 2})

        assert cache.get("exec0", "node0") == {"data": 0}
        cache.set("exec3", "node3", {"data": 3})

        assert cache.get("exec1", "node1") is None
        assert cache.get("exec0", "node0") == {"data": 0}


class TestNodeDataCacheInvalidation:
    """Test cache invalidation"""

    @pytest.fixture
    def cache(self):
        """Pre-populated cache"""
        cache = NodeDataCache(max_size=10, default_ttl=3600)
        cache.set("exec1", "node1", {"data": "1"})
        cache.set("exec1", "node2", {"data": "2"})
        cache.set("exec1", "node1", {"data": "3"}, port_id="output1")
        cache.set("exec2", "node1", {"data": "4"})
        return cache

    def test_invalidate_execution(self, cache):
        """Test invalidating all entries for an execution"""
        count = cache.invalidate_execution("exec1")

        assert count == 3  # exec1:node1, exec1:node2, exec1:node1:output1
        assert cache.get("exec1", "node1") is None
        assert cache.get("exec1", "node2") is None
        assert cache.get("exec1", "node1", "output1") is None
        assert cache.get("exec2", "node1") == {"data": "4"}  # Unaffected

    def test_invalidate_node(self, cache):
        """Test invalidating entries for a specific node"""
        count = cache.invalidate_node("exec1", "node1")

        assert count == 2  # exec1:node1, exec1:node1:output1
        assert cache.get("exec1", "node1") is None
        assert cache.get("exec1", "node1", "output1") is None
        assert cache.get("exec1", "node2") == {"data": "2"}  # Unaffected
        assert cache.get("exec2", "node1") == {"data": "4"}  # Unaffected

    def test_clear(self, cache):
        """Test clearing all cache entries"""
        count = cache.clear()

        assert count == 4
        assert cache.get("exec1", "node1") is None
        assert cache.get("exec2", "node1") is None


class TestNodeDataCacheStats:
    """Test cache statistics"""

    def test_get_stats(self):
        """Test getting cache statistics"""
        cache = NodeDataCache(max_size=10, default_ttl=3600)
        cache.set("exec1", "node1", {"data": "1"})
        cache.set("exec2", "node2", {"data": "2"})

        stats = cache.get_stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 10
        assert stats["ttl"] == 3600
        assert "exec1:node1" in stats["keys"]
        assert "exec2:node2" in stats["keys"]


class TestGlobalCacheInstance:
    """Test global cache instance"""

    def test_get_node_data_cache_singleton(self):
        """Test that get_node_data_cache returns singleton"""
        cache1 = get_node_data_cache()
        cache2 = get_node_data_cache()

        assert cache1 is cache2

    def test_global_cache_persistence(self):
        """Test that global cache persists across calls"""
        cache = get_node_data_cache()
        cache.clear()  # Start fresh

        cache.set("exec1", "node1", {"data": "test"})

        cache2 = get_node_data_cache()
        result = cache2.get("exec1", "node1")

        assert result == {"data": "test"}
