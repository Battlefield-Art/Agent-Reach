# -*- coding: utf-8 -*-
"""Tests for Lightpanda browser integration."""

import socket
from unittest.mock import MagicMock, patch

import pytest

from agent_reach.channels.web import (
    WebChannel,
    _get_lightpanda_url,
    _has_lightpanda,
)


class TestLightpandaDetection:
    """Test Lightpanda detection and connectivity."""

    def test_has_lightpanda_returns_true_when_port_open(self, monkeypatch):
        """_has_lightpanda should return True when port 9222 is open."""
        # Mock socket to simulate open port
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0  # Success

        def mock_socket_factory(*args, **kwargs):
            return mock_sock

        monkeypatch.setattr(socket, "socket", mock_socket_factory)

        assert _has_lightpanda() is True
        mock_sock.connect_ex.assert_called_once_with(("localhost", 9222))
        mock_sock.close.assert_called_once()

    def test_has_lightpanda_returns_false_when_port_closed(self, monkeypatch):
        """_has_lightpanda should return False when port 9222 is closed."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 61  # Connection refused

        def mock_socket_factory(*args, **kwargs):
            return mock_sock

        monkeypatch.setattr(socket, "socket", mock_socket_factory)

        assert _has_lightpanda() is False

    def test_has_lightpanda_handles_exceptions(self, monkeypatch):
        """_has_lightpanda should return False on exceptions."""

        def mock_socket_factory(*args, **kwargs):
            raise socket.error("Network error")

        monkeypatch.setattr(socket, "socket", mock_socket_factory)

        assert _has_lightpanda() is False

    def test_has_lightpanda_uses_env_var(self, monkeypatch):
        """_has_lightpanda should use LIGHTPANDA_URL env var."""
        monkeypatch.setenv("LIGHTPANDA_URL", "ws://192.168.1.100:9223")

        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0

        def mock_socket_factory(*args, **kwargs):
            return mock_sock

        monkeypatch.setattr(socket, "socket", mock_socket_factory)

        _has_lightpanda()

        # Should connect to the custom host:port
        mock_sock.connect_ex.assert_called_once_with(("192.168.1.100", 9223))

    def test_has_lightpanda_parses_wss_url(self, monkeypatch):
        """_has_lightpanda should handle wss:// URLs."""
        monkeypatch.setenv("LIGHTPANDA_URL", "wss://secure.example.com:9443")

        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0

        def mock_socket_factory(*args, **kwargs):
            return mock_sock

        monkeypatch.setattr(socket, "socket", mock_socket_factory)

        _has_lightpanda()

        mock_sock.connect_ex.assert_called_once_with(("secure.example.com", 9443))


class TestLightpandaUrl:
    """Test Lightpanda URL configuration."""

    def test_get_lightpanda_url_default(self, monkeypatch):
        """Should return default URL when env var not set."""
        monkeypatch.delenv("LIGHTPANDA_URL", raising=False)
        assert _get_lightpanda_url() == "ws://localhost:9222"

    def test_get_lightpanda_url_from_env(self, monkeypatch):
        """Should return URL from env var when set."""
        monkeypatch.setenv("LIGHTPANDA_URL", "ws://custom:9999")
        assert _get_lightpanda_url() == "ws://custom:9999"


