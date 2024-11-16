import os
import subprocess
import requests
import json


class DjangoTemplateCreator:
    def __init__(self, project_name):
        self.project_name = project_name
        self.api_url = "https://api.google-gemini.com/v1/instructions"  # Placeholder URL
        self.api_key = "YOUR_API_KEY"  # Replace with your actual API key

    def prompt_google_gemini(self, requirements):
        """ Send project requirements to Google Gemini and get back setup instructions. """
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"requirements": requirements}

        # Send request
        response = requests.post(self.api_url, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(f"API call failed with status {response.status_code}: {response.text}")

        instructions = response.json().get("instructions")
        return instructions

    def create_django_project(self):
        """Create the base Django project."""
        subprocess.run(["django-admin", "startproject", self.project_name])

    def apply_instructions(self, instructions):
        """Modify project files based on the provided instructions."""
        for task in instructions:
            task_type = task.get("task_type")
            file_path = os.path.join(self.project_name, task.get("file"))
            content = task.get("content")

            if task_type == "create":
                with open(file_path, "w") as f:
                    f.write(content)
            elif task_type == "append":
                with open(file_path, "a") as f:
                    f.write(content)
            elif task_type == "replace":
                self.replace_in_file(file_path, task.get("find_text"), task.get("replace_text"))

    def replace_in_file(self, file_path, find_text, replace_text):
        """Replace specific text in a file."""
        with open(file_path, "r") as file:
            file_data = file.read()

        # Replace target string
        file_data = file_data.replace(find_text, replace_text)

        with open(file_path, "w") as file:
            file.write(file_data)

    def run(self, requirements):
        """Main function to create and modify the Django project."""
        # Step 1: Get instructions from Google Gemini
        instructions = self.prompt_google_gemini(requirements)

        # Step 2: Create the Django project
        self.create_django_project()

        # Step 3: Apply instructions
        self.apply_instructions(instructions)
