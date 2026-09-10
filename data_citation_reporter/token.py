# -*- coding: utf-8 -*-
"""Utility module for managing tokens."""

from pathlib import Path
import os
import yaml
from getpass import getpass

token_file = Path(__file__).parent.parent / "tokens.yaml"
if not token_file.exists():
    os.system(f"touch {token_file}")


def load_token_file():
    """Loads tokens from tokens file."""
    with open(token_file, encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def store_token(key: str, value: str):
    """Stores token in tokens file."""
    token = load_token_file()
    token[key] = value
    with open(token_file, "w", encoding="utf-8") as f:
        yaml.dump(token, f, Dumper=yaml.Dumper)


def load_token(key: str):
    """Loads token from tokens file."""

    tokens = load_token_file()
    if key in tokens:
        return tokens[key]

    print(f"Token `{key}` not found in tokens file")
    value = getpass(f"Please provide your `{key}` token:")
    store_token(key, value)

    return value
