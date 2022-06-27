
"""Test template script."""

import os

import pytest

from django_template import ProjectCreator


@pytest.fixture
def creator(tmp_path):
    yield ProjectCreator(tmp_path)

def test_dir_exists(creator):
    creator._ensure_destination_exists()
    assert creator.dest_dir.exists()

def test_readme_exists(creator):
    creator.create_readme()
    assert (creator.dest_dir / "README.md").exists()
    # file is non-empty
    assert (creator.dest_dir / "README.md").stat().st_size > 0

def test_policy_files_exist(creator):
    creator.get_policy_files()
    for filename in ["CONTRIBUTING.md", "LICENSE.md"]:
        filepath = creator.dest_dir / filename
        assert filepath.exists()
        # file is non-empty
        assert filepath.stat().st_size > 0

def test_django_app_created(creator):
    creator.create_django_app()
    app_location = creator.dest_dir / creator.app_name
    assert app_location.exists()
    assert app_location.is_dir()
    assert (app_location / "manage.py").exists()
    assert (app_location / creator.app_name).exists()
    assert (app_location / creator.app_name).is_dir()
