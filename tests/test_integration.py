"""Test the resulting project for correctness."""

import time

from contextlib import contextmanager
from subprocess import CalledProcessError

import pytest

from django_template.project_creator import ProjectCreator


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    this_dir = tmp_path_factory.mktemp("test-proj")
    creator = ProjectCreator(this_dir, config={"uswds": True})
    # run the entire creation process
    creator.run()

    # have to manually pipenv install
    creator.exec_in_destination(["pipenv", "install"])

    yield creator


def test_docker_compose_build(project):
    """Can run docker_compose build."""
    project.exec_in_destination(["docker-compose", "build"])


def test_docker_tests(project):
    """Can run tests in docker."""
    project.exec_in_destination(
        [
            "docker-compose",
            "run",
            "app",
            "python",
            "manage.py",
            "migrate",
        ]
    )
    project.exec_in_destination(
        [
            "docker-compose",
            "run",
            "app",
            "python",
            "manage.py",
            "test",
        ]
    )


@contextmanager
def _docker_up(project):
    try:
        project.exec_in_destination(
            # run in daemon mode
            ["docker-compose", "up", "-d"]
        )
        # that might take a while to get up and running, let's just wait
        # a magic number of seconds. TODO: use a better waiting method
        time.sleep(5)
        yield
    finally:
        project.exec_in_destination(["docker-compose", "stop"])


def test_page_load(project):
    """Can load page running in Docker."""
    with _docker_up(project):
        project.exec_in_destination(["curl", "--fail", "localhost:8000"])


def test_nonexistent_page(project):
    """Loading a non-existent page gives an HTTP error code."""
    with _docker_up(project):
        with pytest.raises(CalledProcessError):
            project.exec_in_destination(
                ["curl", "--fail", "localhost:8000/not/a/valid/url"]
            )
