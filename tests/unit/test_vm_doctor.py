from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from cloudmesh.ai.command.vm.doctor import doctor


def make_provider(
    requirements=True,
    validation=None,
    info=None,
):
    """Create a lightweight fake provider for doctor tests."""
    provider = SimpleNamespace()

    provider.cloud_name = "test-cloud"

    provider.check_requirements = MagicMock(
        return_value=requirements
    )

    provider.validate_config = MagicMock(
        return_value={} if validation is None else validation
    )

    provider.get_provider_info = MagicMock(
        return_value=(
            {"provider": "Test Provider"}
            if info is None
            else info
        )
    )

    return provider


def get_rows(mock_render):
    """Return the rows passed to render_table()."""
    return mock_render.call_args.args[2]


def test_doctor_healthy_provider():
    provider = make_provider()

    runner = CliRunner()

    with patch(
        "cloudmesh.ai.command.vm.doctor.get_active_provider",
        return_value=provider,
    ), patch(
        "cloudmesh.ai.command.vm.doctor.render_table"
    ) as mock_render:
        result = runner.invoke(doctor, [])

    assert result.exit_code == 0

    provider.check_requirements.assert_called_once()
    provider.validate_config.assert_called_once()
    provider.get_provider_info.assert_called_once()

    rows = get_rows(mock_render)

    assert len(rows) == 4
    assert "PASS" in rows[0][1]
    assert "PASS" in rows[1][1]
    assert "PASS" in rows[2][1]
    assert "PASS" in rows[3][1]


def test_doctor_skips_provider_info_when_requirements_fail():
    provider = make_provider(
        requirements=False
    )

    runner = CliRunner()

    with patch(
        "cloudmesh.ai.command.vm.doctor.get_active_provider",
        return_value=provider,
    ), patch(
        "cloudmesh.ai.command.vm.doctor.render_table"
    ) as mock_render:
        result = runner.invoke(doctor, [])

    assert result.exit_code == 0

    provider.check_requirements.assert_called_once()
    provider.validate_config.assert_called_once()

    # Runtime provider information must not be queried if the
    # provider requirements are unavailable.
    provider.get_provider_info.assert_not_called()

    rows = get_rows(mock_render)

    requirements_row = rows[1]
    provider_info_row = rows[3]

    assert requirements_row[0] == "Requirements"
    assert "FAIL" in requirements_row[1]

    assert provider_info_row[0] == "Provider Info"
    assert "SKIP" in provider_info_row[1]


def test_doctor_detects_configuration_errors():
    provider = make_provider(
        requirements=True,
        validation={
            "errors": [
                "Missing image",
                "Missing credentials",
            ]
        },
    )

    runner = CliRunner()

    with patch(
        "cloudmesh.ai.command.vm.doctor.get_active_provider",
        return_value=provider,
    ), patch(
        "cloudmesh.ai.command.vm.doctor.render_table"
    ) as mock_render:
        result = runner.invoke(doctor, [])

    assert result.exit_code == 0

    rows = get_rows(mock_render)

    configuration_row = rows[2]

    assert configuration_row[0] == "Configuration"
    assert "FAIL" in configuration_row[1]
    assert "Missing image" in configuration_row[2]
    assert "Missing credentials" in configuration_row[2]


def test_doctor_handles_provider_info_failure():
    provider = make_provider(
        requirements=True,
        validation={},
    )

    provider.get_provider_info.side_effect = RuntimeError(
        "provider information unavailable"
    )

    runner = CliRunner()

    with patch(
        "cloudmesh.ai.command.vm.doctor.get_active_provider",
        return_value=provider,
    ), patch(
        "cloudmesh.ai.command.vm.doctor.render_table"
    ) as mock_render:
        result = runner.invoke(doctor, [])

    assert result.exit_code == 0

    rows = get_rows(mock_render)

    provider_info_row = rows[3]

    assert provider_info_row[0] == "Provider Info"
    assert "FAIL" in provider_info_row[1]
    assert (
        "provider information unavailable"
        in provider_info_row[2]
    )


def test_doctor_strict_returns_nonzero_on_failure():
    provider = make_provider(
        requirements=False
    )

    runner = CliRunner()

    with patch(
        "cloudmesh.ai.command.vm.doctor.get_active_provider",
        return_value=provider,
    ), patch(
        "cloudmesh.ai.command.vm.doctor.render_table"
    ):
        result = runner.invoke(
            doctor,
            ["--strict"],
        )

    assert result.exit_code == 1

    provider.get_provider_info.assert_not_called()

    # Click's intentional exit must not be converted into
    # "Unexpected Error" by handle_errors.
    assert "Unexpected Error" not in result.output
    assert "Aborted!" not in result.output