class TestWebChannelLightpanda:
    """Test WebChannel integration with Lightpanda."""

    def test_check_includes_lightpanda_status(self, monkeypatch):
        """WebChannel.check should include Lightpanda in message."""
        # Mock _has_lightpanda to return True
        monkeypatch.setattr(
            "agent_reach.channels.web._has_lightpanda", lambda: True
        )
        monkeypatch.setattr(
            "agent_reach.channels.web._has_scrapling", lambda: True
        )
        monkeypatch.setattr(
            "agent_reach.channels.web._has_stealth_fetcher", lambda: True
        )

        channel = WebChannel()
        status, message = channel.check()

        assert status == "ok"
        assert "Lightpanda CDP 可用" in message

    def test_check_omits_lightpanda_when_not_running(self, monkeypatch):
        """WebChannel.check should omit Lightpanda when not running."""
        monkeypatch.setattr(
            "agent_reach.channels.web._has_lightpanda", lambda: False
        )
        monkeypatch.setattr(
            "agent_reach.channels.web._has_scrapling", lambda: True
        )
        monkeypatch.setattr(
            "agent_reach.channels.web._has_stealth_fetcher", lambda: True
        )

        channel = WebChannel()
        status, message = channel.check()

        assert status == "ok"
        assert "Lightpanda" not in message

    def test_read_with_lightpanda_method_exists(self):
        """Test _read_with_lightpanda method exists and accepts URL."""
        channel = WebChannel()

        # Just verify the method exists and is callable
        assert hasattr(channel, "_read_with_lightpanda")
        import inspect
        sig = inspect.signature(channel._read_with_lightpanda)
        assert "url" in sig.parameters

    def test_try_lightpanda_or_fallback_uses_lightpanda(self, monkeypatch):
        """_try_lightpanda_or_fallback should use Lightpanda when available."""
        channel = WebChannel()

        monkeypatch.setattr(
            "agent_reach.channels.web._has_lightpanda", lambda: True
        )

        # Mock _read_with_lightpanda to return content
        def mock_read(url):
            return "Lightpanda content"

        monkeypatch.setattr(channel, "_read_with_lightpanda", mock_read)

        result = channel._try_lightpanda_or_fallback("https://example.com")
        assert result == "Lightpanda content"

    def test_try_lightpanda_or_fallback_to_stealth(self, monkeypatch):
        """_try_lightpanda_or_fallback should fallback to StealthyFetcher."""
        channel = WebChannel()

        # Lightpanda not available
        monkeypatch.setattr(
            "agent_reach.channels.web._has_lightpanda", lambda: False
        )
        monkeypatch.setattr(
            "agent_reach.channels.web._has_stealth_fetcher", lambda: True
        )

        # Mock _read_with_scrapling_stealth to return content
        def mock_read(url):
            return "StealthyFetcher content"

        monkeypatch.setattr(channel, "_read_with_scrapling_stealth", mock_read)

        result = channel._try_lightpanda_or_fallback("https://example.com")
        assert result == "StealthyFetcher content"

    def test_try_lightpanda_fallback_when_lightpanda_fails(self, monkeypatch):
        """_try_lightpanda_or_fallback should fallback when Lightpanda fails."""
        channel = WebChannel()

        monkeypatch.setattr(
            "agent_reach.channels.web._has_lightpanda", lambda: True
        )
        monkeypatch.setattr(
            "agent_reach.channels.web._has_stealth_fetcher", lambda: True
        )

        # Mock _read_with_lightpanda to raise exception
        def mock_read_fail(url):
            raise Exception("Lightpanda failed")

        def mock_read_stealth(url):
            return "StealthyFetcher content"

        monkeypatch.setattr(channel, "_read_with_lightpanda", mock_read_fail)
        monkeypatch.setattr(channel, "_read_with_scrapling_stealth", mock_read_stealth)

        result = channel._try_lightpanda_or_fallback("https://example.com")
        assert result == "StealthyFetcher content"


class TestLightpandaDockerSetup:
    """Test Docker-based Lightpanda installation helpers."""

    def test_install_lightpanda_skips_without_docker(self, capsys, monkeypatch):
        """Should skip Lightpanda if Docker is not available."""
        import shutil
        import platform
        from agent_reach.cli import _install_lightpanda

        monkeypatch.setattr(shutil, "which", lambda x: None)

        _install_lightpanda()

        captured = capsys.readouterr()
        assert "Lightpanda skipped" in captured.out
        assert "Docker not found" in captured.out

    def test_install_lightpanda_skips_on_termux(self, capsys, monkeypatch):
        """Should skip Lightpanda on Termux/ARM."""
        import shutil
        import platform
        from agent_reach.cli import _install_lightpanda

        monkeypatch.setattr(shutil, "which", lambda x: "/usr/bin/docker" if x == "docker" else None)
        monkeypatch.setattr(platform, "machine", lambda: "aarch64")
        monkeypatch.setenv("TERMUX_VERSION", "0.118")

        _install_lightpanda()

        captured = capsys.readouterr()
        assert "Lightpanda skipped" in captured.out
        assert "Termux" in captured.out

    def test_install_lightpanda_detects_running_container(self, capsys, monkeypatch):
        """Should detect if Lightpanda container is already running."""
        import shutil
        import subprocess
        import platform
        from agent_reach.cli import _install_lightpanda

        monkeypatch.setattr(shutil, "which", lambda x: "/usr/bin/docker" if x == "docker" else None)
        monkeypatch.setattr(platform, "machine", lambda: "x86_64")

        call_count = {"count": 0}

        def mock_run(cmd, **kwargs):
            call_count["count"] += 1
            # First call checks running containers with --filter
            if call_count["count"] == 1 and "ps" in cmd and "--filter" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "lightpanda\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        monkeypatch.setattr(subprocess, "run", mock_run)

        _install_lightpanda()

        captured = capsys.readouterr()
        assert "already running on port 9222" in captured.out


class TestDoctorLightpanda:
    """Test doctor module Lightpanda integration."""

    def test_check_lightpanda_returns_ok_when_running(self, monkeypatch):
        """_check_lightpanda should return True when Lightpanda is running."""
        from agent_reach.doctor import _check_lightpanda

        monkeypatch.setattr(
            "agent_reach.channels.web._has_lightpanda", lambda: True
        )

        available, message = _check_lightpanda()
        assert available is True
        assert "可用" in message

    def test_check_lightpanda_returns_false_when_not_running(self, monkeypatch):
        """_check_lightpanda should return False when Lightpanda is not running."""
        from agent_reach.doctor import _check_lightpanda

        monkeypatch.setattr(
            "agent_reach.channels.web._has_lightpanda", lambda: False
        )

        available, message = _check_lightpanda()
        assert available is False
        assert "未运行" in message
