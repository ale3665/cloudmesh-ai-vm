import pytest
from unittest.mock import MagicMock, PropertyMock, patch
from cloudmesh.ai.vm.exceptions import VMProviderError
from cloudmesh.ai.vm.openstack.OpenstackManager import OpenstackManager


@pytest.fixture
def mock_driver():
    return MagicMock()


@pytest.fixture
def provider(mock_driver):
    config = {
        "clouds": {
            "test-openstack": {
                "image": "test-image",
                "flavor": "test-flavor",
                "key_path": "~/.ssh/id_rsa",
                "security_group": "ssh-access",
                "network": "test-network",
            }
        }
    }

    conn = MagicMock()
    conn.compute = mock_driver
    conn.network = mock_driver

    with patch.object(
        OpenstackManager,
        "_get_sdk_conn",
        return_value=conn,
    ):
        p = OpenstackManager(
            config,
            cloud_name="test-openstack",
        )
        p._test_conn = conn
        yield p


def test_start_uses_configured_key_and_security_group(
    provider,
    mock_driver,
):
    """VM creation should use the configured key, security group, and network."""

    image = MagicMock()
    image.id = "image-123"
    image.name = "test-image"
    mock_driver.find_image.return_value = image

    flavor = MagicMock()
    flavor.id = "flavor-123"
    flavor.name = "test-flavor"
    mock_driver.find_flavor.return_value = flavor

    security_group = MagicMock()
    security_group.id = "sg-123"
    security_group.name = "ssh-access"
    mock_driver.find_security_group.return_value = security_group

    node = MagicMock()
    node.id = "vm-123"
    node.name = "test-vm"
    mock_driver.create_server.return_value = node

    with patch.object(
        provider,
        "wait_for_active",
        return_value=True,
    ), patch.object(
        provider,
        "assign_floating_ip",
        return_value="1.2.3.4",
    ), patch.object(
        provider,
        "wait_for_login",
        return_value=True,
    ):
        result = provider.start(name="test-vm")

    assert result == "vm-123"

    mock_driver.create_server.assert_called_once_with(
        name="test-vm",
        image_id=image.id,
        flavor_id=flavor.id,
        key_name="id_rsa",
        security_groups=[{"name": "ssh-access"}],
        networks=[{"uuid": "test-network"}],
    )


def test_start_does_not_create_vm_when_security_group_is_missing(
    provider,
    mock_driver,
):
    """VM creation should fail before boot if the configured security group is missing."""

    provider.config["clouds"]["test-openstack"][
        "security_group"
    ] = "missing-group"

    image = MagicMock()
    image.id = "image-123"
    image.name = "test-image"
    mock_driver.find_image.return_value = image

    flavor = MagicMock()
    flavor.id = "flavor-123"
    flavor.name = "test-flavor"
    mock_driver.find_flavor.return_value = flavor

    # OpenStack SDK returns None when the group is not found.
    mock_driver.find_security_group.return_value = None

    with pytest.raises(
        VMProviderError,
        match="Could not find security group missing-group",
    ):
        provider.start(name="test-vm")

    mock_driver.create_server.assert_not_called()


def test_start_prefers_explicit_key_name(
    provider,
    mock_driver,
):
    """An explicit key_name should override the key name derived from key_path."""

    provider.config["clouds"]["test-openstack"][
        "key_name"
    ] = "custom-cloud-key"

    image = MagicMock()
    image.id = "image-123"
    image.name = "test-image"
    mock_driver.find_image.return_value = image

    flavor = MagicMock()
    flavor.id = "flavor-123"
    flavor.name = "test-flavor"
    mock_driver.find_flavor.return_value = flavor

    security_group = MagicMock()
    security_group.id = "sg-123"
    security_group.name = "ssh-access"
    mock_driver.find_security_group.return_value = security_group

    node = MagicMock()
    node.id = "vm-123"
    node.name = "test-vm"
    mock_driver.create_server.return_value = node

    with patch.object(
        provider,
        "wait_for_active",
        return_value=True,
    ), patch.object(
        provider,
        "assign_floating_ip",
        return_value="1.2.3.4",
    ), patch.object(
        provider,
        "wait_for_login",
        return_value=True,
    ):
        result = provider.start(name="test-vm")

    assert result == "vm-123"

    assert (
        mock_driver.create_server.call_args.kwargs["key_name"]
        == "custom-cloud-key"
    )


def test_get_provider_info_uses_supported_configuration_fields(
    provider,
):
    """Provider info should expose supported, non-sensitive OpenStack fields."""

    conn = MagicMock()
    conn.region = "IU"
    conn.auth.auth_url = "https://example.invalid/v3/"

    with patch.object(
        provider,
        "_get_sdk_conn",
        return_value=conn,
    ), patch(
        "cloudmesh.ai.vm.openstack.OpenstackManager.OpenstackManager.version",
        new_callable=PropertyMock,
    ) as mock_version:
        mock_version.return_value = [
            "SDK: test",
        ]

        info = provider.get_provider_info()

    assert info["provider"] == "OpenStack"
    assert info["cloud_name"] == "test-openstack"
    assert info["region"] == "IU"
    assert info["auth_url"] == "https://example.invalid/v3/"
