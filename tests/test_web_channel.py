# -*- coding: utf-8 -*-
"""Tests for web channel with Scrapling fallback and tiered fetching."""

import pytest
from unittest.mock import patch, MagicMock
from agent_reach.channels.web import (
    WebChannel,
    _is_uae_gov_portal,
    _has_scrapling,
    _has_stealth_fetcher,
    _has_lightpanda,
    _get_lightpanda_url,
)


class TestUAEDetection:
    """Test UAE government portal detection."""

    def test_mohre_url_detected(self):
        assert _is_uae_gov_portal("https://www.mohre.gov.ae/en/") is True
        assert _is_uae_gov_portal("https://mohre.gov.ae") is True

    def test_fta_tax_url_detected(self):
        assert _is_uae_gov_portal("https://tax.gov.ae/en/") is True
        assert _is_uae_gov_portal("https://www.tax.gov.ae") is True

    def test_ded_dubai_url_detected(self):
        assert _is_uae_gov_portal("https://ded.ae") is True
        assert _is_uae_gov_portal("https://www.dubaided.gov.ae") is True

    def test_shams_ae_detected(self):
        assert _is_uae_gov_portal("https://shams.ae") is True
        assert _is_uae_gov_portal("https://www.shams.ae") is True

    def test_regular_url_not_detected(self):
        assert _is_uae_gov_portal("https://example.com") is False
        assert _is_uae_gov_portal("https://github.com") is False
        assert _is_uae_gov_portal("https://google.com") is False


class TestScraplingAvailability:
    """Test Scrapling availability detection."""

    def test_has_scrapling_when_installed(self):
        with patch("builtins.__import__") as mock_import:
            mock_import.return_value = MagicMock()
            assert _has_scrapling() is True

    def test_has_scrapling_when_not_installed(self):
        with patch("builtins.__import__", side_effect=ImportError):
            assert _has_scrapling() is False

    def test_has_stealth_fetcher_when_available(self):
        with patch("agent_reach.channels.web._has_scrapling", return_value=True):
            with patch("scrapling.StealthyFetcher") as mock_fetcher:
                mock_fetcher.return_value = MagicMock()
                assert _has_stealth_fetcher() is True

    def test_has_stealth_fetcher_when_not_available(self):
        with patch("agent_reach.channels.web._has_scrapling", return_value=True):
            with patch("scrapling.StealthyFetcher", side_effect=Exception("Not found")):
                assert _has_stealth_fetcher() is False


class TestLightpandaAvailability:
    """Test Lightpanda availability detection."""

    def test_get_lightpanda_url_default(self):
        with patch.dict("os.environ", {}, clear=True):
            assert _get_lightpanda_url() == "ws://localhost:9222"

    def test_get_lightpanda_url_from_env(self):
        with patch.dict("os.environ", {"LIGHTPANDA_URL": "ws://remote:9222"}):
            assert _get_lightpanda_url() == "ws://remote:9222"

    def test_has_lightpanda_when_running(self):
        with patch("socket.socket") as mock_socket:
            mock_sock_instance = MagicMock()
            mock_sock_instance.connect_ex.return_value = 0  # Success
            mock_socket.return_value = mock_sock_instance
            assert _has_lightpanda() is True

    def test_has_lightpanda_when_not_running(self):
        with patch("socket.socket") as mock_socket:
            mock_sock_instance = MagicMock()
            mock_sock_instance.connect_ex.return_value = 1  # Failure
            mock_socket.return_value = mock_sock_instance
            assert _has_lightpanda() is False


class TestWebChannelCheck:
    """Test WebChannel.check() method."""

    def test_check_returns_ok_with_jina_only(self):
        with patch("agent_reach.channels.web._has_scrapling", return_value=False):
            with patch("agent_reach.channels.web._has_lightpanda", return_value=False):
                channel = WebChannel()
                status, msg = channel.check()
                assert status == "ok"
                assert "Jina" in msg

    def test_check_returns_ok_with_scrapling(self):
        with patch("agent_reach.channels.web._has_scrapling", return_value=True):
            with patch("agent_reach.channels.web._has_stealth_fetcher", return_value=True):
                with patch("agent_reach.channels.web._has_lightpanda", return_value=False):
                    channel = WebChannel()
                    status, msg = channel.check()
                    assert status == "ok"
                    assert "Jina" in msg
                    assert "Scrapling" in msg

    def test_check_returns_ok_with_lightpanda(self):
        with patch("agent_reach.channels.web._has_scrapling", return_value=False):
            with patch("agent_reach.channels.web._has_lightpanda", return_value=True):
                channel = WebChannel()
                status, msg = channel.check()
                assert status == "ok"
                assert "Jina" in msg
                assert "Lightpanda" in msg

    def test_check_returns_complete_status(self):
        with patch("agent_reach.channels.web._has_scrapling", return_value=True):
            with patch("agent_reach.channels.web._has_stealth_fetcher", return_value=True):
                with patch("agent_reach.channels.web._has_lightpanda", return_value=True):
                    channel = WebChannel()
                    status, msg = channel.check()
                    assert status == "ok"
                    assert "Jina" in msg
                    assert "Scrapling" in msg
                    assert "Lightpanda" in msg


