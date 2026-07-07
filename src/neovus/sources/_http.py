"""Shared HTTP helpers for source clients."""

from __future__ import annotations

import time
from typing import Any

import requests

USER_AGENT = "neovus/0.1 (Built with Claude hackathon; open-data VUS interpretation)"
_session = requests.Session()
# Accept JSON explicitly — Ensembl REST returns non-JSON without it.
_session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})


def get_json(url: str, params: dict[str, Any] | None = None, timeout: int = 20,
             retries: int = 2) -> Any:
    """GET JSON with a few retries — public REST endpoints (esp. Ensembl) return
    transient empty bodies / 429s under load, which would otherwise look like a
    'variant not found' to a clinician."""
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = _session.get(url, params=params, timeout=timeout)
            if r.status_code == 429:
                raise requests.HTTPError("429 rate limited")
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as e:  # ValueError = JSON decode
            last = e
            if attempt < retries:
                time.sleep(0.6 * (attempt + 1))
    raise last  # type: ignore[misc]


def first(value: Any) -> Any:
    """Many DB fields come back as a list (one entry per transcript). Take the first."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def max_num(value: Any) -> float | None:
    """Max numeric value from a scalar or list (scores can vary by transcript)."""
    if value is None:
        return None
    vals = value if isinstance(value, list) else [value]
    nums = [v for v in vals if isinstance(v, (int, float))]
    return max(nums) if nums else None
