import json
import subprocess
from unittest.mock import patch

from cloudmesh.ai.vm.openstack.OpenstackManager import OpenstackManager


def make_provider():
    return OpenstackManager(
        {"clouds": {"jetstream": {}}},
        cloud_name="jetstream",
    )


def test_provider_info_parses_completed_process():
    provider = make_provider()

    output = json.dumps({
        "region_name": "test-region",
        "auth.auth_url": "https://example.invalid/v3",
    })

    result = subprocess.CompletedProcess(
        args=["openstack"],
        returncode=0,
        stdout=output,
        stderr="",
    )

    with patch.object(
        provider, "_run_cli_command", return_value=result
    ):
        info = provider.get_provider_info()

    assert info["region"] == "test-region"
    assert info["auth_url"] == "https://example.invalid/v3"


def test_provider_info_reports_cli_failure_without_secrets():
    provider = make_provider()

    with patch.object(
        provider,
        "_run_cli_command",
        side_effect=RuntimeError(
            "OpenStack CLI unavailable; password=private-value"
        ),
    ):
        info = provider.get_provider_info()

    assert info["cloud_name"] == "jetstream"
    assert info.get("diagnostic_warning")
    assert "private-value" not in str(info)
