"""Test template script."""

import pytest

from subprocess import check_call, CalledProcessError

from django_template import ProjectCreator


@pytest.fixture
def creator(tmp_path):
    yield ProjectCreator(tmp_path, config={"uswds": True})


def _check_npm_present():
    """Return true if Node.js is available."""
    try:
        check_call(["node", "-v"])
    except CalledProcessError:
        return False
    return True


npm_is_present = pytest.mark.skipif(
    not _check_npm_present(), reason="Test requires node to be installed"
)


def exists_and_non_empty(path):
    """Return True if the path exists and the file isn't empty."""
    return path.exists() and path.stat().st_size > 0


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
        assert exists_and_non_empty(filepath)


def test_git_initialize(creator):
    creator.initialize_git()
    assert (creator.dest_dir / ".git").exists()


def test_git_initialize_twice(creator):
    creator.initialize_git()
    assert (creator.dest_dir / ".git").exists()
    creator.initialize_git()


def test_gitignore_exists(creator):
    creator.get_gitignore()
    filepath = creator.dest_dir / ".gitignore"
    assert exists_and_non_empty(filepath)


def test_precommit_hook_exists(creator):
    creator.initialize_git()
    creator.setup_precommit_hook()
    hook_path = creator.dest_dir / ".git" / "hooks" / "pre-commit"
    assert exists_and_non_empty(hook_path)


def test_django_app_created(creator):
    creator.create_django_app()
    app_location = creator.dest_dir / creator.app_name
    assert app_location.exists()
    assert app_location.is_dir()
    assert (app_location / "manage.py").exists()
    assert (app_location / creator.app_name).exists()
    assert (app_location / creator.app_name).is_dir()

    assert (creator.dest_dir / "Pipfile").exists()

    templates_dir = app_location / creator.app_name / "templates"
    assert templates_dir.exists()
    assert (templates_dir / "base.html").exists()

    logs_dir = app_location / creator.app_name / "logs"
    assert logs_dir.exists()
    assert (logs_dir / ".gitkeep").exists()


def test_django_settings_directory(creator):
    creator.create_django_app()
    creator._make_settings_directory()
    app_dir = creator.dest_dir / creator.app_name / creator.app_name
    assert not (app_dir / "settings.py").exists()
    assert (app_dir / "settings" / "__init__.py").exists()
    assert (app_dir / "settings" / "base.py").exists()

    # no secret key in base.py
    with open(app_dir / "settings" / "base.py", "r") as f:
        assert "SECRET_KEY" not in f.read()


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


@npm_is_present
def test_npm(creator):
    creator.set_up_npm()
    assert (creator.dest_dir / "package.json").exists()
    assert (creator.dest_dir / "package-lock.json").exists()
    node_modules_path = creator.dest_dir / "node_modules"
    assert node_modules_path.exists()
    assert node_modules_path.is_dir()


@npm_is_present
def test_uswds(creator):
    creator.set_up_npm()
    creator.set_up_uswds_templates()
    assert (creator.dest_dir / "gulpfile.js").exists()
    assert (
        creator.dest_dir
        / creator.app_name
        / creator.app_name
        / "static"
        / "css"
        / "styles.css"
    ).exists()
    assert (
        creator.dest_dir
        / creator.app_name
        / creator.app_name
        / "static"
        / "js"
        / "uswds.min.js"
    ).exists()


def test_circleci(creator):
    creator.set_up_circleci()
    assert (creator.dest_dir / ".circleci").exists()
    assert (creator.dest_dir / ".circleci" / "config.yml").exists()


def test_github_actions(creator):
    creator.set_up_github_actions()
    assert (creator.dest_dir / ".github" / "actions").exists()
    assert (creator.dest_dir / ".github" / "workflows").exists()
