import json
from pathlib import Path
from uuid import UUID

from src.storage.base_storage import BaseStorage


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class JsonStorage(BaseStorage):
    def __init__(self, file_path: Path, indent: int = 2) -> None:
        self.file_path = file_path
        self.indent = indent

    def ensure_path_exists(self):
        if not self.file_path.parent.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load_data(self):
        if not self.file_path.exists():
            return None
        with self.file_path.open("r") as file:
            return json.load(file)

    def save_data(self, data):
        self.ensure_path_exists()
        with self.file_path.open("w") as file:
            json.dump(data, file, ensure_ascii=False, indent=self.indent, cls=Encoder)
