"""Regression tests for AWS EC2 instance identity matching."""

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


def test_lookup_rejects_unrelated_get_node_result():
    provider, driver = make_provider()

    wrong = SimpleNamespace(
        id="i-unrelated",
        name="other-instance",
    )
    correct = SimpleNamespace(
        id="i-target",
        name="target-instance",
    )

    driver.get_node.return_value = wrong
    driver.list_nodes.return_value = [wrong, correct]

    result = provider._find_node("target-instance")

    assert result is correct


def test_lookup_returns_none_when_no_identity_matches():
    provider, driver = make_provider()

    wrong = SimpleNamespace(
        id="i-unrelated",
        name="other-instance",
    )

    driver.get_node.return_value = wrong
    driver.list_nodes.return_value = [wrong]

    assert provider._find_node("missing-instance") is None


def test_lookup_prefers_exact_instance_id():
    provider, driver = make_provider()

    name_collision = SimpleNamespace(
        id="i-other",
        name="i-target",
    )
    correct = SimpleNamespace(
        id="i-target",
        name="actual-instance",
    )

    driver.get_node.return_value = None
    driver.list_nodes.return_value = [name_collision, correct]

    assert provider._find_node("i-target") is correct


def test_delete_does_not_terminate_unrelated_instance():
    provider, driver = make_provider()

    wrong = SimpleNamespace(
        id="i-unrelated",
        name="other-instance",
    )

    driver.get_node.return_value = wrong
    driver.list_nodes.return_value = [wrong]

    result = provider.delete("target-instance")

    assert result is False
    driver.destroy_node.assert_not_called()


def test_stop_does_not_stop_unrelated_instance():
    provider, driver = make_provider()

    wrong = SimpleNamespace(
        id="i-unrelated",
        name="other-instance",
    )

    driver.get_node.return_value = wrong
    driver.list_nodes.return_value = [wrong]

    result = provider.stop("target-instance")

    assert result is False
    driver.stop_node.assert_not_called()
