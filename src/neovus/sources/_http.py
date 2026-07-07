"""Shared HTTP helpers for source clients."""

from __future__ import annotations

from typing import Any

import requests

USER_AGENT = "neovus-kg/0.1 (Built with Claude hackathon; open-data VUS interpretation)"
_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})


def get_json(url: str, params: dict[str, Any] | None = None, timeout: int = 20) -> Any:
    r = _session.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


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
