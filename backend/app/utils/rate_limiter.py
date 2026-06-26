"""
内存中的速率限制器 — 防止暴力破解和滥用
基于 IP 地址和端点进行限制
"""
import time
from typing import Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RateLimitEntry:
    """单个限制条目"""
    count: int
    window_start: float
    first_request_time: float


class RateLimiter:
    """内存中的滑动窗口速率限制器"""

    def __init__(self):
        """初始化限制器"""
        self._requests: Dict[str, RateLimitEntry] = {}

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        检查是否超过限制

        Args:
            identifier: 限制标识符 (e.g., "192.168.1.1:login")
            max_requests: 时间窗口内允许的最大请求数
            window_seconds: 时间窗口大小（秒）

        Returns:
            (allowed, remaining, retry_after)
            - allowed: 是否允许此请求
            - remaining: 时间窗口内剩余的请求数
            - retry_after: 若被限制，建议重试等待时间（秒）
        """
        now = time.time()

        if identifier not in self._requests:
            # 首次请求
            self._requests[identifier] = RateLimitEntry(
                count=1,
                window_start=now,
                first_request_time=now,
            )
            return True, max_requests - 1, 0

        entry = self._requests[identifier]
        time_elapsed = now - entry.window_start

        if time_elapsed >= window_seconds:
            # 旧窗口过期，开始新窗口
            self._requests[identifier] = RateLimitEntry(
                count=1,
                window_start=now,
                first_request_time=now,
            )
            return True, max_requests - 1, 0

        # 在同一个窗口内
        if entry.count < max_requests:
            entry.count += 1
            remaining = max_requests - entry.count
            return True, remaining, 0
        else:
            # 超过限制
            time_until_reset = window_seconds - time_elapsed
            retry_after = max(1, int(time_until_reset))
            return False, 0, retry_after

    def cleanup_expired_entries(self, max_age_seconds: int = 3600) -> int:
        """
        清除过期的限制条目（无活动超过 max_age_seconds）

        Args:
            max_age_seconds: 条目保留的最大时间（默认 1 小时）

        Returns:
            删除的条目数量
        """
        now = time.time()
        expired_keys = [
            key
            for key, entry in self._requests.items()
            if (now - entry.first_request_time) > max_age_seconds
        ]

        for key in expired_keys:
            del self._requests[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, int]:
        """获取当前统计信息"""
        return {
            "tracked_identifiers": len(self._requests),
            "total_entries": sum(entry.count for entry in self._requests.values()),
        }


# 全局单例实例
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """获取全局速率限制器实例"""
    return _rate_limiter


def check_rate_limit_for_endpoint(
    ip_address: str,
    endpoint: str,
) -> Tuple[bool, int, int]:
    """
    便利函数：检查特定端点的速率限制

    Args:
        ip_address: 客户端 IP 地址
        endpoint: 端点名称 (e.g., "login", "register", "password_validate")

    Returns:
        (allowed, remaining, retry_after)
    """
    limiter = get_rate_limiter()
    identifier = f"{ip_address}:{endpoint}"

    # 配置：端点特定的限制
    limits = {
        "login": (10, 900),  # 10 requests per 15 minutes
        "register": (5, 900),  # 5 requests per 15 minutes
        "password_validate": (30, 900),  # 30 requests per 15 minutes
        "change_password": (20, 3600),  # 20 requests per 1 hour
    }

    max_requests, window_seconds = limits.get(endpoint, (100, 3600))

    return limiter.check_rate_limit(identifier, max_requests, window_seconds)
