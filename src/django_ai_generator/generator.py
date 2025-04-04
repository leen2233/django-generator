import subprocess
from typing import List, Dict
import os
from rich.console import Console

from .api_client import GeminiClient
from .file_manager import FileManager

console = Console()


class ProjectGenerator:
    def __init__(self, name: str, options: Dict):
        self.name = name
        self.options = options
        self.api_client = GeminiClient(project_name=self.name, options=self.options)
        self.file_manager = FileManager(project_name=self.name)

    def generate(self):
        """Main method to generate the project."""
        try:
            self._create_project()
            authentication = self.options.get("authentication")
            if authentication:
                instructions = self.api_client.get_authentication_instructions(self.options.get("auth_type"),
                                                                               self.options.get("auth_prompt"))
                self.run_instructions(instructions)

            for app in self.options.get("apps"):
                instructions = self.api_client.get_app_instructions(app)
                self.run_instructions(instructions)

        except Exception as e:
            console.print(f"[red]Project generation failed: {e}[/red]")

    def run_instructions(self, instructions):
        for instruction in instructions:
            if instruction.get("type") == "command":
                self._run_command(instruction.get("command"))
            elif instruction.get("type") == "file":
                self._configure_file(instruction)
            elif instruction.get("type") == "update_settings":
                self._update_settings(instruction)
            elif instruction.get("type") == "dependencies":
                self._install_dependencies(instruction.get("dependencies"))

    def _install_django(self):
        """Install Django using pip."""
        console.print("[yellow]Django not found. Installing Django...[/yellow]")
        try:
            subprocess.check_call(["pip", "install", "django"])
            console.print("[green]Django installed successfully![/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to install Django: {e}[/red]")
            raise RuntimeError("Could not install Django. Please check your environment.")

    def _create_project(self):
        """Create a Django project using `django-admin startproject`."""
        try:
            console.print(f"[blue]Creating Django project: {self.name}...[/blue]")
            subprocess.check_call(["django-admin", "startproject", self.name])
            console.print("[green]Project created successfully![/green]")
            os.chdir(self.name)
            console.print(f"[blue]Changed working directory to {self.name}[/blue]")
        except FileNotFoundError as e:
            if "django-admin" in str(e):
                self._install_django()
                self._create_project()  # Retry after installing Django
            else:
                console.print(f"[red]Error: {e}[/red]")
                raise
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to create Django project: {e}[/red]")
            raise

    def _run_command(self, command: str):
        """Run a command in the project's root directory."""
        try:
            if "makemigrations" not in command or "migrate" not in command:
                console.print(f"[yellow]Running command: {command}...[/yellow]")
                subprocess.check_call(command, shell=True)
                console.print("[green]Command executed successfully![/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to run command: {e}[/red]")
            raise

    def _configure_file(self, instruction: Dict):
        """Configure a file in the project's root directory."""
        try:
            file_path = instruction.get("filename")
            content = instruction.get("content")
            console.print(f"[yellow]Configuring file: {file_path}...[/yellow]")
            self.file_manager.create_file(file_path, content)
            console.print("[green]File configured successfully![/green]")
        except Exception as e:
            console.print(f"[red]Failed to configure file: {e}[/red]")
            raise

    def _update_settings(self, instruction: Dict):
        """Update settings in the project's settings.py file."""
        console.print("[yellow]Updating settings...[/yellow]")
        try:
            key = instruction.get("variable_name")
            value = instruction.get("value")
            action = instruction.get("action")
            self.file_manager.update_setting(key, value, action)
            console.print("[green]Settings updated successfully![/green]")
        except Exception as e:
            console.print(f"[red]Failed to update settings: {e}[/red]")
            raise

    def _install_dependencies(self, dependencies: List[str]):
        """Install a dependencies using pip."""
        failed_dependencies = list()
        for dependency in dependencies:
            console.print(f"[yellow]Installing dependency: {dependency}...[/yellow]")
            try:
                subprocess.check_call(["pip", "install", dependency])
                console.print("[green]Dependency installed successfully![/green]")
            except subprocess.CalledProcessError as e:
                failed_dependencies.append({"name": dependency, "error": e})
        if failed_dependencies:
            # Refactor failed dependencies
            console.print(f"[red]Failed dependency: {failed_dependencies}![/red]")
            refactored_deps = self.api_client.refactor_dependencies(failed_dependencies)
            self._install_dependencies(refactored_deps[0].get("dependencies"))
