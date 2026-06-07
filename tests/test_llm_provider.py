#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for LLM provider abstraction (server/base/llm_provider.py).

Unit tests use mocked HTTP responses; integration tests hit the real API
and are skipped when MINIMAX_API_KEY is not set.
"""

import json
import os
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest

from server.base.llm_provider import (
    LLMProvider,
    LMDeployProvider,
    MiniMaxProvider,
    create_llm_provider,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_stream_lines(contents: list[str]) -> list[str]:
    """Build SSE lines like the MiniMax API returns."""
    lines = []
    for c in contents:
        chunk = {"choices": [{"delta": {"content": c}}]}
        lines.append(f"data: {json.dumps(chunk)}")
    lines.append("data: [DONE]")
    return lines


def _make_sync_response(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


# ---------------------------------------------------------------------------
# Unit tests – MiniMaxProvider
# ---------------------------------------------------------------------------


class TestMiniMaxProviderInit:
    """Test MiniMaxProvider initialization."""

    def test_init_with_explicit_key(self):
        p = MiniMaxProvider(api_key="test-key", model="MiniMax-M3")
        assert p.available_models == ["MiniMax-M3"]

    def test_init_from_env(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "env-key")
        monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M2.7")
        p = MiniMaxProvider()
        assert p.available_models == ["MiniMax-M2.7"]
        assert p._api_key == "env-key"

    def test_default_model_is_m3(self, monkeypatch):
        """Default model should be MiniMax-M3."""
        monkeypatch.delenv("MINIMAX_MODEL", raising=False)
        p = MiniMaxProvider(api_key="k")
        assert p.available_models == ["MiniMax-M3"]

    def test_init_missing_key_raises(self, monkeypatch):
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key is required"):
            MiniMaxProvider(api_key="")

    def test_default_base_url(self):
        p = MiniMaxProvider(api_key="k")
        assert p._base_url == "https://api.minimax.io/v1"

    def test_custom_base_url(self):
        p = MiniMaxProvider(api_key="k", base_url="https://custom.api/v2/")
        assert p._base_url == "https://custom.api/v2"  # trailing slash stripped


class TestMiniMaxTemperatureClamping:
    """Test temperature clamping."""

    def test_clamp_normal(self):
        assert MiniMaxProvider._clamp_temperature(0.7) == 0.7

    def test_clamp_zero(self):
        assert MiniMaxProvider._clamp_temperature(0.0) == 0.0

    def test_clamp_one(self):
        assert MiniMaxProvider._clamp_temperature(1.0) == 1.0

    def test_clamp_above_one(self):
        assert MiniMaxProvider._clamp_temperature(1.5) == 1.0

    def test_clamp_negative(self):
        assert MiniMaxProvider._clamp_temperature(-0.5) == 0.0


class TestMiniMaxStripThinkTags:
    """Test think-tag stripping."""

    def test_strip_think_tags(self):
        text = "<think>reasoning here</think>\nActual content"
        result = MiniMaxProvider._strip_think_tags(text)
        assert result == "Actual content"

    def test_strip_multiple_think_tags(self):
        text = "<think>a</think>Hello <think>b</think>World"
        result = MiniMaxProvider._strip_think_tags(text)
        assert result == "Hello World"

    def test_no_think_tags(self):
        text = "Just normal text"
        assert MiniMaxProvider._strip_think_tags(text) == text

    def test_empty_think_tag(self):
        text = "<think></think>Content"
        result = MiniMaxProvider._strip_think_tags(text)
        assert result == "Content"

    def test_multiline_think_tag(self):
        text = "<think>\nline1\nline2\n</think>\nAnswer"
        result = MiniMaxProvider._strip_think_tags(text)
        assert result == "Answer"


class TestMiniMaxStreamingMocked:
    """Test streaming with mocked HTTP."""

    @patch("server.base.llm_provider.httpx.Client")
    def test_streaming_basic(self, mock_client_cls):
        lines = _make_stream_lines(["Hello", " World"])
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter(lines)
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        p = MiniMaxProvider(api_key="test-key")
        results = list(
            p.chat_completions_v1(
                model="MiniMax-M3",
                messages=[{"role": "user", "content": "Hi"}],
                stream=True,
            )
        )

        assert len(results) == 2
        assert results[0]["choices"][0]["delta"]["content"] == "Hello"
        assert results[1]["choices"][0]["delta"]["content"] == " World"

    @patch("server.base.llm_provider.httpx.Client")
    def test_streaming_strips_think_tags(self, mock_client_cls):
        chunk_content = "<think>reasoning</think>Answer"
        lines = _make_stream_lines([chunk_content])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = iter(lines)
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        p = MiniMaxProvider(api_key="test-key")
        results = list(
            p.chat_completions_v1(
                model="MiniMax-M3",
                messages=[{"role": "user", "content": "Hi"}],
                stream=True,
            )
        )

        assert results[0]["choices"][0]["delta"]["content"] == "Answer"


class TestMiniMaxSyncMocked:
    """Test non-streaming with mocked HTTP."""

    @patch("server.base.llm_provider.httpx.Client")
    def test_sync_basic(self, mock_client_cls):
        resp_data = _make_sync_response("Hello World")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = resp_data

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        p = MiniMaxProvider(api_key="test-key")
        results = list(
            p.chat_completions_v1(
                model="MiniMax-M3",
                messages=[{"role": "user", "content": "Hi"}],
                stream=False,
            )
        )

        assert len(results) == 1
        assert results[0]["choices"][0]["message"]["content"] == "Hello World"

    @patch("server.base.llm_provider.httpx.Client")
    def test_sync_strips_think_tags(self, mock_client_cls):
        resp_data = _make_sync_response("<think>thought</think>Answer")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = resp_data

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        p = MiniMaxProvider(api_key="test-key")
        results = list(
            p.chat_completions_v1(
                model="MiniMax-M3",
                messages=[{"role": "user", "content": "Hi"}],
                stream=False,
            )
        )

        assert results[0]["choices"][0]["message"]["content"] == "Answer"

    @patch("server.base.llm_provider.httpx.Client")
    def test_sync_api_error(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        p = MiniMaxProvider(api_key="bad-key")
        with pytest.raises(RuntimeError, match="MiniMax API error 401"):
            list(
                p.chat_completions_v1(
                    model="MiniMax-M3",
                    messages=[{"role": "user", "content": "Hi"}],
                )
            )


class TestMiniMaxMessageFiltering:
    """Test that messages are properly filtered for MiniMax API."""

    @patch("server.base.llm_provider.httpx.Client")
    def test_filters_environment_role(self, mock_client_cls):
        resp_data = _make_sync_response("ok")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = resp_data

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        p = MiniMaxProvider(api_key="test-key")
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
            {"role": "environment", "content": "tool result"},
        ]
        list(p.chat_completions_v1(model="M", messages=messages))

        call_args = mock_client.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        sent_messages = payload["messages"]

        # environment role should be converted to user
        assert len(sent_messages) == 3
        assert sent_messages[2]["role"] == "user"
        assert sent_messages[2]["content"] == "tool result"

    @patch("server.base.llm_provider.httpx.Client")
    def test_skip_special_tokens_ignored(self, mock_client_cls):
        """skip_special_tokens is an LMDeploy kwarg; MiniMax should ignore it."""
        resp_data = _make_sync_response("ok")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = resp_data

        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_client

        p = MiniMaxProvider(api_key="test-key")
        # Should not raise
        list(
            p.chat_completions_v1(
                model="M",
                messages=[{"role": "user", "content": "Hi"}],
                skip_special_tokens=False,
            )
        )


# ---------------------------------------------------------------------------
# Unit tests – create_llm_provider factory
# ---------------------------------------------------------------------------


class TestCreateLLMProvider:
    """Test the factory function."""

    def test_create_minimax(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        p = create_llm_provider("minimax")
        assert isinstance(p, MiniMaxProvider)

    def test_create_minimax_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        p = create_llm_provider("MiniMax")
        assert isinstance(p, MiniMaxProvider)

    def test_create_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            create_llm_provider("unknown_provider")

    def test_create_lmdeploy_needs_url(self):
        with pytest.raises(ValueError, match="api_url is required"):
            create_llm_provider("lmdeploy")

    def test_env_default(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "minimax")
        monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
        p = create_llm_provider()
        assert isinstance(p, MiniMaxProvider)


# ---------------------------------------------------------------------------
# Unit tests – LLMProvider ABC
# ---------------------------------------------------------------------------


class TestLLMProviderABC:
    """Ensure the ABC cannot be instantiated directly."""

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            LLMProvider()


# ---------------------------------------------------------------------------
# Integration tests – require MINIMAX_API_KEY
# ---------------------------------------------------------------------------

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
skip_no_key = pytest.mark.skipif(
    not MINIMAX_API_KEY,
    reason="MINIMAX_API_KEY not set; skipping integration tests",
)


@skip_no_key
class TestMiniMaxIntegrationSync:
    """Integration: non-streaming call to MiniMax API."""

    def test_sync_chat(self):
        p = MiniMaxProvider(api_key=MINIMAX_API_KEY, model="MiniMax-M3")
        results = list(
            p.chat_completions_v1(
                model="MiniMax-M3",
                messages=[{"role": "user", "content": "Say hello in one word."}],
                stream=False,
                temperature=0.1,
            )
        )
        assert len(results) == 1
        content = results[0]["choices"][0]["message"]["content"]
        assert len(content) > 0
        assert "think>" not in content  # think tags should be stripped


@skip_no_key
class TestMiniMaxIntegrationStream:
    """Integration: streaming call to MiniMax API."""

    def test_stream_chat(self):
        p = MiniMaxProvider(api_key=MINIMAX_API_KEY, model="MiniMax-M3")
        chunks = list(
            p.chat_completions_v1(
                model="MiniMax-M3",
                messages=[{"role": "user", "content": "Say hello in one word."}],
                stream=True,
                temperature=0.1,
            )
        )
        assert len(chunks) > 0
        full_text = "".join(
            c["choices"][0]["delta"].get("content", "") for c in chunks
        )
        assert len(full_text) > 0


@skip_no_key
class TestMiniMaxIntegrationFactory:
    """Integration: factory creates working MiniMax provider."""

    def test_factory_minimax(self):
        p = create_llm_provider("minimax", api_key=MINIMAX_API_KEY, model="MiniMax-M3")
        assert isinstance(p, MiniMaxProvider)
        assert p.available_models == ["MiniMax-M3"]
        results = list(
            p.chat_completions_v1(
                model="MiniMax-M3",
                messages=[{"role": "user", "content": "Respond with OK"}],
                stream=False,
            )
        )
        assert len(results) == 1
