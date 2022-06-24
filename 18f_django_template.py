
"""Create an 18F-flavored Django project."""

import re

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from requests import get


class ProjectCreator:

    def __init__(self, dest_dir=None):
        if dest_dir is None:
            dest_dir = self.ask("What is the name of your project?")
        self.dest_dir = (Path("..") / Path(dest_dir)).resolve()
        self._ensure_destination_exists()
        self.app_name = self._make_identifier(dest_dir)

        answers = self.ask_questions()
        self._init_environment(answers)

    @staticmethod
    def _make_identifier(name):
        """Make name into a valid python identifier."""
        return re.sub('\W|^(?=\d)','_', name)

    def _init_environment(self, answers):
        """Make a Jinja environment with our information."""
        self.environment = Environment(
               loader=FileSystemLoader(Path(__file__).parent / "templates"),
        )
        self.environment.globals.update({"app_name": self.app_name})

    def _ensure_destination_exists(self):
        """Ensure that the directory self.dest_dir exists."""
        self.dest_dir.mkdir(parents=True, exist_ok=True)

    def download_file(self, url, relative_path):
        """Download a remote file to the destination directory."""
        local_filename = self.dest_dir / relative_path
        with get(url, stream=True) as r:
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)

    def ask(self, question):
        """Ask a question and return the response."""
        return input(question)

    def ask_questions(self):
        return {}

    def write_file(self, relative_path, content):
        """Write a file into the destination directory."""
        file_path =  self.dest_dir / relative_path
        with open(file_path, "w") as f:
            f.write(content)

    def create_readme(self):
        """Create a README file."""
        template = self.environment.get_template("README.md.jinja")
        self.write_file("README.md", template.render())

    def get_policy_files(self):
        """Get license and contributing files from 18F open source policy."""
        for filename in ["CONTIBUTING.md", "LICENSE.md"]:
            remote_url = f"https://raw.githubusercontent.com/18F/open-source-policy/master/{filename}"
            self.download_file(remote_url, filename)  # filename is relative to the dest_dir

    def run(self):
        self.create_readme()
        self.get_policy_files()

def main():
    """Run the command line script."""
    ProjectCreator().run()

if __name__ == "__main__":
    main()
