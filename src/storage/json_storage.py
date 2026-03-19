import json
from pathlib import Path
from uuid import UUID

from src.settings import JSON_INDENT
from src.storage.base_storage import BaseStorage


class Encoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUID serialization.

    Extends the standard JSONEncoder to convert UUID objects to their
    string representation, which is necessary because UUID is not
    natively JSON serializable."""

    def default(self, obj):
        """Override the default serialization method.

        Args:
            obj: The object to serialize.

        Returns:
            The string representation of a UUID object, or falls back to
            the parent class method for other types."""
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class JsonStorage(BaseStorage):
    """JSON file-based storage implementation.

    Provides concrete implementation of BaseStorage using JSON files
    as the persistence mechanism. Handles file operations, directory
    creation, and proper serialization/deserialization of data.

    Attributes:
        file_path: Path object pointing to the JSON file location.
        indent: Number of spaces for JSON pretty-printing (default: 2 in settings.py)."""

    def __init__(self, file_path: Path, indent=JSON_INDENT) -> None:
        """Initialize JSON storage with a file path.

        Args:
            file_path: Path to the JSON file where data will be stored.
            indent: Number of spaces to use for JSON indentation (default: 2 in settings.py).
                   Set to None for compact storage without extra whitespace."""
        self.file_path = file_path
        self.indent = indent

    def ensure_path_exists(self):
        """Ensure the directory for the storage file exists.

        Creates the parent directory if it doesn't exist. This prevents
        FileNotFoundError when trying to write to a non-existent directory."""
        if not self.file_path.parent.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load_data(self):
        """Load data from the JSON file.

        Reads the JSON file and parses its contents. If the file doesn't
        exist, returns None instead of raising an error.

        Returns:
            Parsed JSON data (typically a list of dictionaries) if file exists,
            None otherwise.

        Raises:
            json.JSONDecodeError: If the file contains invalid JSON.
            StorageReadError: For other file access errors."""
        if not self.file_path.exists():
            return None
        with self.file_path.open("r") as file:
            return json.load(file)

    def save_data(self, data):
        """Save data to the JSON file.

        Serializes the provided data to JSON format and writes it to the file.
        Ensures the directory exists before writing. Uses the custom Encoder
        to handle UUID serialization.

        Args:
            data: The data to serialize (typically a list of entity dictionaries).

        Raises:
            json.JSONEncodeError: If the data cannot be serialized to JSON.
            StorageWriteError: For file access errors during writing."""
        self.ensure_path_exists()
        with self.file_path.open("w") as file:
            json.dump(data, file, ensure_ascii=False, indent=self.indent, cls=Encoder)
