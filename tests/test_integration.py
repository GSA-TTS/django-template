"""Test the resulting project for correctness."""

import subprocess
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

    # Try building the docker images here to make the later tests more
    # reliable.
    creator.exec_in_destination(["docker compose", "build"])

    yield creator


def _check_docker_running():
    """Return True if the Docker daemon is running."""
    try:
        output = subprocess.check_output(
            ["docker", "info", "-f", "{{json .ServerErrors}}"]
        )
    except CalledProcessError:
        return False

    # output is bytes, so need to decode it lossily into a string
    output = output.decode("ascii", "ignore")
    if output.startswith("null"):
        # no server errors so docker server is running
        return True
    return False


docker_is_running = pytest.mark.skipif(
    not _check_docker_running(), reason="Docker must be running for integration tests"
)


@docker_is_running
def test_docker_compose_build(project):
    """Can run docker_compose build."""
    project.exec_in_destination(["docker compose", "build"])


@docker_is_running
def test_docker_tests(project):
    """Can run tests in docker."""
    project.exec_in_destination(
        ["docker compose", "run", "app", "python", "manage.py", "migrate"]
    )
    project.exec_in_destination(
        ["docker compose", "run", "app", "python", "manage.py", "test"]
    )


@contextmanager
def _docker_up(project):
    try:
        project.exec_in_destination(
            # run in daemon mode
            ["docker compose", "up", "-d"]
        )
        # that might take a while to get up and running, let's just wait
        # a magic number of seconds. TODO: use a better waiting method
        time.sleep(5)
        yield
    finally:
        project.exec_in_destination(["docker compose", "stop"])


@docker_is_running
def test_page_load(project):
    """Can load page running in Docker."""
    with _docker_up(project):
        project.exec_in_destination(["curl", "--fail", "localhost:8000"])


@docker_is_running
def test_nonexistent_page(project):
    """Loading a non-existent page gives an HTTP error code."""
    with _docker_up(project):
        with pytest.raises(CalledProcessError):
            project.exec_in_destination(
                ["curl", "--fail", "localhost:8000/not/a/valid/url"]
            )
