"""Tests for disk-based caching."""

from __future__ import annotations

import json
import threading
import time

import pytest

from open_web_retrieval.cache import CacheStats, DiskCache


@pytest.fixture
def cache(tmp_path):
    """Fresh disk cache in a temp directory."""
    return DiskCache(tmp_path / "cache", default_ttl_seconds=60)


class TestDiskCache:
    def test_set_and_get(self, cache):
        cache.set("key1", {"data": "value"})
        result = cache.get("key1")
        assert result == {"data": "value"}

    def test_get_missing_returns_none(self, cache):
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self, cache):
        cache.set("key1", "value", ttl=0)
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_clear(self, cache):
        cache.set("a", 1)
        cache.set("b", 2)
        count = cache.clear()
        assert count == 2
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_evict_expired(self, cache):
        cache.set("fresh", "value", ttl=3600)
        cache.set("stale", "value", ttl=0)
        time.sleep(0.01)
        evicted = cache.evict_expired()
        assert evicted == 1
        assert cache.get("fresh") == "value"

    def test_overwrite(self, cache):
        cache.set("key", "v1")
        cache.set("key", "v2")
        assert cache.get("key") == "v2"

    def test_complex_values(self, cache):
        value = {"list": [1, 2, 3], "nested": {"a": True}}
        cache.set("complex", value)
        assert cache.get("complex") == value

    def test_deterministic_key_path(self, cache):
        """Same key always maps to same file."""
        path1 = cache._key_path("test")
        path2 = cache._key_path("test")
        assert path1 == path2

    def test_different_keys_different_paths(self, cache):
        path1 = cache._key_path("key_a")
        path2 = cache._key_path("key_b")
        assert path1 != path2


class TestFileLocking:
    def test_file_locking_prevents_corruption(self, tmp_path):
        """Two threads writing the same key should not produce corrupt JSON."""
        cache = DiskCache(tmp_path / "lock_cache", default_ttl_seconds=60)
        errors: list[str] = []
        iterations = 50

        def writer(thread_id: int) -> None:
            for i in range(iterations):
                cache.set("shared_key", {"thread": thread_id, "iteration": i})

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # The file must exist and contain valid JSON after concurrent writes
        path = cache._key_path("shared_key")
        assert path.exists(), "Cache file should exist after concurrent writes"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            assert "value" in data
            assert "thread" in data["value"]
        except json.JSONDecodeError as exc:
            errors.append(f"Corrupt JSON after concurrent writes: {exc}")

        assert not errors, "\n".join(errors)


class TestMaxEntriesEviction:
    def test_max_entries_eviction(self, tmp_path):
        """Writing more entries than max_entries evicts the oldest."""
        cache = DiskCache(tmp_path / "evict_cache", max_entries=3)

        # Write 5 entries with small sleeps so mtimes differ
        for i in range(5):
            cache.set(f"key_{i}", f"value_{i}")
            time.sleep(0.02)

        # Only 3 should remain
        remaining = list(cache.cache_dir.glob("*.json"))
        assert len(remaining) == 3

        # The newest 3 entries should survive (key_2, key_3, key_4)
        assert cache.get("key_2") == "value_2"
        assert cache.get("key_3") == "value_3"
        assert cache.get("key_4") == "value_4"

        # The oldest 2 should have been evicted
        # (get returns None, but we need to check without incrementing miss counter further)
        path_0 = cache._key_path("key_0")
        path_1 = cache._key_path("key_1")
        assert not path_0.exists()
        assert not path_1.exists()

    def test_eviction_counter_increments(self, tmp_path):
        """Eviction counter tracks how many entries were evicted."""
        cache = DiskCache(tmp_path / "evict_counter", max_entries=2)
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache._evictions == 0

        cache.set("c", 3)  # Should evict 1
        assert cache._evictions == 1


class TestCacheStats:
    def test_cache_stats(self, tmp_path):
        """Verify hits/misses/evictions counters in stats()."""
        cache = DiskCache(tmp_path / "stats_cache", max_entries=3)

        # Misses
        cache.get("missing1")
        cache.get("missing2")

        # Hits
        cache.set("present", "value")
        cache.get("present")
        cache.get("present")

        s = cache.stats()
        assert s.misses == 2
        assert s.hits == 2
        assert s.entries == 1
        assert s.evictions == 0

    def test_cache_stats_size(self, tmp_path):
        """Verify size_bytes is approximately correct."""
        cache = DiskCache(tmp_path / "size_cache")

        # Write a known payload
        cache.set("size_key", "x" * 100)

        s = cache.stats()
        assert s.entries == 1
        # The envelope adds key, stored_at, ttl around the value.
        # The 100-char value plus envelope metadata should be > 100 bytes
        # and < 500 bytes (generous upper bound).
        assert s.size_bytes > 100
        assert s.size_bytes < 500

        # Verify it matches the actual file size
        path = cache._key_path("size_key")
        assert s.size_bytes == path.stat().st_size

    def test_cache_stats_with_evictions(self, tmp_path):
        """Stats reflect eviction count after LRU eviction."""
        cache = DiskCache(tmp_path / "evict_stats", max_entries=2)
        cache.set("a", 1)
        time.sleep(0.02)
        cache.set("b", 2)
        time.sleep(0.02)
        cache.set("c", 3)  # evicts 1

        s = cache.stats()
        assert s.entries == 2
        assert s.evictions == 1

    def test_stats_returns_dataclass(self, tmp_path):
        """CacheStats is a proper dataclass."""
        cache = DiskCache(tmp_path / "dc_cache")
        s = cache.stats()
        assert isinstance(s, CacheStats)
