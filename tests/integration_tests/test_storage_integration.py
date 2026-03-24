"""Integration tests for storage layer with actual file system."""

import json
import pytest
from uuid import uuid4

from src.storage.json_storage import JsonStorage
from src.exceptions import StorageReadError


class TestJsonStorageIntegration:
    """Integration tests for JsonStorage with real file operations."""

    def test_create_storage_file_on_save(self, test_data_dir):
        """Test that storage file is created when saving data."""
        file_path = test_data_dir / "new_books.json"
        storage = JsonStorage(file_path)

        assert not file_path.exists()

        data = [{"id": str(uuid4()), "title": "Test Book"}]
        storage.save_data(data)

        assert file_path.exists()
        assert file_path.is_file()

    def test_load_data_from_existing_file(self, test_data_dir):
        """Test loading data from an existing JSON file."""
        file_path = test_data_dir / "existing_books.json"

        # Create a test file manually
        test_data = [
            {"id": str(uuid4()), "title": "Book 1", "author": "Author 1"},
            {"id": str(uuid4()), "title": "Book 2", "author": "Author 2"},
        ]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        # Load using storage
        storage = JsonStorage(file_path)
        loaded_data = storage.load_data()

        assert len(loaded_data) == len(test_data)
        assert loaded_data[0]["title"] == test_data[0]["title"]
        assert loaded_data[1]["author"] == test_data[1]["author"]

    def test_save_and_load_cycle_with_uuids(self, test_data_dir):
        """Test complete save-load cycle with UUID objects."""
        file_path = test_data_dir / "cycle_test.json"
        storage = JsonStorage(file_path)

        # Create data with UUIDs
        book_id1 = uuid4()
        book_id2 = uuid4()
        original_data = [
            {"id": book_id1, "title": "UUID Book 1", "year": 2020},
            {"id": book_id2, "title": "UUID Book 2", "year": 2021},
        ]

        # Save
        storage.save_data(original_data)

        # Load
        loaded_data = storage.load_data()

        # Verify UUIDs were properly serialized/deserialized
        assert len(loaded_data) == 2
        assert loaded_data[0]["id"] == str(book_id1)
        assert loaded_data[1]["id"] == str(book_id2)
        assert loaded_data[0]["title"] == "UUID Book 1"

    def test_overwrite_existing_file(self, test_data_dir):
        """Test that saving overwrites existing file content."""
        file_path = test_data_dir / "overwrite_test.json"
        storage = JsonStorage(file_path)

        # Save initial data
        initial_data = [{"id": str(uuid4()), "value": "initial"}]
        storage.save_data(initial_data)

        # Save new data
        new_data = [{"id": str(uuid4()), "value": "new"}]
        storage.save_data(new_data)

        # Load and verify only new data exists
        loaded = storage.load_data()
        assert len(loaded) == 1
        assert loaded[0]["value"] == "new"

    def test_append_to_file_not_supported(self, test_data_dir):
        """Test that storage doesn't support append (always overwrites)."""
        file_path = test_data_dir / "append_test.json"
        storage = JsonStorage(file_path)

        # First save
        data1 = [{"id": str(uuid4()), "data": "first"}]
        storage.save_data(data1)

        # Second save with different data
        data2 = [{"id": str(uuid4()), "data": "second"}]
        storage.save_data(data2)

        # Load should have only second data
        loaded = storage.load_data()
        assert len(loaded) == 1
        assert loaded[0]["data"] == "second"

    def test_load_nonexistent_file_returns_none(self, test_data_dir):
        """Test that loading a non-existent file returns None."""
        file_path = test_data_dir / "nonexistent.json"
        storage = JsonStorage(file_path)

        assert not file_path.exists()
        result = storage.load_data()
        assert result is None

    def test_create_nested_directories(self, test_data_dir):
        """Test that storage creates nested directories if needed."""
        nested_path = test_data_dir / "level1" / "level2" / "nested_books.json"
        storage = JsonStorage(nested_path)

        assert not nested_path.parent.exists()

        data = [{"id": str(uuid4()), "test": "data"}]
        storage.save_data(data)

        assert nested_path.parent.exists()
        assert nested_path.exists()

    def test_save_large_dataset(self, test_data_dir):
        """Test saving and loading a large dataset."""
        file_path = test_data_dir / "large_dataset.json"
        storage = JsonStorage(file_path)

        # Create 1000 books
        large_data = []
        for i in range(1000):
            large_data.append(
                {
                    "id": str(uuid4()),
                    "title": f"Book {i}",
                    "author": f"Author {i % 10}",
                    "year": 2000 + (i % 30),
                    "isbn": f"978000000{i:04d}",
                }
            )

        # Save
        storage.save_data(large_data)

        # Load and verify
        loaded = storage.load_data()
        assert len(loaded) == 1000
        assert loaded[500]["title"] == "Book 500"

    def test_unicode_characters_handling(self, test_data_dir):
        """Test handling of Unicode characters in JSON."""
        file_path = test_data_dir / "unicode_test.json"
        storage = JsonStorage(file_path)

        data = [
            {
                "id": str(uuid4()),
                "title": "Book in Russian",
                "author": "Author Name in Chinese",
                "description": "French text with accents",
            }
        ]

        storage.save_data(data)
        loaded = storage.load_data()

        assert loaded[0]["title"] == "Book in Russian"
        assert loaded[0]["author"] == "Author Name in Chinese"
        assert "French" in loaded[0]["description"]

    def test_json_decode_error_handling(self, test_data_dir):
        """Test handling of corrupted JSON files."""
        file_path = test_data_dir / "corrupted.json"

        # Write invalid JSON
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('{"invalid": json, file: [1,2,3]')  # Missing closing brace

        storage = JsonStorage(file_path)

        with pytest.raises(StorageReadError) as exc_info:
            storage.load_data()
        assert "JSON decode error" in str(exc_info.value)

    def test_empty_file_handling(self, test_data_dir):
        """Test handling of empty JSON file."""
        file_path = test_data_dir / "empty.json"

        # Create empty file
        file_path.touch()

        storage = JsonStorage(file_path)

        with pytest.raises(StorageReadError) as exc_info:
            storage.load_data()
        assert "JSON decode error" in str(exc_info.value) or "Expecting value" in str(
            exc_info.value
        )

    def test_custom_indent_parameter(self, test_data_dir):
        """Test that indent parameter affects file formatting."""
        file_path = test_data_dir / "indent_test.json"

        # Test with different indent values
        for indent in [None, 0, 2, 4]:
            storage = JsonStorage(file_path, indent=indent)
            data = [{"id": str(uuid4()), "test": "data"}]
            storage.save_data(data)

            # Read raw file to check formatting
            with open(file_path, "r") as f:
                content = f.read()

            if indent is None:
                # Compact JSON - no newlines between items
                assert "\n" not in content or len(content.split("\n")) <= 2
            else:
                # Pretty printed - should have newlines
                assert "\n" in content

    def test_concurrent_file_access(self, test_data_dir):
        """Test that storage handles concurrent access (simulated)."""
        file_path = test_data_dir / "concurrent.json"
        storage1 = JsonStorage(file_path)
        storage2 = JsonStorage(file_path)

        # Storage1 saves data
        data1 = [{"id": str(uuid4()), "owner": "storage1"}]
        storage1.save_data(data1)

        # Storage2 saves different data (overwrites)
        data2 = [{"id": str(uuid4()), "owner": "storage2"}]
        storage2.save_data(data2)

        # Storage1 reads - should get storage2's data (last write wins)
        loaded = storage1.load_data()
        assert loaded[0]["owner"] == "storage2"
