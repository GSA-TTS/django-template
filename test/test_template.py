
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

def test_django_settings_directory(creator):
    creator.create_django_app()
    creator._make_settings_directory()
    app_dir = creator.dest_dir / creator.app_name / creator.app_name
    assert not (app_dir / "settings.py").exists()
    assert (app_dir / "settings" / "__init__.py").exists()
    assert (app_dir / "settings" / "base.py").exists()

def test_django_settings_directory_twice(creator):
    creator.create_django_app()
    creator._make_settings_directory()
    creator._make_settings_directory()

def test_prod_settings(creator):
    creator.create_django_app()
    creator.make_prod_settings()
    settings_dir = creator.dest_dir / creator.app_name / creator.app_name / "settings"
    assert (settings_dir / "prod.py").exists()

def test_dev_settings(creator):
    creator.create_django_app()
    creator.make_dev_settings()
    settings_dir = creator.dest_dir / creator.app_name / creator.app_name / "settings"
    assert (settings_dir / "dev.py").exists()
