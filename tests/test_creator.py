"""Test the creator object's methods."""

import os
from django_template.project_creator import ProjectCreator
from pathlib import Path

def test_yes(monkeypatch, tmp_path):
    creator = ProjectCreator(tmp_path, config={})
    with monkeypatch.context() as m:
        m.setattr("builtins.input", lambda _: "y")
        assert creator.yes("Question?")

    with monkeypatch.context() as m:
        m.setattr("builtins.input", lambda _: "n")
        assert not creator.yes("Question?")


def test_ask_questions(monkeypatch, tmp_path):
    creator = ProjectCreator(tmp_path, config={})
    with monkeypatch.context() as m:
        m.setattr("builtins.input", lambda _: "n")
        responses = creator.ask_questions()
        assert len(responses.keys()) == 3


def test_run(monkeypatch, tmp_path):
    creator = ProjectCreator(tmp_path, config={})
    dest_dir = creator.run()
    assert os.path.isdir(dest_dir)
    assert len(sorted(Path(dest_dir).glob('**/manage.py'))) == 1
    assert len(sorted(Path(dest_dir).glob('**/prod.py'))) == 1

def test_run_uswds(monkeypatch, tmp_path):
    creator = ProjectCreator(tmp_path, config={})
    creator.config['uswds'] = 'y'
    dest_dir = creator.run()
    assert os.path.isdir(dest_dir)
    assert len(sorted(Path(dest_dir).glob('**/gulpfile.js'))) == 3 # 3 copies get created due to npm commands
