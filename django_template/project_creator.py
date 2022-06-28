
import re
import subprocess

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from requests import get


class ProjectCreator:

    def __init__(self, dest_dir=None):
        if dest_dir is None:
            # destination wasn't given
            dest_dir = self.ask("What is the name of your project?")
            self.dest_dir = (Path("..") / Path(dest_dir)).resolve()
        else:
            # destination was given, make sure it's a path
            self.dest_dir = Path(dest_dir)
        self._ensure_destination_exists()
        self.app_name = self._make_identifier_from_path(self.dest_dir)

        answers = self.ask_questions()
        self._init_templates(answers)

    @staticmethod
    def _make_identifier_from_path(path):
        """Make path into a valid python identifier."""
        # Get the basename of the path
        name = path.name
        # and fix any invalid characters
        return re.sub(r'\W|^(?=\d)','_', name)

    def _init_templates(self, answers):
        """Make a Jinja environment with our information."""
        self.templates = Environment(
               loader=FileSystemLoader(Path(__file__).parent / "templates"),
        )
        self.templates.globals.update({"app_name": self.app_name})
        self.templates.globals.update(answers)

    def _ensure_destination_exists(self):
        """Ensure that the directory self.dest_dir exists."""
        self.dest_dir.mkdir(parents=True, exist_ok=True)

    def ask(self, question):
        """Ask a question and return the response."""
        return input(question)

    def ask_questions(self):
        """Ask configuration questions and return dict of answers."""
        return {}

    def write_file(self, relative_path, content):
        """Write a file into the destination directory."""
        file_path =  self.dest_dir / relative_path
        with open(file_path, "w") as f:
            f.write(content)

    def download_file(self, url, relative_path):
        """Download a remote file to the destination directory."""
        local_filename = self.dest_dir / relative_path
        with get(url, stream=True) as r:
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)

    def exec_in_destination(self, command):
        """Run a command in the destination directory.

        `command` should be in a form that can be passed to `subprocess.check_call`
        """
        subprocess.check_call(command, cwd=self.dest_dir)

    # Steps that are done when we run

    def create_readme(self):
        """Create a README file."""
        template = self.templates.get_template("README.md.jinja")
        self.write_file("README.md", template.render())

    def get_policy_files(self):
        """Get license and contributing files from 18F open source policy."""
        for filename in ["CONTRIBUTING.md", "LICENSE.md"]:
            remote_url = f"https://raw.githubusercontent.com/18F/open-source-policy/master/{filename}"
            self.download_file(remote_url, filename)  # filename is relative to the dest_dir

    def create_django_app(self):
        """Create the Django app."""
        if (self.dest_dir / self.app_name).exists():
            # basic check to see if the app has been created
            if (self.dest_dir / self.app_name / "manage.py").exists():
                return
            # if the directory already exists, give it as an argument to use
            # the existing directory
            self.exec_in_destination(["django-admin", "startproject", self.app_name, self.app_name])
        else:
            self.exec_in_destination(["django-admin", "startproject", self.app_name])

    def _make_settings_directory(self):
        """Make a settings package instead of a single settings file."""
        app_dir = self.dest_dir / self.app_name / self.app_name
        print(app_dir)
        settings_dir = app_dir / "settings"
        print(settings_dir)
        # should be idempotent
        settings_dir.mkdir(exist_ok=True)
        (settings_dir / "__init__.py").touch()
        try:
            (app_dir / "settings.py").replace(settings_dir / "base.py")
        except FileNotFoundError:
            pass

    def make_prod_settings(self):
        """Make a settings file for production."""
        self._make_settings_directory()
        template = self.templates.get_template("settings/prod.py.jinja")
        dest_path = Path(self.app_name) / self.app_name / "settings" / "prod.py"
        #print(dest_path)
        self.write_file(
            dest_path,
            template.render()
        )


    # main method that runs all of our steps

    def run(self):
        self.create_readme()
        self.get_policy_files()
        self.create_django_app()
        self.make_prod_settings()


