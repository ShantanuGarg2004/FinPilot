"""Unit tests for Wave 1 rate-limit core (memory store + policies + keys)."""
from datetime import timezone

from services.rate_limit.keys import build_bucket_key, hash_api_key
from services.rate_limit.memory_store import MemoryRateLimitStore
from services.rate_limit.policies import PolicyRegistry


def test_hash_api_key_is_stable_and_short():
    a = hash_api_key("secret-one")
    b = hash_api_key("secret-one")
    c = hash_api_key("secret-two")
    assert a == b
    assert a != c
    assert len(a) == 16


def test_bucket_key_includes_user_when_requested():
    k1 = build_bucket_key("k", "llm_report")
    k2 = build_bucket_key("k", "llm_report", user_id=7)
    assert k1.endswith(":llm_report")
    assert k2.endswith(":llm_report:u7")
    assert k1 != k2


def test_memory_store_allows_then_denies():
    store = MemoryRateLimitStore()
    r1 = store.incr_and_check("a:llm_report", window_seconds=60, limit=2)
    r2 = store.incr_and_check("a:llm_report", window_seconds=60, limit=2)
    r3 = store.incr_and_check("a:llm_report", window_seconds=60, limit=2)
    assert r1.allowed and r1.hit_count == 1
    assert r2.allowed and r2.hit_count == 2
    assert not r3.allowed and r3.hit_count == 3
    assert r3.retry_after >= 1
    assert r3.reset_at.tzinfo is not None


def test_memory_store_isolates_keys():
    store = MemoryRateLimitStore()
    store.incr_and_check("key-a", 60, 1)
    other = store.incr_and_check("key-b", 60, 1)
    assert other.allowed


def test_policy_options_and_health_exempt():
    pol = PolicyRegistry()
    assert pol.rules_for("OPTIONS", "/api/report/1") == []
    assert pol.rules_for("GET", "/api/health") == []


def test_policy_maps_llm_report_with_per_user_rule():
    pol = PolicyRegistry()
    rules = pol.rules_for("POST", "/api/generate-report")
    assert rules is not None
    assert any(r.route_class == "llm_report" and not r.per_user for r in rules)
    assert any(r.route_class == "llm_report" and r.per_user for r in rules)


def test_policy_maps_read_report():
    pol = PolicyRegistry()
    rules = pol.rules_for("GET", "/api/report/42")
    assert len(rules) == 1
    assert rules[0].route_class == "read_report"
