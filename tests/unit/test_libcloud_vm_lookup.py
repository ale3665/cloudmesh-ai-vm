"""Regression tests for provider-independent Libcloud VM lookup."""

from types import SimpleNamespace

from cloudmesh.ai.vm.LibcloudManager import LibcloudManager


class FakeManager(LibcloudManager):
    def _get_driver(self):
        return None


def make_manager(nodes):
    manager = object.__new__(FakeManager)
    manager.cloud_name = "synthetic"
    manager.driver = SimpleNamespace(list_nodes=lambda: nodes)
    return manager


def test_lookup_by_id():
    node = SimpleNamespace(id="vm-123", name="research")
    manager = make_manager([node])

    assert manager.get_vm("vm-123") is node


def test_lookup_by_name():
    node = SimpleNamespace(id="vm-123", name="research")
    manager = make_manager([node])

    assert manager.get_vm("research") is node


def test_lookup_missing_node():
    manager = make_manager([])

    assert manager.get_vm("missing") is None


def test_exact_id_has_priority_over_name():
    name_match = SimpleNamespace(id="vm-456", name="vm-123")
    id_match = SimpleNamespace(id="vm-123", name="research")

    manager = make_manager([name_match, id_match])

    assert manager.get_vm("vm-123") is id_match


def test_exact_id_priority_with_reversed_order():
    id_match = SimpleNamespace(id="vm-123", name="research")
    name_match = SimpleNamespace(id="vm-456", name="vm-123")

    manager = make_manager([id_match, name_match])

    assert manager.get_vm("vm-123") is id_match


def test_duplicate_names_return_first_match():
    first = SimpleNamespace(id="vm-101", name="shared-name")
    second = SimpleNamespace(id="vm-202", name="shared-name")

    manager = make_manager([first, second])

    assert manager.get_vm("shared-name") is first
