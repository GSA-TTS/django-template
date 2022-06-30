
"""Test the creator object's methods."""

from django_template.project_creator import ProjectCreator

def test_yes(monkeypatch, tmp_path):
    creator = ProjectCreator(tmp_path, config={})
    with monkeypatch.context() as m:
        m.setattr("builtins.input", lambda _: "y")
        assert creator.yes("Question?")

    with monkeypatch.context() as m:
        m.setattr("builtins.input", lambda _: "n")
        assert not creator.yes("Question?")
