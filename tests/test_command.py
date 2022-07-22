"""Test CLI command behavior."""

from django_template import template_command

def test_no_app_name(cli_runner):
    """No app_name prompts for name."""
    result = cli_runner.invoke(template_command, [], input="test-project\n\n\n\n")
    assert result.exit_code == 0
    assert "test-project" in result.output
    assert "test_project" in result.output

def test_all_options(cli_runner):
    """Giving all options requires no input."""
    result = cli_runner.invoke(
        template_command,
        ["--app-name=given-name",
         "--no-uswds",
         "--no-circleci",
         "--no-github-actions",
        ],
        input="")
    assert result.exit_code == 0
    assert "given-name" in result.output
    assert "given_name" in result.output
