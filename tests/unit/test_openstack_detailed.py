from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from cloudmesh.ai.vm.openstack.OpenstackManager import OpenstackManager


MOCK_CONFIG = {
    "clouds": {
        "test-openstack": {
            "image": "test-image",
            "flavor": "test-flavor",
            "auth_url": "https://example.invalid/v3/",
            "region_name": "RegionOne",
            "floating_ip_pool": "public",
        }
    }
}


@pytest.fixture
def provider():
    return OpenstackManager(
        MOCK_CONFIG,
        cloud_name="test-openstack",
    )


def test_list_sdk_success(provider):
    conn = MagicMock()

    server = SimpleNamespace(
        name="vm1",
        id="id1",
        status="ACTIVE",
        addresses={
            "private": [{"addr": "10.0.0.1"}],
            "floating": [{"addr": "1.2.3.4"}],
        },
        image=SimpleNamespace(name="img1"),
        flavor=SimpleNamespace(name="flv1"),
    )

    conn.compute.servers.return_value = [server]

    with patch.object(provider, "_get_sdk_conn", return_value=conn):
        vms = provider.list()

    assert len(vms) == 1
    assert vms[0]["name"] == "vm1"
    assert vms[0]["id"] == "id1"
    assert vms[0]["status"] == "ACTIVE"
    assert vms[0]["ip"] == "1.2.3.4"
    assert vms[0]["image"] == "img1"
    assert vms[0]["flavor"] == "flv1"


def test_get_floating_ip_success(provider):
    conn = MagicMock()

    server = SimpleNamespace(
        addresses={
            "private": [{"addr": "10.0.0.1"}],
            "floating": [{"addr": "1.2.3.4"}],
        }
    )

    conn.compute.find_server.return_value = server

    with patch.object(provider, "_get_sdk_conn", return_value=conn):
        ip = provider._get_floating_ip("test-vm")

    assert ip == "1.2.3.4"
    conn.compute.find_server.assert_called_once_with("test-vm")


def test_get_floating_ip_none(provider):
    conn = MagicMock()

    server = SimpleNamespace(
        addresses={
            "private": [{"addr": "10.0.0.1"}],
        }
    )

    conn.compute.find_server.return_value = server

    with patch.object(provider, "_get_sdk_conn", return_value=conn):
        ip = provider._get_floating_ip("test-vm")

    assert ip is None


def test_assign_floating_ip_success(provider):
    conn = MagicMock()

    node = SimpleNamespace(
        name="test-vm",
        id="id-123",
        private_ips=["10.0.0.1"],
    )

    pool = SimpleNamespace(
        id="public-network-id",
        name="public",
    )

    floating_ip = SimpleNamespace(
        floating_ip_address="1.2.3.4",
        fixed_ip=None,
    )

    conn.network.find_network.return_value = pool
    conn.network.create_floating_ip.return_value = floating_ip

    with patch.object(provider, "_find_node", return_value=node), \
         patch.object(provider, "wait_for_active", return_value=True), \
         patch.object(provider, "_wait_for_network", return_value=True), \
         patch.object(provider, "_get_sdk_conn", return_value=conn), \
         patch.object(
             provider,
             "get_cloud_config",
             return_value={"floating_ip_pool": "public"},
         ):

        ip = provider.assign_floating_ip("test-vm")

    assert ip == "1.2.3.4"

    conn.network.find_network.assert_called_once_with("public")

    conn.network.create_floating_ip.assert_called_once_with(
        floating_network_id="public-network-id"
    )

    conn.compute.add_floating_ip_to_server.assert_called_once_with(
        node,
        floating_ip,
    )


def test_assign_floating_ip_vm_not_found(provider):
    with patch.object(provider, "_find_node", return_value=None):
        result = provider.assign_floating_ip("missing-vm")

    assert result is None


def test_release_floating_ip_success(provider):
    conn = MagicMock()

    node = SimpleNamespace(
        name="test-vm",
        id="id-123",
        public_ips=["1.2.3.4"],
    )

    floating_ip = SimpleNamespace(
        floating_ip_address="1.2.3.4"
    )

    conn.network.find_floating_ip.return_value = floating_ip

    with patch.object(provider, "_find_node", return_value=node), \
         patch.object(provider, "_get_sdk_conn", return_value=conn):

        result = provider.release_floating_ip("test-vm")

    assert result is True

    conn.network.find_floating_ip.assert_called_once_with("1.2.3.4")

    conn.compute.remove_floating_ip_from_server.assert_called_once_with(
        node,
        floating_ip,
    )

    conn.network.delete_floating_ip.assert_called_once_with(
        floating_ip
    )


def test_release_floating_ip_without_public_ip(provider):
    node = SimpleNamespace(
        name="test-vm",
        id="id-123",
        public_ips=[],
    )

    with patch.object(provider, "_find_node", return_value=node):
        result = provider.release_floating_ip("test-vm")

    assert result is False