class TestJinaFastPath:
    """Test Tier 1: Jina Reader fast path."""

    def test_jina_fast_path_success(self):
        channel = WebChannel()
        mock_response = MagicMock()
        mock_response.read.return_value = b"Test content from Jina"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=None)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = channel._read_with_jina("https://example.com")
            assert result == "Test content from Jina"

    def test_jina_fast_path_adds_https(self):
        channel = WebChannel()
        mock_response = MagicMock()
        mock_response.read.return_value = b"Test content"

        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("urllib.request.Request") as mock_request:
                mock_request_instance = MagicMock()
                mock_request.return_value = mock_request_instance
                mock_urlopen.return_value = mock_response

                channel._read_with_jina("example.com")

                # Verify the URL was constructed with https
                call_args = mock_request.call_args
                assert "https://example.com" in call_args[0][0]


class TestScraplingFallback:
    """Test Tier 2: Scrapling Fetcher fallback."""

    def test_scrapling_fetcher_fallback(self):
        channel = WebChannel()

        with patch.object(channel, "_read_with_jina", side_effect=Exception("Jina failed")):
            with patch("agent_reach.channels.web._has_scrapling", return_value=True):
                with patch("agent_reach.channels.web._has_stealth_fetcher", return_value=False):
                    with patch("agent_reach.channels.web._has_lightpanda", return_value=False):
                        with patch("scrapling.Fetcher") as mock_fetcher_class:
                            mock_fetcher = MagicMock()
                            mock_fetcher.get.return_value.text = "Scrapling content"
                            mock_fetcher_class.return_value = mock_fetcher

                            result = channel.read("https://example.com")
                            assert result == "Scrapling content"

    def test_scrapling_fetcher_used_directly(self):
        channel = WebChannel()

        with patch("scrapling.Fetcher") as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher.get.return_value.text = "Direct Scrapling content"
            mock_fetcher_class.return_value = mock_fetcher

            result = channel._read_with_scrapling_fetcher("https://example.com")
            assert result == "Direct Scrapling content"


class TestStealthAutoTrigger:
    """Test Tier 3: StealthyFetcher auto-trigger for UAE portals."""

    def test_uae_portal_skips_to_stealth(self):
        channel = WebChannel()

        # Jina should NOT be called for UAE portals
        with patch.object(channel, "_read_with_jina") as mock_jina:
            with patch("agent_reach.channels.web._has_stealth_fetcher", return_value=True):
                with patch("scrapling.StealthyFetcher") as mock_stealth_class:
                    mock_stealth = MagicMock()
                    mock_stealth.get.return_value.text = "Stealth content for MOHRE"
                    mock_stealth_class.return_value = mock_stealth

                    result = channel.read("https://www.mohre.gov.ae/en/")

                    # Jina should not be called
                    mock_jina.assert_not_called()
                    # Stealth should be used
                    assert result == "Stealth content for MOHRE"

    def test_stealth_mode_via_parameter(self):
        channel = WebChannel()

        with patch.object(channel, "_read_with_jina") as mock_jina:
            with patch("agent_reach.channels.web._has_stealth_fetcher", return_value=True):
                with patch("scrapling.StealthyFetcher") as mock_stealth_class:
                    mock_stealth = MagicMock()
                    mock_stealth.get.return_value.text = "Stealth content"
                    mock_stealth_class.return_value = mock_stealth

                    result = channel.read("https://example.com", stealth=True)

                    # Jina should not be called when stealth=True
                    mock_jina.assert_not_called()
                    assert result == "Stealth content"

    def test_stealthy_fetcher_direct(self):
        channel = WebChannel()

        with patch("scrapling.StealthyFetcher") as mock_stealth_class:
            mock_stealth = MagicMock()
            mock_stealth.get.return_value.text = "Direct stealth content"
            mock_stealth_class.return_value = mock_stealth

            result = channel._read_with_scrapling_stealth("https://example.com")
            assert result == "Direct stealth content"


