import requests
from json.decoder import JSONDecodeError
from typing import Dict, Union


def get(access_url: str, headers=None) -> Union[Dict, None]:

    if headers is None:
        headers = {}
    try:
        print(f"requesting {access_url}")
        response = requests.get(access_url, headers=headers)
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
