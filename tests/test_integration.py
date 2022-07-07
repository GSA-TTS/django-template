
"""Test the resulting project for correctness."""

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
        ["docker-compose",
         "run",
         "app",
         "python",
         "manage.py",
         "test",
        ]
    )

