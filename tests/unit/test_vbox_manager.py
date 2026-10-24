import pytest
from unittest.mock import MagicMock, patch
from cloudmesh.ai.vm.local.VBoxManager import Provider


VM_UUID = "12345678-1234-1234-1234-123456789abc"
VM_UUID_2 = "abcdef12-3456-7890-abcd-ef1234567890"


@pytest.fixture
def mock_config():
    return {
        "clouds": {
            "vbox": {}
        }
    }


@pytest.fixture
def provider(mock_config):
    p = Provider(mock_config)
    p._run_command = MagicMock()
    return p


def test_start_success(provider):
    provider._run_command.side_effect = [
        MagicMock(
            stdout=f'"vbox-vm" {{{VM_UUID}}}\n',
            returncode=0,
        ),
        MagicMock(
            stdout="Started",
            returncode=0,
        ),
    ]

    assert provider.start(name="vbox-vm") == "vbox-vm"

    assert provider._run_command.call_count == 2

    provider._run_command.assert_any_call(
        ["VBoxManage", "list", "vms"]
    )

    provider._run_command.assert_any_call(
        [
            "VBoxManage",
            "startvm",
            "vbox-vm",
            "--type",
            "headless",
        ]
    )


def test_stop_success(provider):
    provider._run_command.side_effect = [
        MagicMock(
            stdout=f'"vbox-vm" {{{VM_UUID}}}\n',
            returncode=0,
        ),
        MagicMock(
            stdout="Stopped",
            returncode=0,
        ),
    ]

    assert provider.stop(name="vbox-vm") is True

    assert provider._run_command.call_count == 2

    provider._run_command.assert_any_call(
        ["VBoxManage", "list", "vms"]
    )

    provider._run_command.assert_any_call(
        [
            "VBoxManage",
            "controlvm",
            "vbox-vm",
            "poweroff",
        ]
    )


def test_delete_success(provider):
    provider._run_command.side_effect = [
        MagicMock(
            stdout=f'"vbox-vm" {{{VM_UUID}}}\n',
            returncode=0,
        ),
        MagicMock(
            stdout="Deleted",
            returncode=0,
        ),
    ]

    assert provider.delete(name="vbox-vm") is True

    assert provider._run_command.call_count == 2

    provider._run_command.assert_any_call(
        ["VBoxManage", "list", "vms"]
    )

    provider._run_command.assert_any_call(
        [
            "VBoxManage",
            "unregistervm",
            "vbox-vm",
            "--delete",
        ]
    )


def test_list_parsing(provider):
    mock_output = (
        f'"VM 1" {{{VM_UUID}}}\n'
        f'"VM 2" {{{VM_UUID_2}}}\n'
    )

    provider._run_command.return_value = MagicMock(
        stdout=mock_output,
        returncode=0,
    )

    vms = provider.list()

    assert len(vms) == 2

    assert vms[0]["name"] == "VM 1"
    assert vms[0]["uuid"] == VM_UUID

    assert vms[1]["name"] == "VM 2"
    assert vms[1]["uuid"] == VM_UUID_2

    provider._run_command.assert_called_once_with(
        ["VBoxManage", "list", "vms"]
    )


def test_suspend_success(provider):
    provider._run_command.side_effect = [
        MagicMock(
            stdout=f'"vbox-vm" {{{VM_UUID}}}\n',
            returncode=0,
        ),
        MagicMock(
            stdout="Suspended",
            returncode=0,
        ),
    ]

    assert provider.suspend(name="vbox-vm") is True

    assert provider._run_command.call_count == 2

    provider._run_command.assert_any_call(
        ["VBoxManage", "list", "vms"]
    )

    provider._run_command.assert_any_call(
        [
            "VBoxManage",
            "controlvm",
            "vbox-vm",
            "savestate",
        ]
    )


def test_restart_success(provider):
    with patch.object(
        provider,
        "exists",
        return_value=True,
    ):
        provider._run_command.return_value = MagicMock(
            stdout="",
            returncode=0,
        )

        assert provider.restart(name="vbox-vm") is True

    assert provider._run_command.call_count == 2

    provider._run_command.assert_any_call(
        [
            "VBoxManage",
            "controlvm",
            "vbox-vm",
            "poweroff",
        ]
    )

    provider._run_command.assert_any_call(
        [
            "VBoxManage",
            "startvm",
            "vbox-vm",
            "--type",
            "headless",
        ]
    )
