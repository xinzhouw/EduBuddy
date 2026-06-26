"""
速率限制器单元测试
"""
import pytest
import time
from app.utils.rate_limiter import RateLimiter, check_rate_limit_for_endpoint


class TestRateLimiter:
    """测试内存中的速率限制器"""

    def test_first_request_allowed(self):
        """首次请求总是被允许"""
        limiter = RateLimiter()
        allowed, remaining, retry_after = limiter.check_rate_limit("test:1", max_requests=5, window_seconds=60)
        assert allowed is True
        assert remaining == 4
        assert retry_after == 0

    def test_multiple_requests_within_limit(self):
        """在限制内的多个请求被允许"""
        limiter = RateLimiter()
        for i in range(5):
            allowed, remaining, retry_after = limiter.check_rate_limit("test:1", max_requests=5, window_seconds=60)
            assert allowed is True
            assert remaining == 4 - i
            assert retry_after == 0

    def test_exceeds_limit_returns_429(self):
        """超过限制的请求被拒绝"""
        limiter = RateLimiter()
        # Make 5 allowed requests
        for i in range(5):
            limiter.check_rate_limit("test:1", max_requests=5, window_seconds=60)
        # 6th request should be blocked
        allowed, remaining, retry_after = limiter.check_rate_limit("test:1", max_requests=5, window_seconds=60)
        assert allowed is False
        assert remaining == 0
        assert retry_after > 0

    def test_separate_identifiers_tracked_separately(self):
        """不同的标识符独立追踪"""
        limiter = RateLimiter()
        # Max out identifier 1
        for i in range(5):
            limiter.check_rate_limit("test:1", max_requests=5, window_seconds=60)

        # Identifier 2 should still have quota
        allowed, remaining, retry_after = limiter.check_rate_limit("test:2", max_requests=5, window_seconds=60)
        assert allowed is True
        assert remaining == 4

    def test_cleanup_expired_entries(self):
        """清理过期的条目"""
        limiter = RateLimiter()
        limiter.check_rate_limit("test:1", max_requests=5, window_seconds=60)
        limiter.check_rate_limit("test:2", max_requests=5, window_seconds=60)

        stats_before = limiter.get_stats()
        assert stats_before["tracked_identifiers"] == 2

        # Cleanup with 0 second threshold (all entries are "expired")
        deleted = limiter.cleanup_expired_entries(max_age_seconds=0)
        assert deleted == 2

        stats_after = limiter.get_stats()
        assert stats_after["tracked_identifiers"] == 0

    def test_window_reset_after_expiry(self):
        """时间窗口过期后重置"""
        limiter = RateLimiter()
        # Max out requests in first window
        for i in range(5):
            limiter.check_rate_limit("test:1", max_requests=5, window_seconds=1)

        # Should be blocked
        allowed, _, _ = limiter.check_rate_limit("test:1", max_requests=5, window_seconds=1)
        assert allowed is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        allowed, remaining, _ = limiter.check_rate_limit("test:1", max_requests=5, window_seconds=1)
        assert allowed is True
        assert remaining == 4

    def test_endpoint_specific_limits(self):
        """端点特定的限制配置"""
        # Login: 10 per 15min
        allowed, _, _ = check_rate_limit_for_endpoint("192.168.1.1", "login")
        assert allowed is True

        # Register: 5 per 15min
        allowed, _, _ = check_rate_limit_for_endpoint("192.168.1.1", "register")
        assert allowed is True

        # Password validate: 30 per 15min
        allowed, _, _ = check_rate_limit_for_endpoint("192.168.1.1", "password_validate")
        assert allowed is True
