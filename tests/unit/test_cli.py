from typer.testing import CliRunner

from hostlens.cli import app


def test_cli_help_lists_public_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "identify" in result.stdout
    assert "scan" in result.stdout
    assert "watch" in result.stdout


def test_cli_rejects_conflicting_profiles() -> None:
    result = CliRunner().invoke(app, ["scan", "--fast", "--deep"])

    assert result.exit_code != 0
    assert "either --fast or --deep" in result.output
