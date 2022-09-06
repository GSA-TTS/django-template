"""Click command for 18f_django_template.py main function."""

import click

from .project_creator import ProjectCreator


@click.command()
@click.option(
    "--app-name",
    default=None,
    type=str,
    show_default=False,
    prompt="What is the name of your application",
    help="Name of the new application",
)
@click.option(
    "--uswds/--no-uswds",
    prompt="Would you like to install USWDS (requires node to already be installed)",
    help="Use USWDS in the new application",
)
@click.option(
    "--circleci/--no-circleci",
    prompt="Would you like to set up CircleCI for CI/CD",
    help="Configure CircleCI for the new application",
)
@click.option(
    "--github-actions/--no-github-actions",
    prompt="Would you like to set up Github Actions for CI/CD",
    help="Configure Github Actions for the new application",
)
@click.option(
    "--cloud-gov-terraform/--no-cloud-gov-terraform",
    prompt="Create terrform scripts for cloud.gov infrastructure",
    help="Configure Terraform for cloud.gov infrastructure",
)
@click.option(
    "--cloud-gov-organization",
    default="ORGANIZATION",
    help="Cloud.gov organization name",
)
@click.option(
    "--cloud-gov-staging-space",
    default="staging",
    help="Cloud.gov space to use for staging",
)
@click.option(
    "--cloud-gov-production-space",
    default="prod",
    help="Cloud.gov space to use for production",
)
def template_command(
    app_name,
    uswds,
    circleci,
    github_actions,
    cloud_gov_terraform,
    cloud_gov_organization,
    cloud_gov_staging_space,
    cloud_gov_production_space,
):
    """Run the command line script."""
    config = {
        "uswds": uswds,
        "circleci": circleci,
        "github_actions": github_actions,
        "cloud_gov_terraform": cloud_gov_terraform,
        "cloud_gov": {
            "organization": cloud_gov_organization,
            "staging_space": cloud_gov_staging_space,
            "production_space": cloud_gov_production_space,
        },
    }
    ProjectCreator(dest_dir=app_name, config=config).run()
    return 0  # successful exit code
