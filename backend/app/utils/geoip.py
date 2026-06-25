import os
from pathlib import Path
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class GeoIPManager:
    def __init__(self):
        self.reader = None
        self.db_path = Path(__file__).parent.parent.parent / "data" / "GeoLite2-City.mmdb"

        if self.db_path.exists():
            try:
                import geoip2.database
                self.reader = geoip2.database.Reader(str(self.db_path))
                logger.info(f"GeoIP database loaded from {self.db_path}")
            except ImportError:
                logger.warning("geoip2 library not installed, GeoIP functionality disabled")
            except Exception as e:
                logger.warning(f"Failed to load GeoIP database: {e}")
        else:
            logger.warning(f"GeoIP database not found at {self.db_path}")

    def get_city_country(self, ip_address: str) -> Tuple[str, str]:
        """
        根据 IP 地址获取城市和国家

        Args:
            ip_address: IP 地址

        Returns:
            (city, country) 元组，如果获取失败返回 ("Unknown", "Unknown")
        """
        if not self.reader or not ip_address or ip_address in ["127.0.0.1", "localhost"]:
            return "Unknown", "Unknown"

        try:
            response = self.reader.city(ip_address)
            city = response.city.name or "Unknown"
            country = response.country.iso_code or "Unknown"
            return city, country
        except Exception as e:
            logger.debug(f"Error looking up IP {ip_address}: {e}")
            return "Unknown", "Unknown"

    def close(self):
        """关闭数据库连接"""
        if self.reader:
            self.reader.close()

# 全局单例
_geoip_manager = None

def get_geoip_manager() -> GeoIPManager:
    global _geoip_manager
    if _geoip_manager is None:
        _geoip_manager = GeoIPManager()
    return _geoip_manager
