from rich.text import Text
from typer.testing import CliRunner

from hostlens.cli import app
from hostlens.client import HostLens
from hostlens.models import DeviceFound, DeviceProfile, ScanCompleted, ScanSummary


def test_cli_help_lists_public_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "identify" in result.stdout
    assert "scan" in result.stdout
    assert "watch" in result.stdout


def test_cli_rejects_conflicting_profiles() -> None:
    result = CliRunner().invoke(app, ["scan", "--fast", "--deep"], color=True)

    assert result.exit_code != 0
    output = Text.from_ansi(result.output).plain
    assert "either --fast or --deep" in output


def test_cli_accepts_positional_subnets(monkeypatch) -> None:
    async def scan_stream(self, subnet, *, mode):
        assert subnet == "192.168.1.0/24"
        yield ScanCompleted(
            summary=ScanSummary(
                duration=0,
                targets_checked=254,
                devices_found=0,
                mode=str(mode),
            )
        )

    async def discover(self, subnet):
        assert subnet == "192.168.1.0/24"
        return []

    async def watch_network(self, subnet):
        assert subnet == "192.168.1.0/24"
        yield DeviceFound(device=DeviceProfile(ip="192.168.1.1"))

    monkeypatch.setattr(HostLens, "scan_stream", scan_stream)
    monkeypatch.setattr(HostLens, "discover", discover)
    monkeypatch.setattr(HostLens, "watch_network", watch_network)

    runner = CliRunner()
    for command in ("scan", "discover", "watch"):
        result = runner.invoke(app, [command, "192.168.1.0/24"])
        assert result.exit_code == 0, result.output
