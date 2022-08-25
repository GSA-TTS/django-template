import re
import subprocess

from pathlib import Path

from click import echo
from jinja2 import Environment, FileSystemLoader
from requests import get


class ProjectCreator:
    def __init__(self, dest_dir=None, config=None):

        """Create a ProjectCreator.

        For use off of the command line, pass in dest_dir and a config
        dictionary, otherwise interative questions will be used to determine
        these things.
        """

        if dest_dir is None:
            # destination wasn't given
            dest_dir = self.ask("What is the name of your project?")
        self.dest_dir = (Path("..") / Path(dest_dir)).resolve()
        self._ensure_destination_exists()
        self.app_name = self._make_identifier_from_path(self.dest_dir)
        echo(f"Creating Django app named {self.app_name} in directory {self.dest_dir}")

        if config is None:
            # need to use input to get config options.
            self.config = self.ask_questions()
        else:
            self.config = config
        self.config["app_name"] = self.app_name
        self._init_templates()

    @staticmethod
    def _make_identifier_from_path(path):
        """Make path into a valid python identifier."""
        # Get the basename of the path
        name = path.name
        # and fix any invalid characters
        return re.sub(r"\W|^(?=\d)", "_", name)

    def _init_templates(self):
        """Make a Jinja environment with our information."""
        self.templates_dir = Path(__file__).parent / "templates"
        self.templates = Environment(loader=FileSystemLoader(self.templates_dir))
        self.templates.globals.update(self.config)

    def _ensure_path_exists(self, path):
        """Ensure that the given directory exists.

        If the path is relative, it is made inside of self.dest_dir.
        """
        if path.is_absolute():
            path.mkdir(parents=True, exist_ok=True)
        else:
            (self.dest_dir / path).mkdir(parents=True, exist_ok=True)

    def _ensure_destination_exists(self):
        """Ensure that the directory self.dest_dir exists."""
        self._ensure_path_exists(self.dest_dir)

    @staticmethod
    def re_sub_file(filename, pattern, replace):
        """Run a regexp-replace on the contents of an entire file.

        Inspired by Thor's gsub_file.
        """
        with open(filename, "r") as f:
            content = f.read()
        with open(filename, "w") as f:
            f.write(re.sub(pattern, replace, content, count=0, flags=re.MULTILINE))

    @staticmethod
    def ask(question):
        """Ask a question and return the response."""
        # ensure the question ends with a space
        if not question.endswith(" "):
            question += " "
        return input(question)

    def yes(self, question):
        """Ask a question and return True if the answer starts with Y."""
        answer = self.ask(question)
        return answer.lower().startswith("y")

    def ask_questions(self):
        """Ask configuration questions and return dict of answers."""
        responses = {}

        responses["uswds"] = self.yes(
            "Would you like to install USWDS (requires node to already be installed)?"
        )
        responses["circleci"] = self.yes("Would you like to set up CircleCI for CI/CD?")
        responses["github_actions"] = self.yes(
            "Would you like to set up Github Actions for CI/CD?"
        )

        return responses

    def write_file(self, relative_path, content):
        """Write a file into the destination directory."""
        file_path = self.dest_dir / relative_path
        with open(file_path, "w") as f:
            f.write(content)

    def copy_file(self, relative_source, relative_dest):
        """Copy a file from our templates directory into the destination."""
        dest_path = self.dest_dir / relative_dest
        source_path = Path(__file__).parent / "templates" / relative_source
        dest_path.write_bytes(source_path.read_bytes())

    def write_templated_file(self, template_name, destination_path):
        """Render a template and write it into the destination."""
        template = self.templates.get_template(template_name)
        self.write_file(destination_path, template.render())

    def _copy_directory_with_templates(self, relative_source_path, relative_dest_path):
        """Copy a directory of template files into the destination.

        Files whose names end with .jinja will be template substituted as they
        are written. Any other files will be copied over directly.
        """
        source_dir = self.templates_dir / relative_source_path
        destination = self.dest_dir / relative_dest_path
        self._ensure_path_exists(destination)
        for f in source_dir.rglob("*"):
            relative_f = f.relative_to(source_dir)
            if f.is_dir():
                # create the directory in the destination
                self._ensure_path_exists(relative_dest_path / relative_f)
                continue
            if f.suffix == ".jinja":
                # template this file
                self.write_templated_file(
                    str(relative_source_path / relative_f),
                    relative_dest_path / relative_f.with_suffix(""),
                )
            else:
                # just copy it over
                self.copy_file(f, relative_dest_path / relative_f)

    def download_file(self, url, relative_path):
        """Download a remote file to the destination directory."""
        local_filename = self.dest_dir / relative_path
        with get(url, stream=True) as r:
            with open(local_filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    def exec_in_destination(self, command):
        """Run a command in the destination directory.

        `command` should be in a form that can be passed to `subprocess.check_output`

        Returns stdout of the executed command.
        """
        return subprocess.check_output(command, cwd=self.dest_dir, encoding="utf-8")

    # Steps that are done when we run

    def create_readme(self):
        """Create a README file."""
        template = self.templates.get_template("README.md.jinja")
        self.write_file("README.md", template.render())

    def get_policy_files(self):
        """Get license and contributing files from 18F open source policy."""
        for filename in ["CONTRIBUTING.md", "LICENSE.md"]:
            remote_url = f"https://raw.githubusercontent.com/18F/open-source-policy/master/{filename}"  # noqa
            self.download_file(
                remote_url, filename
            )  # filename is relative to the dest_dir

    def initialize_git(self):
        """Initialize a git repository in the target if it doesn't exist."""
        if not (self.dest_dir / ".git").exists():
            self.exec_in_destination(["git", "init", "."])
            # Use a different initial branch name than "master"
            self.exec_in_destination(["git", "branch", "-m", "main"])

    def get_gitignore(self):
        """Get the Python gitignore file from Github."""
        self.download_file(
            "https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore",
            ".gitignore",
        )
        # need to ignore node_modules too, and the generated files
        with open(self.dest_dir / ".gitignore", "a") as f:
            f.write("\nnode_modules\n")
            # and the generated files from USWDS
            f.write(f"\n{self.app_name}/{self.app_name}/static")

    def setup_precommit_hook(self):
        """Set up a git precommit hook."""
        self.write_templated_file("githooks/pre-commit.jinja", ".git/hooks/pre-commit")
        # configure flake8 to be compatible with black
        self.write_templated_file("flake8", ".flake8")

    def create_django_app(self):
        """Create the Django app."""
        # Add a Pipfile to the destination
        self.write_templated_file("Pipfile", "Pipfile")
        # tentatively lock the versions
        self.write_templated_file("Pipfile.lock", "Pipfile.lock")
        # TODO: encourage users to do `pipenv lock` to get new dependency # versions
        # self.exec_in_destination(["pipenv", "lock"])

        # run django-admin startproject if necessary
        if (self.dest_dir / self.app_name).exists():
            # basic check to see if the app has been created
            if (self.dest_dir / self.app_name / "manage.py").exists():
                pass
            else:
                # if the directory already exists, give it as an argument to use
                # the existing directory
                self.exec_in_destination(
                    ["django-admin", "startproject", self.app_name, self.app_name]
                )
        else:
            self.exec_in_destination(["django-admin", "startproject", self.app_name])

        # set up basic URL routing
        self.write_templated_file(
            "django/urls.py", Path(self.app_name) / self.app_name / "urls.py"
        )
        # set up templates
        template_dir = Path(self.app_name) / self.app_name / "templates"
        (self.dest_dir / template_dir).mkdir(parents=True, exist_ok=True)
        # copy because these are already jinja files
        self.copy_file("django/templates/base.html", template_dir / "base.html")
        self.copy_file(
            "django/templates/sample_index.html", template_dir / "sample_index.html"
        )

        # set up basic integration tests
        test_dir = Path(self.app_name) / self.app_name / "tests"
        (self.dest_dir / test_dir).mkdir(parents=True, exist_ok=True)
        (self.dest_dir / test_dir / "__init__.py").touch()
        self.write_templated_file(
            "django/tests/test_integration.py.jinja", test_dir / "test_integration.py"
        )

        # and a logs directory
        logs_dir = self.dest_dir / self.app_name / self.app_name / "logs"
        self._ensure_path_exists(logs_dir)
        (logs_dir / ".gitkeep").touch()

        # and a static directory
        static_dir = self.dest_dir / self.app_name / self.app_name / "static"
        self._ensure_path_exists(static_dir)
        (static_dir / ".gitkeep").touch()

    def setup_docker(self):
        """Make a Dockerfile and docker-compose.yml in the destination."""
        self.copy_file("Dockerfile", "Dockerfile")
        self.write_templated_file("docker-compose.yml.jinja", "docker-compose.yml")
        self.write_templated_file(
            "docker_entrypoint.py.jinja", Path(self.app_name) / "docker_entrypoint.py"
        )

    def setup_owasp(self):
        """Configuration for OWASP Zap scanning using docker-compose."""
        self.copy_file("zap.conf", "zap.conf")

    def _make_settings_directory(self):
        """Make a settings package instead of a single settings file."""
        app_dir = self.dest_dir / self.app_name / self.app_name
        settings_dir = app_dir / "settings"

        # should be idempotent
        settings_dir.mkdir(exist_ok=True)
        (settings_dir / "__init__.py").touch()
        try:
            (app_dir / "settings.py").replace(settings_dir / "base.py")
        except FileNotFoundError:
            pass

        # base.py shouldn't define a SECRET_KEY
        self.re_sub_file(settings_dir / "base.py", r"^\s*SECRET_KEY = .*$", "")

        # patch the default settings to have a templates directory
        base_file_path = settings_dir / "base.py"
        with open(base_file_path, "r") as f:
            contents = f.read()
        contents = contents.replace('"DIRS": []', '"DIRS": [BASE_DIR / "templates"]')
        with open(base_file_path, "w") as f:
            f.write(contents)

        # need this utility for other settings files
        self.copy_file(
            Path("settings") / "env.py",
            Path(self.app_name) / self.app_name / "settings" / "env.py",
        )

    def make_prod_settings(self):
        """Make a settings file for production."""
        self._make_settings_directory()
        self.write_templated_file(
            "settings/prod.py.jinja",
            Path(self.app_name) / self.app_name / "settings" / "prod.py",
        )

    def make_dev_settings(self):
        """Make a settings file for production."""
        self._make_settings_directory()
        self.write_templated_file(
            "settings/dev.py.jinja",
            Path(self.app_name) / self.app_name / "settings" / "dev.py",
        )

    def set_up_npm(self):
        """install node modules in the destination."""
        self.write_templated_file(
            "package.json.jinja",
            "package.json",
        )
        # tentatively lock dependency versions
        self.write_templated_file("package-lock.json", "package-lock.json")
        # TODO: encourage users to `npm update` for their own versions
        self.exec_in_destination(["npm", "install"])

    def set_up_uswds_templates(self):
        """install USWDS using npm and gulp."""
        self.exec_in_destination(["npm", "install"])
        # uswds is installed, what next?
        self.write_templated_file("gulpfile.js.jinja", "gulpfile.js")
        self.exec_in_destination(["npx", "gulp", "init"])
        self.exec_in_destination(["npx", "gulp", "compile"])

    def set_up_circleci(self):
        """Set up CirclCI for CI/CD."""
        # CircleCI config file
        self._ensure_path_exists(Path(".circleci"))  # relative path is inside dest_dir
        self.write_templated_file("circleci/config.yml.jinja", ".circleci/config.yml")

    def set_up_github_actions(self):
        """Set up Github Actions for CI/CD."""
        self._copy_directory_with_templates("github", ".github")

    # main method that runs all of our steps

    def run(self):
        self.create_readme()
        self.get_policy_files()
        self.initialize_git()
        self.get_gitignore()
        self.setup_precommit_hook()

        self.create_django_app()
        self.make_prod_settings()
        self.make_dev_settings()

        # opinionatedly run under Docker and docker-compose
        self.setup_docker()
        self.setup_owasp()

        if self.config.get("uswds"):
            self.set_up_npm()
            self.set_up_uswds_templates()

        if self.config.get("circleci"):
            self.set_up_circleci()

        if self.config.get("github_actions"):
            self.set_up_github_actions()
