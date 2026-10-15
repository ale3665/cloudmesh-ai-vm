from pathlib import Path
from unittest.mock import patch
import subprocess

from cloudmesh.ai.vm.key_manager import KeyManager


def test_passphrase_protected_key():
    """An encrypted key must be identified as passphrase-protected."""
    with patch("cloudmesh.ai.vm.key_manager.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=255, stdout="", stderr="incorrect passphrase"
        )

        result = KeyManager()._has_passphrase(Path("/tmp/test_encrypted_key"))

        assert result is True
        mock_run.assert_called_once_with(
            ["ssh-keygen", "-y", "-P", "", "-f", "/tmp/test_encrypted_key"],
            capture_output=True,
            text=True,
            timeout=5,
            stdin=subprocess.DEVNULL,
        )


def test_unprotected_key():
    """An unencrypted key must not be identified as passphrase-protected."""
    with patch("cloudmesh.ai.vm.key_manager.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="ssh-ed25519 AAAA...", stderr=""
        )

        result = KeyManager()._has_passphrase(Path("/tmp/test_unencrypted_key"))

        assert result is False


def test_missing_key_returns_unknown():
    """A missing key must not be classified as passphrase-protected."""
    with patch("cloudmesh.ai.vm.key_manager.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=255,
            stdout="",
            stderr="/tmp/missing_key: No such file or directory",
        )

        result = KeyManager()._has_passphrase(Path("/tmp/missing_key"))

        assert result is None
