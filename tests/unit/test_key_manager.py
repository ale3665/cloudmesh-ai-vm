from pathlib import Path
from unittest.mock import patch

from cloudmesh.ai.vm.key_manager import KeyManager


def test_has_passphrase_false_for_unprotected_key():
    """An unprotected private key should not require a passphrase."""
    manager = KeyManager()
    key_path = Path("id_ed25519")

    with patch("cloudmesh.ai.vm.key_manager.PKey.from_path") as from_path:
        from_path.return_value = object()

        result = manager._has_passphrase(key_path)

    assert result is False
    from_path.assert_called_once_with(key_path)


def test_has_passphrase_true_for_password_protected_key():
    """A password-protected private key should be detected."""
    manager = KeyManager()
    key_path = Path("id_ed25519")

    with patch("cloudmesh.ai.vm.key_manager.PKey.from_path") as from_path:
        from_path.side_effect = TypeError(
            "Key is password-protected, but password was not provided."
        )

        result = manager._has_passphrase(key_path)

    assert result is True
    from_path.assert_called_once_with(key_path)


def test_has_passphrase_unknown_for_unrelated_parse_error():
    """Unrelated parsing errors should produce an unknown status."""
    manager = KeyManager()
    key_path = Path("invalid_key")

    with patch("cloudmesh.ai.vm.key_manager.PKey.from_path") as from_path:
        from_path.side_effect = ValueError("Invalid private key")

        result = manager._has_passphrase(key_path)

    assert result is None


def test_has_passphrase_true_for_password_required_exception():
    """A key requiring a password must be classified as protected."""
    from paramiko.ssh_exception import PasswordRequiredException

    manager = KeyManager()
    key_path = Path("id_ed25519")

    with patch("cloudmesh.ai.vm.key_manager.PKey.from_path") as from_path:
        from_path.side_effect = PasswordRequiredException(
            "Private key file is encrypted"
        )
        result = manager._has_passphrase(key_path)

    assert result is True
    from_path.assert_called_once_with(key_path)


def test_has_passphrase_unknown_for_unrelated_type_error():
    """Unexpected TypeError must not classify a key as unprotected."""
    manager = KeyManager()
    key_path = Path("invalid_key")

    with patch("cloudmesh.ai.vm.key_manager.PKey.from_path") as from_path:
        from_path.side_effect = TypeError("Unsupported key format")
        result = manager._has_passphrase(key_path)

    assert result is None
    from_path.assert_called_once_with(key_path)
