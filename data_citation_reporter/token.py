# -*- coding: utf-8 -*-
"""Utility module for managing tokens."""

import os
import yaml
from pathlib import Path
from getpass import getpass

TOKEN_FILE = Path(os.environ["HOME"]) / ".data_citation_report" / "tokens.yaml"


def load_token_file():
    """Loads tokens from tokens file."""
    TOKEN_FILE.touch(exist_ok=True)
    with open(TOKEN_FILE, encoding="utf-8") as f:
        tokens = yaml.load(f, Loader=yaml.FullLoader)
    if tokens is None:
        tokens = {}
    return tokens


def store_token(key: str, value: str):
    """Stores token in tokens file."""
    token = load_token_file()
    token[key] = value
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        yaml.dump(token, f, Dumper=yaml.Dumper)


def load_token(key: str):
    """Loads token from tokens file."""

    tokens = load_token_file()
    if tokens.get(key) is not None:
        return tokens[key]

    print(f"Token `{key}` not found in tokens file")
    value = getpass(f"Please provide your `{key}` token:")
    store_token(key, value)

    return value
