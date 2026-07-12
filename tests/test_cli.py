from skill_lab import __version__
from skill_lab.cli import run


def test_version_flag(capsys):
    assert run(["--version"]) == 0
    assert capsys.readouterr().out.strip() == f"skilllab {__version__}"


def test_smoke_test(capsys):
    assert run(["--smoke-test"]) == 0
    assert capsys.readouterr().out.strip() == "Skill Lab app constructed successfully"
