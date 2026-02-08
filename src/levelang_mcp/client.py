"""Async HTTP client for the Levelang translation API."""

from __future__ import annotations

from typing import Any

import httpx

from .config import get_settings


class LevelangClient:
    """Async HTTP client wrapping the Levelang backend API.

    Uses a shared httpx.AsyncClient for connection reuse across requests.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.api_base_url
        self._api_key = settings.api_key
        self._client = httpx.AsyncClient(timeout=30.0)

    def _headers(self) -> dict[str, str]:
        """Build request headers, conditionally including auth."""
        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def translate(
        self,
        text: str,
        source_language_code: str,
        target_language_code: str,
        level: str,
        mood: str,
    ) -> dict[str, Any]:
        """Call POST /translate and return the response dict."""
        response = await self._client.post(
            f"{self.base_url}/translate",
            headers=self._headers(),
            json={
                "text": text,
                "source_language_code": source_language_code,
                "target_language_code": target_language_code,
                "level": level,
                "mood": mood,
            },
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    async def get_languages(self) -> dict[str, Any]:
        """Call GET /languages/details and return full language configs."""
        response = await self._client.get(
            f"{self.base_url}/languages/details",
            headers=self._headers(),
            timeout=10.0,
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    async def get_language(self, code: str) -> dict[str, Any]:
        """Call GET /languages/{code} and return single language config."""
        response = await self._client.get(
            f"{self.base_url}/languages/{code}",
            headers=self._headers(),
            timeout=10.0,
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
