from typer.testing import CliRunner
from apps.cli.main import app

runner = CliRunner()


def test_cli_doctor():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "MailRadar Diagnostics" in result.output
    assert "Database Connection" in result.output


def test_cli_config_init():
    result = runner.invoke(app, ["config", "init"])
    assert result.exit_code == 0
    assert "Initialized configuration" in result.output


def test_cli_projects_list():
    result = runner.invoke(app, ["projects", "list"])
    assert result.exit_code == 0
    assert "Tracked Projects" in result.output


def test_cli_suppression_list():
    result = runner.invoke(app, ["suppression", "list"])
    assert result.exit_code == 0
    assert "Suppressed Addresses" in result.output
