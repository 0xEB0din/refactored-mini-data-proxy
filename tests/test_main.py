import pytest
from unittest.mock import patch
from main import main


def test_demo_default(capsys):
    """End-to-end: demo sub-command with defaults prints decrypted output."""
    with patch("sys.argv", ["mini-data-proxy", "demo"]):
        main()

    captured = capsys.readouterr()
    assert "Decrypted" in captured.out
    assert "Access URL:" in captured.out


def test_demo_custom_payload(capsys):
    """Demo with a user-supplied payload round-trips correctly."""
    with patch("sys.argv", [
        "mini-data-proxy", "demo",
        "--data", "hello proxy",
        "--asset-id", "custom-42",
    ]):
        main()

    captured = capsys.readouterr()
    assert "hello proxy" in captured.out
