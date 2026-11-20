"""Tests for AWS EC2 instance lookup using Apache Libcloud."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from cloudmesh.ai.vm.aws.AwsManager import Provider


def make_provider():
    driver = MagicMock()
    with patch(
        "cloudmesh.ai.vm.aws.AwsManager.get_driver",
        return_value=MagicMock(return_value=driver),
    ):
        provider = Provider({
            "clouds": {
                "aws": {
                    "access_key": "test-access",
                    "secret_key": "test-secret",
                    "region": "us-east-1",
                }
            }
        })
    return provider, driver


def test_lookup_by_instance_id():
    provider, driver = make_provider()
    node = SimpleNamespace(id="i-123", name="research-server")
    driver.list_nodes.return_value = [node]

    assert provider._find_node("i-123") is node


def test_lookup_by_name():
    provider, driver = make_provider()
    node = SimpleNamespace(id="i-123", name="research-server")
    driver.list_nodes.return_value = [node]

    assert provider._find_node("research-server") is node


def test_lookup_prioritizes_instance_id_over_name():
    provider, driver = make_provider()

    collision = SimpleNamespace(id="i-456", name="i-123")
    correct = SimpleNamespace(id="i-123", name="research-server")

    driver.list_nodes.return_value = [collision, correct]

    assert provider._find_node("i-123") is correct


def test_lookup_rejects_unmatched_instance_id():
    provider, driver = make_provider()
    driver.list_nodes.return_value = [
        SimpleNamespace(id="i-456", name="i-123")
    ]

    assert provider._find_node("i-123") is None


def test_delete_does_not_terminate_unrelated_instance():
    provider, driver = make_provider()
    driver.list_nodes.return_value = [
        SimpleNamespace(id="i-456", name="another-server")
    ]

    assert provider.delete("missing-server") is False
    driver.destroy_node.assert_not_called()


def test_stop_does_not_stop_unrelated_instance():
    provider, driver = make_provider()
    driver.list_nodes.return_value = [
        SimpleNamespace(id="i-456", name="another-server")
    ]

    assert provider.stop("missing-server") is False
    driver.stop_node.assert_not_called()