class TestLightpandaConnection:
    """Test Tier 4: Lightpanda CDP connection."""

    def test_lightpanda_used_when_available(self):
        channel = WebChannel()

        with patch("agent_reach.channels.web._has_lightpanda", return_value=True):
            with patch("scrapling.DynamicFetcher") as mock_dynamic_class:
                mock_fetcher = MagicMock()
                mock_fetcher.get.return_value.text = "Lightpanda content"
                mock_dynamic_class.return_value = mock_fetcher

                result = channel._read_with_lightpanda("https://example.com")
                assert result == "Lightpanda content"
                # Verify it was called with Lightpanda endpoint
                mock_dynamic_class.assert_called_once()
                call_kwargs = mock_dynamic_class.call_args.kwargs
                assert "browserWSEndpoint" in call_kwargs

    def test_lightpanda_fallback_to_stealth(self):
        channel = WebChannel()

        with patch("agent_reach.channels.web._has_lightpanda", return_value=True):
            with patch("scrapling.DynamicFetcher", side_effect=Exception("Lightpanda failed")):
                with patch("agent_reach.channels.web._has_stealth_fetcher", return_value=True):
                    with patch("scrapling.StealthyFetcher") as mock_stealth_class:
                        mock_stealth = MagicMock()
                        mock_stealth.get.return_value.text = "Fallback stealth content"
                        mock_stealth_class.return_value = mock_stealth

                        result = channel._try_lightpanda_or_fallback("https://example.com")
                        assert result == "Fallback stealth content"

    def test_read_stealth_convenience_method(self):
        channel = WebChannel()

        with patch.object(channel, "read") as mock_read:
            mock_read.return_value = "Stealth result"
            result = channel.read_stealth("https://example.com")

            mock_read.assert_called_once_with("https://example.com", stealth=True)
            assert result == "Stealth result"


class TestTierFallback:
    """Test automatic tier fallback behavior."""

    def test_full_fallback_chain_jina_to_scrapling_to_stealth(self):
        channel = WebChannel()

        # Jina fails, Scrapling fails, Stealth works
        with patch.object(channel, "_read_with_jina", side_effect=Exception("Jina failed")):
            with patch("agent_reach.channels.web._has_scrapling", return_value=True):
                with patch.object(channel, "_read_with_scrapling_fetcher", side_effect=Exception("Scrapling failed")):
                    with patch("agent_reach.channels.web._has_lightpanda", return_value=False):
                        with patch("agent_reach.channels.web._has_stealth_fetcher", return_value=True):
                            with patch("scrapling.StealthyFetcher") as mock_stealth_class:
                                mock_stealth = MagicMock()
                                mock_stealth.get.return_value.text = "Final stealth result"
                                mock_stealth_class.return_value = mock_stealth

                                result = channel.read("https://example.com")
                                assert result == "Final stealth result"

    def test_fallback_to_lightpanda_when_jina_fails(self):
        channel = WebChannel()

        with patch.object(channel, "_read_with_jina", side_effect=Exception("Jina failed")):
            with patch("agent_reach.channels.web._has_scrapling", return_value=False):
                with patch("agent_reach.channels.web._has_lightpanda", return_value=True):
                    with patch("scrapling.DynamicFetcher") as mock_dynamic_class:
                        mock_fetcher = MagicMock()
                        mock_fetcher.get.return_value.text = "Lightpanda fallback"
                        mock_dynamic_class.return_value = mock_fetcher

                        result = channel.read("https://example.com")
                        assert result == "Lightpanda fallback"

    def test_error_when_no_backend_available(self):
        channel = WebChannel()

        with patch.object(channel, "_read_with_jina", side_effect=Exception("Jina failed")):
            with patch("agent_reach.channels.web._has_scrapling", return_value=False):
                with patch("agent_reach.channels.web._has_lightpanda", return_value=False):
                    with patch("agent_reach.channels.web._has_stealth_fetcher", return_value=False):
                        with pytest.raises(RuntimeError, match="No browser backend available"):
                            channel.read("https://example.com")


class TestCanHandle:
    """Test WebChannel.can_handle() method."""

    def test_can_handle_any_url(self):
        channel = WebChannel()
        assert channel.can_handle("https://example.com") is True
        assert channel.can_handle("http://test.org") is True
        assert channel.can_handle("ftp://files.example.com") is True
        assert channel.can_handle("not-a-url") is True  # Fallback handles anything


class TestChannelProperties:
    """Test WebChannel properties."""

    def test_name(self):
        channel = WebChannel()
        assert channel.name == "web"

    def test_backends(self):
        channel = WebChannel()
        assert "Jina Reader" in channel.backends
        assert "Scrapling" in channel.backends
        assert "Lightpanda" in channel.backends
