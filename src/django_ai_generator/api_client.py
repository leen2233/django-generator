import json
from typing import List, Dict
import os

import requests
from rich.console import Console
from rich.pretty import pprint
console = Console()


class GeminiClient:
    def __init__(self, project_name):
        self.project_name = project_name
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = "gemini-exp-1114"
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.chat = []
        self._load_system_instructions()

    def get_authentication_instructions(self, type: str, description: str = None):
        prompt = self._build_authentication_prompt(type, description)
        response = self._send_request(prompt)
        return response

    def get_project_instructions(self, name: str, features: List[Dict]) -> dict:
        prompt = self._build_prompt(name, features)
        system_instructions = self._system_instruction
        try:
            content = None
            while True:
                headers = {"Content-Type": "application/json"}
                data = {"system_instruction": {"parts": {"text": system_instructions}},
                        "contents": [{"parts": [{"text": prompt}]}]}
                url = (f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest"
                       f":generateContent?key={self.api_key}")
                response = requests.post(url, json=data, headers=headers)
                if response.status_code != 200:
                    console.print(f"[red]Error generating instructions from Gemini API: {response.status_code} - {response.text}[/red]")
                    raise Exception(f"Failed to generate instructions from Gemini API")
                data = response.json()
                if not data.get("candidates", [{}])[0].get("finishReason") == "RECITATION":
                    try:
                        content = self._get_response_text(data)
                        break
                    except:
                        continue
                print("[retrying...]")
            return content

        except Exception as e:
            console.print(f"[red]Error getting instructions from Gemini API: {str(e)}[/red]")
            raise

    def _build_authentication_prompt(self, type: str, custom_description: str = None) -> str:
        return f"""
        Create and configure an authentication app using {type}. Include all necessary files and configurations such as models, serializers, views, URLs, and settings to fully implement the specified authentication type. Ensure all required endpoints for login, registration, and token management (if applicable) are functional.
        {custom_description}
        """

    def _build_prompt(self, name: str, features: List[Dict]) -> str:
        return f"""
        Create a detailed Django project structure for a project named '{name}' with the following features:
        {features}
        """

    def _load_system_instructions(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(script_dir, "system_instructions.txt")
            with open(file_path, "r") as f:
                self._system_instruction = f.read()
        except FileNotFoundError:
            console.print("[red]System instructions file not found. Please generate them using the 'generate_system_instructions.py' script and upload the resulting JSON file to the project directory.[/red]")
            raise

    def _send_request(self, prompt):
        self.chat.append({"role": "user", "parts": [{"text": prompt}]})
        try:
            content = None
            while True:
                headers = {"Content-Type": "application/json"}
                data = {"system_instruction": {"parts": {"text": self._system_instruction}},
                        "contents": self.chat}
                url = (f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}"
                       f":generateContent?key={self.api_key}")
                response = requests.post(url, json=data, headers=headers)
                if response.status_code != 200:
                    console.print(
                        f"[red]Error generating instructions from Gemini API: {response.status_code} - {response.text}[/red]")
                    raise Exception(f"Failed to generate instructions from Gemini API")
                data = response.json()
                if not data.get("candidates", [{}])[0].get("finishReason") == "RECITATION":
                    try:
                        content = self._get_response_text(data)
                        break
                    except:
                        continue
                print("[retrying...]")
            self.chat.append({"role": "model", "parts": [{"text": json.dumps(content)}]})
            return content

        except Exception as e:
            console.print(f"[red]Error getting instructions from Gemini API: {str(e)}[/red]")
            raise

    def _get_response_text(self, response: dict) -> dict:
        try:
            response = response.get("candidates", [{}])[0]
            response = response.get("content", {}).get("parts", [{}])[0]
            content = response.get("text").replace("```json", "").replace("```", "")
            content = json.loads(content)
        except Exception as e:
            console.print("[red]Error parsing response from Gemini API: Invalid response format[/red]")
            raise
        pprint(content)
        return content


