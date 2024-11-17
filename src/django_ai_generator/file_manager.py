import ast
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional


class FileManager:
    def __init__(self, project_name):
        self.project_name = project_name
        self.settings_path = None

    def create_file(self, path: str, content: str = ""):
        """Create a file and write content to it."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)

    def _load_settings(self):
        self.settings_path = Path(os.path.join(self.project_name, "settings.py"))
        if not self.settings_path.exists():
            raise FileNotFoundError(f"Settings file not found at {self.settings_path}")

    def _read_settings(self) -> str:
        return self.settings_path.read_text()

    def _write_settings(self, content: str):
        self.settings_path.write_text(content)

    def _parse_value(self, value: Any) -> str:
        if isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (list, tuple, set)):
            return str(value)
        elif isinstance(value, dict):
            return str(value)
        return str(value)

    def _find_variable(self, content: str, variable_name: str) -> Optional[tuple[int, int]]:
        pattern = rf"{variable_name}\s*=\s*"
        match = re.search(pattern, content)
        if not match:
            return None

        start_pos = match.start()

        remaining = content[match.end():].split('\n')[0]
        try:
            # single-line value
            ast.parse(remaining)
            end_pos = match.end() + len(remaining)
            return start_pos, end_pos
        except SyntaxError:
            # multiline value
            bracket_count = 0
            end_pos = match.end()

            for char in content[match.end():]:
                end_pos += 1
                if char in '[{(':
                    bracket_count += 1
                elif char in ']})':
                    bracket_count -= 1
                elif char == '\n' and bracket_count == 0:
                    break

            return start_pos, end_pos

    def update_setting(self, variable_name: str, value: Any, operation_type: Optional[str] = None):
        self._load_settings()
        content = self._read_settings()
        var_pos = self._find_variable(content, variable_name)

        if var_pos is None and operation_type in ('add', 'remove'):
            raise ValueError(f"Cannot {operation_type} from non-existent variable {variable_name}")

        if operation_type is None or operation_type == "set":
            new_value = self._parse_value(value)
            if var_pos is None:
                if content and not content.endswith('\n'):
                    content += '\n'
                content += f"{variable_name} = {new_value}\n"
            else:
                start, end = var_pos
                content = content[:start] + f"{variable_name} = {new_value}" + content[end:]
        else:
            start, end = var_pos
            existing_value = content[start:end].split('=')[1].strip()
            try:
                current_value = ast.literal_eval(existing_value)
            except (SyntaxError, ValueError):
                raise ValueError(f"Could not parse existing value for {variable_name}")

            if not isinstance(current_value, (list, tuple, set)):
                raise TypeError(f"{variable_name} must be a list, tuple, or set for add/remove operations")

            if isinstance(current_value, tuple):
                current_value = list(current_value)
            elif isinstance(current_value, set):
                current_value = list(current_value)

            if operation_type == 'add' and value not in current_value:
                current_value.append(value)
            elif operation_type == 'remove' and value in current_value:
                current_value.remove(value)

            if isinstance(current_value, list):
                if isinstance(existing_value, tuple):
                    current_value = tuple(current_value)
                elif isinstance(existing_value, set):
                    current_value = set(current_value)

            content = (
                    content[:start] +
                    f"{variable_name} = {self._parse_value(current_value)}" +
                    content[end:]
            )

        self._write_settings(content)

