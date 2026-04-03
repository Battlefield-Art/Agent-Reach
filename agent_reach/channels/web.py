# -*- coding: utf-8 -*-
"""Web — any URL via tiered fetch strategy.

- Fast path: Jina Reader (default, no browser)
- Fallback: Scrapling Fetcher (stealthy headers, lightweight)
- Stealth path: Scrapling StealthyFetcher (Cloudflare bypass, headless browser)
"""

import urllib.request
from typing import Tuple
from .base import Channel

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# UAE government portals that always require stealth mode
_UAE_GOV_DOMAINS = {
    "mohre.gov.ae",
    "mohre.com",
    "www.mohre.gov.ae",
    "www.mohre.com",
    "tax.gov.ae",
    "www.tax.gov.ae",  # FTA - Federal Tax Authority
    "ded.ae",
    "www.ded.ae",  # Dubai Economy
    "dubaided.gov.ae",
    "www.dubaided.gov.ae",
    "adbc.gov.ae",
    "www.adbc.gov.ae",  # Abu Dhabi Business Center
    "shams.ae",
    "www.shams.ae",  # Sharjah Media City
}


def _is_uae_gov_portal(url: str) -> bool:
    """Check if URL belongs to UAE government portals that require stealth."""
    url_lower = url.lower()
    for domain in _UAE_GOV_DOMAINS:
        if domain in url_lower:
            return True
    return False


def _has_scrapling() -> bool:
    """Check if scrapling is installed."""
    try:
        import scrapling  # noqa: F401
        return True
    except ImportError:
        return False


def _has_stealth_fetcher() -> bool:
    """Check if Scrapling StealthyFetcher is available (browser installed)."""
    try:
        from scrapling.fetcher import StealthyFetcher

        # Try to instantiate to verify browser binaries are present
        fetcher = StealthyFetcher()
        return True
    except Exception:
        return False


class WebChannel(Channel):
    name = "web"
    description = "任意网页"
    backends = ["Jina Reader", "Scrapling"]
    tier = 0

    def can_handle(self, url: str) -> bool:
        return True  # Fallback — handles any URL

    def check(self, config=None) -> Tuple[str, str]:
        """Check web channel availability and Scrapling status.

        Returns status and message. Also sets scrapling_stealth field in results.
        """
        has_scrapling = _has_scrapling()
        has_stealth = _has_stealth_fetcher() if has_scrapling else False

        if has_scrapling and has_stealth:
            return (
                "ok",
                "通过 Jina Reader 读取任意网页（curl https://r.jina.ai/URL），"
                "Scrapling 反爬模式可用",
            )
        elif has_scrapling:
            return (
                "ok",
                "通过 Jina Reader 读取任意网页（curl https://r.jina.ai/URL），"
                "Scrapling 已安装但浏览器未初始化（运行 scrapling install）",
            )
        else:
            return (
                "ok",
                "通过 Jina Reader 读取任意网页（curl https://r.jina.ai/URL）",
            )

    def _read_with_jina(self, url: str) -> str:
        """Fast path: Read via Jina Reader."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        jina_url = f"https://r.jina.ai/{url}"
        req = urllib.request.Request(
            jina_url,
            headers={"User-Agent": _UA, "Accept": "text/plain"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")

    def _read_with_scrapling_fetcher(self, url: str) -> str:
        """Fallback: Read via Scrapling Fetcher (stealthy headers)."""
        from scrapling.fetcher import Fetcher

        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        fetcher = Fetcher()
        response = fetcher.get(url)
        return response.text

    def _read_with_scrapling_stealth(self, url: str) -> str:
        """Stealth path: Read via Scrapling StealthyFetcher (headless browser)."""
        from scrapling.fetcher import StealthyFetcher

        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        fetcher = StealthyFetcher()
        response = fetcher.get(url)
        return response.text

    def read(self, url: str, stealth: bool = False) -> str:
        """通过 Jina Reader 或 Scrapling 读取网页，返回 Markdown 全文。

        Args:
            url: The URL to fetch
            stealth: Force use of StealthyFetcher (for Cloudflare-protected sites)

        Returns:
            The page content as text/markdown
        """
        # UAE government portals always require stealth mode
        if _is_uae_gov_portal(url):
            stealth = True

        # Stealth path: directly use StealthyFetcher
        if stealth and _has_stealth_fetcher():
            return self._read_with_scrapling_stealth(url)

        # Try fast path (Jina Reader)
        try:
            return self._read_with_jina(url)
        except Exception:
            # Auto-fallback to Scrapling Fetcher if Jina fails
            if _has_scrapling():
                try:
                    return self._read_with_scrapling_fetcher(url)
                except Exception:
                    # Final fallback to StealthyFetcher
                    if _has_stealth_fetcher():
                        return self._read_with_scrapling_stealth(url)
                    raise
            raise

    def read_stealth(self, url: str) -> str:
        """Read with StealthyFetcher (convenience method for anti-bot sites)."""
        return self.read(url, stealth=True)
