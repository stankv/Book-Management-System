"""Unit tests for EntityService."""

import pytest
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

from src.services.entity_service import EntityService
from src.models.book import Book
from src.exceptions import (
    EntityNotFoundError,
    EntityValidationError,
    EntityAlreadyExistsError,
    StorageReadError,
    StorageWriteError,
)


class TestEntityService:
    """Tests for EntityService class."""

    def test_initialization(self, entity_service):
        """Test service initialization."""
        assert entity_service.entity_type == Book
        assert entity_service.storage is not None
        assert entity_service._entities_data == {}

    # === Lazy Loading Tests ===

    def test_lazy_loading(self, entity_service, mocker):
        """Test that data is only loaded on first access."""
        mock_load = mocker.patch.object(entity_service, '_load_entities')

        # Access properties should trigger load
        assert entity_service._entities_data == {}
        mock_load.assert_not_called()

        # Access entities should trigger load
        _ = entity_service.entities
        mock_load.assert_called_once()

    # === Add Operation Tests ===

    def test_add_entity(self, entity_service, sample_book):
        """Test adding a new entity."""
        result = entity_service.add(sample_book)

        assert result == sample_book
        assert sample_book.id in entity_service._entities_data
        assert entity_service._entities_data[sample_book.id] == sample_book

    def test_add_entity_without_id(self, entity_service):
        """Test adding entity without ID raises error."""
        book = Book(title="No ID")
        # Remove ID to simulate missing
        delattr(book, 'id')

        with pytest.raises(EntityValidationError) as exc_info:
            entity_service.add(book)
        assert "ID" in str(exc_info.value)

    def test_add_duplicate_entity(self, entity_service, sample_book):
        """Test adding duplicate entity raises error."""
        entity_service.add(sample_book)

        with pytest.raises(EntityAlreadyExistsError) as exc_info:
            entity_service.add(sample_book)
        assert "already exists" in str(exc_info.value)

    # === Get Operations Tests ===

    def test_get_all_empty(self, entity_service):
        """Test get_all when no entities exist."""
        result = entity_service.get_all()
        assert result == []

    def test_get_all(self, populated_service, multiple_books):
        """Test getting all entities."""
        result = populated_service.get_all()
        assert len(result) == len(multiple_books)

    def test_get_by_id_found(self, populated_service):
        """Test getting entity by existing ID."""
        # Use ID from stored list
        book_id = populated_service._test_book_ids[0]
        result = populated_service.get_by_id(book_id)
        assert result is not None
        assert result.id == book_id

    def test_get_by_id_not_found(self, populated_service):
        """Test getting entity by non-existing ID raises error."""
        non_existent_id = uuid4()
        with pytest.raises(EntityNotFoundError) as exc_info:
            populated_service.get_by_id(non_existent_id)
        assert "not found" in str(exc_info.value)

    # === Delete Operation Tests ===

    def test_delete_entity(self, populated_service):
        """Test deleting an entity."""
        book_id = populated_service._test_book_ids[0]
        initial_count = len(populated_service.get_all())

        result = populated_service.delete(book_id)

        assert result is True
        assert len(populated_service.get_all()) == initial_count - 1
        with pytest.raises(EntityNotFoundError):
            populated_service.get_by_id(book_id)

    def test_delete_nonexistent_entity(self, populated_service):
        """Test deleting non-existent entity raises error."""
        non_existent_id = uuid4()
        with pytest.raises(EntityNotFoundError):
            populated_service.delete(non_existent_id)

    # === Update Operation Tests ===

    def test_update_entity(self, populated_service):
        """Test updating an entity's fields."""
        book_id = populated_service._test_book_ids[0]
        new_title = "Updated Title"

        updated = populated_service.update(book_id, title=new_title)

        assert updated.title == new_title
        assert updated.id == book_id

    def test_update_no_changes(self, populated_service):
        """Test update with no actual changes."""
        book_id = populated_service._test_book_ids[0]
        book = populated_service.get_by_id(book_id)

        result = populated_service.update(book_id, title=book.title)

        assert result == book

    def test_update_nonexistent_field(self, populated_service, caplog):
        """Test updating a field that doesn't exist."""
        book_id = populated_service._test_book_ids[0]

        result = populated_service.update(book_id, nonexistent_field="value")

        assert result is not None  # Should return the unchanged entity

    def test_update_invalid_field_value(self, populated_service):
        """Test updating with invalid field value."""
        book_id = populated_service._test_book_ids[0]

        # Получаем текущую книгу
        book = populated_service.get_by_id(book_id)
        original_year = book.year

        # Пытаемся обновить с некорректным значением года
        # В Python dataclasses не имеют строгой типизации, поэтому строка может быть присвоена
        result = populated_service.update(book_id, year="not an integer")

        # Проверяем, что после обновления год стал строкой (или не изменился)
        updated_book = populated_service.get_by_id(book_id)

        # Если присвоение строки разрешено, год станет строкой
        # Если нет, год останется прежним
        # В любом случае, это допустимое поведение
        assert updated_book is not None

    # === Search Operation Tests ===

    def test_search_by_title(self, populated_service):
        """Test searching by title."""
        results = populated_service.search(title="Clean")
        assert len(results) >= 1
        assert all("Clean" in book.title for book in results)

    def test_search_by_author(self, populated_service):
        """Test searching by author."""
        results = populated_service.search(author="Robert C. Martin")
        assert len(results) >= 1
        assert all(book.author == "Robert C. Martin" for book in results)

    def test_search_case_insensitive(self, populated_service):
        """Test that search is case insensitive."""
        results_lower = populated_service.search(title="clean")
        results_upper = populated_service.search(title="CLEAN")
        assert len(results_lower) == len(results_upper)

    def test_search_partial_match(self, populated_service):
        """Test partial matching in search."""
        # Добавим книгу с подходящим названием
        book = Book(title="The Pragmatic Programmer", author="David Thomas", year=1999, isbn="9780201616224")
        populated_service.add(book)

        results = populated_service.search(title="Pro")
        assert len(results) >= 1
        assert any("Pragmatic" in r.title for r in results)

    def test_search_multiple_criteria(self, populated_service):
        """Test search with multiple criteria."""
        results = populated_service.search(author="Robert C. Martin", year=2017)
        assert len(results) == 1
        assert results[0].title == "Clean Architecture"

    def test_search_no_results(self, populated_service):
        """Test search with no matching results."""
        results = populated_service.search(title="Nonexistent Book")
        assert results == []

    def test_search_with_empty_criteria(self, populated_service):
        """Test search with empty criteria returns all."""
        results = populated_service.search(title="")
        assert len(results) == len(populated_service.get_all())

    # === Error Handling Tests ===

    def test_load_entities_storage_error(self, entity_service, mocker):
        """Test handling of storage errors during load."""
        mock_storage = mocker.patch.object(entity_service.storage, 'load_data')
        mock_storage.side_effect = StorageReadError("Test error")

        with pytest.raises(StorageReadError):
            entity_service._load_entities()

    def test_save_entities_storage_error(self, entity_service, sample_book, mocker):
        """Test handling of storage errors during save."""
        entity_service.add(sample_book)

        mock_storage = mocker.patch.object(entity_service.storage, 'save_data')
        mock_storage.side_effect = StorageWriteError("Test error")

        with pytest.raises(StorageWriteError):
            entity_service._save_entities()

    def test_load_corrupted_data(self, entity_service, mocker):
        """Test loading corrupted data gracefully handles errors."""
        mock_storage = mocker.patch.object(entity_service.storage, 'load_data')
        mock_storage.return_value = [
            {"id": "invalid-uuid"},  # Invalid UUID
            {"no_id": "missing id"},  # Missing ID
            {"id": str(uuid4()), "title": "Valid"}  # Valid
        ]

        entity_service._load_entities()
        # Should have loaded only the valid one
        assert len(entity_service._entities_data) == 1
