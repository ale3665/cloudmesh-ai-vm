from unittest.mock import MagicMock, patch

import pytest

from cloudmesh.ai.vm.exceptions import ProviderFeatureNotSupported
from cloudmesh.ai.vm.google.GoogleManager import Provider


@pytest.fixture
def google_provider():
    config = {
        "clouds": {
            "google": {
                "project_id": "test-project",
                "private_key": "/fake/key.json",
            }
        }
    }

    with patch(
        "cloudmesh.ai.vm.google.GoogleManager.GCEDriver"
    ) as driver_class:
        provider = Provider(config)
        driver_class.assert_called_once()
        yield provider


def test_restart_without_reboot_support(google_provider):
    # No reboot method exists on this simulated VM.
    # Neither the VM nor the driver supports reboot.
    driver = MagicMock(spec=["get_node"])
    driver.get_node.return_value = MagicMock(spec=["name"])
    google_provider.driver = driver

    with pytest.raises(ProviderFeatureNotSupported):
        google_provider.restart("test-vm")


def test_reset_returns_false_when_stop_fails(google_provider):
    with patch.object(
        google_provider, "restart", return_value=False
    ), patch.object(
        google_provider, "stop", return_value=False
    ):
        assert google_provider.reset("test-vm") is False
