# -*- coding: utf-8 -*-
"""Utility module for connecting to APIs."""

from json.decoder import JSONDecodeError
from json import dumps
import hashlib
from typing import Dict, Optional
import requests
from diskcache import Cache

# Cache configuration
_CACHE_DIR = "~/.data_citation_report/api_cache"
_CACHE_SIZE_LIMIT = 100 * 1024 * 1024  # 100 Mo max sur disque
_cache = Cache(_CACHE_DIR, size_limit=_CACHE_SIZE_LIMIT)


def _make_key(url: str, headers: dict, timeout: int) -> str:
    """Clé déterministe basée sur tous les paramètres de l'appel."""
    payload = f"{url}|{dumps(headers, sort_keys=True)}|{timeout}"
    return hashlib.sha256(payload.encode()).hexdigest()


def get(
    access_url: str,
    headers: Dict | None = None,
    timeout: int = 120,
    ttl: int = 3600,
    use_cache: bool = True,
) -> Optional[Dict]:
    """Wrapper function for requests.get.

    This function includes testing:
    - the HTTP response status code
    - the HTTP response data is a valid JSON object

    :param access_url: URL to be accessed
    :param headers: HTTP headers (defaults to None)
    :param timeout: timeout in seconds (defaults to 120 seconds)
    :param ttl: time-to-live in seconds for cached entries (defaults to 3600 seconds)
    :param use_cache: if False, bypasses the cache entirely (defaults to True)
    :return: parsed JSON response, or None on error
    """
    if headers is None:
        headers = {}

    key = _make_key(access_url, headers, timeout)

    # Reading from cache
    if use_cache:
        cached = _cache.get(key)
        if cached is not None:
            print(f"CACHE HIT for {access_url}")
            return cached

    # Real API call
    try:
        print(f"requesting {access_url}")
        response = requests.get(access_url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        print(str(e))
        return None
    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred:", str(e))
        print(response)
        return None

    try:
        data = response.json()
    except JSONDecodeError as e:
        print(str(e))
        return None

    # Writing cache if the query was successful
    if use_cache and data is not None:
        _cache.set(key, data, expire=ttl)

    return data
