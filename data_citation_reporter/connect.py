# -*- coding: utf-8 -*-
"""Utility module for connecting to APIs."""

from json.decoder import JSONDecodeError
from typing import Dict, Union
import requests


def get(access_url: str, headers=None, timeout=120) -> Union[Dict, None]:
    """Wrapper function for requests.get.

    This function includes testing:
    - the HTTP response status code
    - the HTTP response data is a valid JSON object

    :param access_url: URL to be accessed
    :param headers: HTTP headers (defaults to None)
    :param timeout: timeout in seconds (defaults to 120 seconds)
    :return: response object
    """
    if headers is None:
        headers = {}
    try:
        print(f"requesting {access_url}")
        response = requests.get(access_url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        print(str(e))
        return None
    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred:", str(e))
        return None

    try:
        data = response.json()
    except JSONDecodeError as e:
        print(str(e))
        return None

    return data
