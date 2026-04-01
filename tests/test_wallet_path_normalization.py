import os
import sys
import pathlib

# Ensure test can import the app package from repository root.
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from app.dependencies import _normalize_wallet_path as _dep_normalize
from app.services.bittensor_service import BittensorService


def test_dependency_normalize_wallet_path_hotkey_deep_path():
    raw = "~/.bittensor/wallets/w1/hotkeys/default"
    expected = str(pathlib.Path("~/.bittensor/wallets").expanduser())
    assert _dep_normalize(raw, "w1", "default") == expected


def test_service_normalize_wallet_path_wallet_only():
    raw = "~/.bittensor/wallets"
    expected = str(pathlib.Path("~/.bittensor/wallets").expanduser())
    assert BittensorService._normalize_wallet_path(raw, "w1", "default") == expected


def test_service_normalize_wallet_path_wallet_folder():
    raw = "~/.bittensor/wallets/w1"
    expected = str(pathlib.Path("~/.bittensor/wallets").expanduser())
    assert BittensorService._normalize_wallet_path(raw, "w1", "default") == expected
