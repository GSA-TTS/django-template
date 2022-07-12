"""Test the creator object's methods."""

from pathlib import Path

from django_template.project_creator import ProjectCreator


def test_yes(monkeypatch, tmp_path):
    creator = ProjectCreator(tmp_path, config={})
    with monkeypatch.context() as m:
        m.setattr("builtins.input", lambda _: "y")
        assert creator.yes("Question?")

    with monkeypatch.context() as m:
        m.setattr("builtins.input", lambda _: "n")
        assert not creator.yes("Question?")

def test_ensure_path_exists_relative(tmp_path):
    creator = ProjectCreator(tmp_path, config={})
    creator._ensure_path_exists(Path("relative"))
    assert (creator.dest_dir / "relative").exists()

def test_ensure_path_exists_absolute(tmp_path):
    creator = ProjectCreator(tmp_path, config={})
    creator._ensure_path_exists(tmp_path / "subdirectory")
    assert (tmp_path.resolve() / "subdirectory").exists()

