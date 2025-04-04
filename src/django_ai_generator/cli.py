import click
from rich.console import Console
from InquirerPy import prompt
from InquirerPy.base.control import Choice
from rich.prompt import Confirm

from django_ai_generator.generator import ProjectGenerator

console = Console()


def validate_project_name(name: str) -> bool:
    """Validate Django project name"""
    if not name.isidentifier():
        console.print("[red]Project name must be a valid Python identifier[/red]")
        return False
    if name in ["django", "test", "project"]:
        console.print("[red]Project name cannot be a reserved Django name[/red]")
        return False
    return True


@click.command()
def main():
    """Django project generator with AI assistance"""

    # Project name prompt with validation
    while True:
        project_name = prompt([
            {
                "type": "input",
                "name": "name",
                "message": "Enter project name:",
            }
        ])["name"]
        if validate_project_name(project_name):
            break
        console.print("[yellow]Please choose a different project name[/yellow]")

    options = dict()

    # Framework selection
    project_type = prompt([
        {
            "type": "list",
            "name": "project_type",
            "message": "Select project type:",
            "choices": [Choice("pure django with templates", "Django"), Choice("djangorestframework", "Django REST Framework")],
        }
    ])["project_type"]

    # Initialize features list
    options["type"] = project_type

    # Authentication setup
    if Confirm.ask("Include authentication?"):
        options["authentication"] = True
        if project_type == "djangorestframework":
            auth_type = prompt([
                {
                    "type": "list",
                    "name": "auth_type",
                    "message": "Select authentication type:",
                    "choices": [
                        Choice("jwt", "JWT"),
                        Choice("token", "Token"),
                        Choice("session", "Session"),
                        Choice("oauth2", "OAuth2"),
                    ],
                }
            ])["auth_type"]
            options["auth_type"] = auth_type

        auth_description = prompt([
            {
                "type": "input",
                "name": "description",
                "message": "Describe authentication:",
            }
        ])["description"]
        options["auth_prompt"] = auth_description

    # Custom apps
    if Confirm.ask("Add custom apps?"):
        apps = []
        while Confirm.ask("Add another app?"):
            app_name = prompt([
                {
                    "type": "input",
                    "name": "name",
                    "message": "App name:",
                }
            ])["name"]
            app_description = prompt([
                {
                    "type": "input",
                    "name": "description",
                    "message": "Describe this app:",
                }
            ])["description"]
            apps.append({"name": app_name,
                         "description": app_description})
        options["apps"] = apps

    # project_features = []
    #
    # if Confirm.ask("Use environment variables (.env)?", default=True):
    #     project_features.append("env")
    #
    # if Confirm.ask("Configure CORS?", default=True):
    #     project_features.append("cors")
    #
    # if Confirm.ask("Configure CSRF protection?", default=True):
    #     project_features.append("csrf")
    #
    # if project_type == "drf" and Confirm.ask("Add API documentation (Swagger/OpenAPI)?", default=True):
    #     project_features.append("swagger")
    #
    # db_type = prompt([
    #     {
    #         "type": "list",
    #         "name": "db_type",
    #         "message": "Select database type:",
    #         "choices": [Choice("sqlite", "SQLite"), Choice("postgresql", "PostgreSQL"), Choice("mysql", "MySQL")],
    #     }
    # ])["db_type"]
    # project_features.append({"database": db_type})
    #
    # if Confirm.ask("Include Celery for async tasks?"):
    #     project_features.append("celery")
    #
    # if Confirm.ask("Use Redis for caching?"):
    #     project_features.append("redis")
    #
    # if Confirm.ask("Add Docker support?", default=True):
    #     project_features.append("docker")
    #
    # features.append({"project_features": project_features})

    # Initialize generator
    generator = ProjectGenerator(project_name, options)

    # Generate project
    with console.status("Generating project..."):
        generator.generate()

    console.print("[green]✓[/green] Project generated successfully!")

