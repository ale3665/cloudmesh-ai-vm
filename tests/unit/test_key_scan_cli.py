"""Regression tests for SSH key passphrase status reporting."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from cloudmesh.ai.command import cmx


@pytest.mark.parametrize(
    ("has_passphrase", "expected_status"),
    [
        (True, "Yes"),
        (False, "No"),
        (None, "Unknown"),
    ],
)
def test_key_scan_passphrase_status(has_passphrase, expected_status):
    """Display the correct status without misclassifying unknown keys."""
    key = {
        "path": "/tmp/id_ed25519",
        "type": "ed25519",
        "sha256": "SHA256:test",
        "md5": "MD5:test",
        "comment": "test-key",
        "has_passphrase": has_passphrase,
    }

    with (
        patch("cloudmesh.ai.command.key.scan.KeyManager") as mock_manager,
        patch("cloudmesh.ai.command.key.scan.render_table") as mock_table,
    ):
        mock_manager.return_value.scan_local_keys.return_value = [key]

        result = CliRunner().invoke(cmx, ["key", "scan"])

    assert result.exit_code == 0, result.output
    mock_table.assert_called_once()

    rows = mock_table.call_args.args[2]
    assert len(rows) == 1
    assert rows[0][-1] == expected_status

    warning = "The following keys are unprotected"
    assert (warning in result.output) is (has_passphrase is False)
