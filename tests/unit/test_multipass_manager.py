import json
import re
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from cloudmesh.ai.vm.exceptions import VMResourceError
from cloudmesh.ai.vm.local.MultipassManager import Provider


@pytest.fixture
def mock_config():
    return {
        "clouds": {
            "multipass": {
                "image": "22.04",
                "cpus": 2,
                "memory": "4GiB",
                "disk": "20GiB",
            }
        }
    }


@pytest.fixture
def provider(mock_config):
    p = Provider(mock_config)
    p._run_command = MagicMock()
    return p


def command_result(stdout=""):
    """Create a simple mocked command result."""
    return SimpleNamespace(stdout=stdout)


def multipass_list_json(
    name="test-vm",
    state="Running",
    ip="192.168.64.5",
):
    """Return Multipass JSON output containing one VM."""
    return json.dumps(
        {
            "list": [
                {
                    "name": name,
                    "state": state,
                    "ipv4": [ip],
                }
            ]
        }
    )


def empty_multipass_list_json():
    """Return valid Multipass JSON containing no VMs."""
    return json.dumps({"list": []})


def test_start_with_name_and_config(provider):
    vm_name = "test-vm"

    def side_effect(command, **kwargs):
        if command == [
            "multipass",
            "list",
            "--format",
            "json",
        ]:
            return command_result(
                empty_multipass_list_json()
            )

        if command[0:2] == ["multipass", "launch"]:
            return command_result("")

        return command_result("")

    provider._run_command.side_effect = side_effect

    result = provider.start(name=vm_name)

    expected_command = [
        "multipass",
        "launch",
        "-c",
        "2",
        "-m",
        "4GiB",
        "-d",
        "20GiB",
        "-n",
        vm_name,
        "22.04",
    ]

    provider._run_command.assert_any_call(
        expected_command,
        stream=True,
    )

    assert result == vm_name


def test_start_without_name(provider):
    def side_effect(command, **kwargs):
        if command[0:2] == ["multipass", "launch"]:
            return command_result(
                "Launched: generated-vm\n"
            )

        return command_result("")

    provider._run_command.side_effect = side_effect

    result = provider.start()

    expected_command = [
        "multipass",
        "launch",
        "-c",
        "2",
        "-m",
        "4GiB",
        "-d",
        "20GiB",
        "22.04",
    ]

    provider._run_command.assert_any_call(
        expected_command,
        stream=True,
    )

    assert result == "generated-vm"


def test_stop_success(provider):
    def side_effect(command, **kwargs):
        if command == [
            "multipass",
            "list",
            "--format",
            "json",
        ]:
            return command_result(
                multipass_list_json()
            )

        return command_result("")

    provider._run_command.side_effect = side_effect

    assert provider.stop(name="test-vm") is True

    provider._run_command.assert_any_call(
        ["multipass", "stop", "test-vm"]
    )


def test_stop_failure(provider):
    def side_effect(command, **kwargs):
        if command == [
            "multipass",
            "list",
            "--format",
            "json",
        ]:
            return command_result(
                empty_multipass_list_json()
            )

        return command_result("")

    provider._run_command.side_effect = side_effect

    with pytest.raises(VMResourceError):
        provider.stop(name="non-existent")


def test_delete_success(provider):
    def side_effect(command, **kwargs):
        if command == [
            "multipass",
            "list",
            "--format",
            "json",
        ]:
            return command_result(
                multipass_list_json()
            )

        return command_result("")

    provider._run_command.side_effect = side_effect

    assert provider.delete(name="test-vm") is True

    provider._run_command.assert_any_call(
        [
            "multipass",
            "delete",
            "--purge",
            "test-vm",
        ]
    )


def test_list_parsing(provider):
    mock_output = json.dumps(
        {
            "list": [
                {
                    "name": "vm-1",
                    "state": "Running",
                    "ipv4": ["192.168.64.5"],
                },
                {
                    "name": "vm-2",
                    "state": "Stopped",
                    "ipv4": ["192.168.64.6"],
                },
            ]
        }
    )

    provider._run_command.return_value = (
        command_result(mock_output)
    )

    vms = provider.list()

    assert len(vms) == 2

    assert vms[0]["name"] == "vm-1"
    assert vms[0]["status"] == "Running"
    assert vms[0]["ip"] == "192.168.64.5"

    assert vms[1]["name"] == "vm-2"
    assert vms[1]["status"] == "Stopped"
    assert vms[1]["ip"] == "192.168.64.6"

    provider._run_command.assert_called_once_with(
        [
            "multipass",
            "list",
            "--format",
            "json",
        ],
        stream=False,
    )


def test_restart_success(provider):
    def side_effect(command, **kwargs):
        if command == [
            "multipass",
            "list",
            "--format",
            "json",
        ]:
            return command_result(
                multipass_list_json()
            )

        return command_result("")

    provider._run_command.side_effect = side_effect

    assert provider.restart(name="test-vm") is True

    provider._run_command.assert_any_call(
        ["multipass", "stop", "test-vm"]
    )

    provider._run_command.assert_any_call(
        ["multipass", "start", "test-vm"]
    )


def test_getters(provider):
    flavors = provider.get_flavors()

    assert isinstance(flavors, list)
    assert len(flavors) > 0
    assert "name" in flavors[0]

    keys = provider.get_keys()

    assert isinstance(keys, list)
    assert len(keys) > 0
    assert "name" in keys[0]

    security_groups = provider.get_security_groups()

    assert isinstance(security_groups, list)
    assert len(security_groups) > 0
    assert security_groups[0]["name"] == "default"


def test_upload_key_escaping(
    provider,
    tmp_path,
):
    key_content = (
        "ssh-rsa AAAAB3Nza... "
        "'quote' ... user@host"
    )

    key_file = tmp_path / "id_rsa.pub"
    key_file.write_text(key_content)

    key_name = "my'key'name"
    vm_name = "test-vm"

    assert (
        provider.upload_key(
            str(key_file),
            key_name,
            vm_name,
        )
        is True
    )

    escaped_key = key_content.replace(
        "'",
        "'\\''",
    )

    escaped_name = key_name.replace(
        "'",
        "'\\''",
    )

    expected_cmd_part = (
        "mkdir -p ~/.ssh && "
        "chmod 700 ~/.ssh && "
        "printf '%s\\n' "
        f"'{escaped_key} # {escaped_name}' "
        ">> ~/.ssh/authorized_keys && "
        "chmod 600 ~/.ssh/authorized_keys"
    )

    provider._run_command.assert_called_with(
        [
            "multipass",
            "exec",
            vm_name,
            "--",
            "bash",
            "-c",
            expected_cmd_part,
        ]
    )


def test_delete_key_escaping(provider):
    key_name = "my/key'name"
    vm_name = "test-vm"

    assert (
        provider.delete_key(
            key_name,
            vm_name,
        )
        is True
    )

    escaped_key_name = re.escape(
        key_name
    ).replace(
        "/",
        r"\/",
    )

    expected_cmd = [
        "multipass",
        "exec",
        vm_name,
        "--",
        "bash",
        "-c",
        'sed -i "/$1/d" ~/.ssh/authorized_keys',
        "bash",
        escaped_key_name,
    ]

    provider._run_command.assert_called_with(
        expected_cmd
    )
