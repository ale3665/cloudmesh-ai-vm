from unittest.mock import MagicMock, patch
import pytest
from cloudmesh.ai.vm.exceptions import VMAuthError
from cloudmesh.ai.vm.openstack.OpenstackManager import OpenstackManager


def test_openstack_sdk_error_does_not_expose_credentials(caplog):
    """
    Sensitive values from OpenStack SDK authentication failures
    must not appear in provider exceptions or logs.
    """
    fake_secret = "FAKE-APP-CREDENTIAL-SECRET-12345"

    manager = OpenstackManager.__new__(OpenstackManager)
    manager.cloud_name = "test-cloud"
    manager.config = {}

    manager.get_cloud_config = MagicMock(
        return_value={
            "auth": {
                "auth_url": "https://example.invalid/v3/",
                "username": "test-user",
                "password": fake_secret,
            }
        }
    )

    with patch("os.path.exists", return_value=False), \
         patch(
             "openstack.connect",
             side_effect=Exception(
                 f"Authentication failed using secret {fake_secret}"
             ),
         ):
        with pytest.raises(VMAuthError) as exc_info:
            manager._get_sdk_conn()

    assert fake_secret not in str(exc_info.value)
    assert fake_secret not in caplog.text
