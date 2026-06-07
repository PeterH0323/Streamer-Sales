#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@File    :   llm_provider.py
@Time    :   2026/03/22
@Project :   https://github.com/PeterH0323/Streamer-Sales
@Desc    :   LLM provider abstraction supporting LMDeploy and MiniMax Cloud API.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional

import httpx
from loguru import logger


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """Return list of available model names."""
        ...

    @abstractmethod
    def chat_completions_v1(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """Send a chat completion request and yield response chunks.

        Streaming chunks must have the shape:
            {"choices": [{"delta": {"content": "..."}}]}
        Non-streaming chunks must have the shape:
            {"choices": [{"message": {"content": "..."}}]}
        """
        ...


class LMDeployProvider(LLMProvider):
    """Wrapper around LMDeploy's ``APIClient``."""

    def __init__(self, api_url: str) -> None:
        from lmdeploy.serve.openai.api_client import APIClient

        self._client = APIClient(api_url)

    @property
    def available_models(self) -> List[str]:
        return self._client.available_models

    def chat_completions_v1(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        yield from self._client.chat_completions_v1(
            model=model, messages=messages, stream=stream, **kwargs
        )


class MiniMaxProvider(LLMProvider):
    """MiniMax Cloud API provider (OpenAI-compatible)."""

    DEFAULT_BASE_URL = "https://api.minimax.io/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("MINIMAX_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "MiniMax API key is required. Set MINIMAX_API_KEY env var "
                "or pass api_key to MiniMaxProvider."
            )
        self._model = model or os.environ.get("MINIMAX_MODEL", "MiniMax-M3")
        self._base_url = (
            base_url
            or os.environ.get("MINIMAX_BASE_URL", self.DEFAULT_BASE_URL)
        ).rstrip("/")
        self._timeout = float(os.environ.get("MINIMAX_TIMEOUT", "120"))

    @property
    def available_models(self) -> List[str]:
        return [self._model]

    @staticmethod
    def _clamp_temperature(temperature: float) -> float:
        """Clamp temperature to MiniMax's accepted range [0, 1.0]."""
        return max(0.0, min(temperature, 1.0))

    def chat_completions_v1(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        # Filter out LMDeploy-specific kwargs
        kwargs.pop("skip_special_tokens", None)

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        # Filter messages: only keep standard roles
        filtered_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role in ("system", "user", "assistant"):
                filtered_messages.append(
                    {"role": role, "content": msg.get("content", "")}
                )
            elif role == "environment":
                filtered_messages.append(
                    {"role": "user", "content": msg.get("content", "")}
                )

        temperature = kwargs.pop("temperature", 0.7)
        temperature = self._clamp_temperature(temperature)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": filtered_messages,
            "stream": stream,
            "temperature": temperature,
        }

        top_p = kwargs.pop("top_p", None)
        if top_p is not None:
            payload["top_p"] = top_p

        if stream:
            yield from self._stream_request(url, headers, payload)
        else:
            yield from self._sync_request(url, headers, payload)

    def _stream_request(
        self, url: str, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        with httpx.Client(timeout=self._timeout) as client:
            with client.stream("POST", url, headers=headers, json=payload) as resp:
                if resp.status_code != 200:
                    body = resp.read().decode()
                    logger.error(f"MiniMax API error {resp.status_code}: {body}")
                    raise RuntimeError(f"MiniMax API error {resp.status_code}: {body}")

                for line in resp.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    # Strip thinking tags from content
                    if chunk.get("choices"):
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            content = self._strip_think_tags(content)
                            delta["content"] = content

                    yield chunk

    def _sync_request(
        self, url: str, headers: Dict[str, str], payload: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                logger.error(f"MiniMax API error {resp.status_code}: {resp.text}")
                raise RuntimeError(
                    f"MiniMax API error {resp.status_code}: {resp.text}"
                )
            data = resp.json()

            # Strip thinking tags from content
            if data.get("choices"):
                message = data["choices"][0].get("message", {})
                content = message.get("content", "")
                if content:
                    message["content"] = self._strip_think_tags(content)

            yield data

    @staticmethod
    def _strip_think_tags(text: str) -> str:
        """Remove <think>...</think> blocks from MiniMax M2.7+ responses."""
        import re

        return re.sub(r"<think>[\s\S]*?</think>\s*", "", text)


def create_llm_provider(
    provider_name: Optional[str] = None, **kwargs: Any
) -> LLMProvider:
    """Factory function to create an LLM provider.

    Args:
        provider_name: "lmdeploy" or "minimax". Defaults to env var
            ``LLM_PROVIDER`` or "lmdeploy".
        **kwargs: Provider-specific arguments.

    Returns:
        An ``LLMProvider`` instance.
    """
    name = (
        provider_name or os.environ.get("LLM_PROVIDER", "lmdeploy")
    ).lower().strip()

    if name == "minimax":
        return MiniMaxProvider(
            api_key=kwargs.get("api_key"),
            model=kwargs.get("model"),
            base_url=kwargs.get("base_url"),
        )
    elif name == "lmdeploy":
        api_url = kwargs.get("api_url")
        if not api_url:
            raise ValueError("api_url is required for LMDeployProvider")
        return LMDeployProvider(api_url=api_url)
    else:
        raise ValueError(
            f"Unknown LLM provider: {name!r}. "
            "Supported: 'lmdeploy', 'minimax'."
        )
