"""Unit tests for action classes."""

import pytest
from uuid import UUID, uuid4
from unittest.mock import Mock, patch

from src.actions import (
    ActionResult,
    AddEntityAction,
    DeleteEntityAction,
    ListEntitiesAction,
    SearchEntityAction,
    UpdateEntityAction,
    ExitAction,
)
from src.exceptions import (
    EntityNotFoundError,
    ActionCancelledError,
    InvalidChoiceError,
    BookValidationError,
)


class TestBaseAction:
    """Tests for base action functionality."""

    def test_action_result_dataclass(self):
        """Test ActionResult dataclass default values."""
        result = ActionResult()
        assert result.stop is False
        assert result.error is False

        result = ActionResult(stop=True, error=True)
        assert result.stop is True
        assert result.error is True


class TestExitAction:
    """Tests for ExitAction."""

    def test_exit_action_properties(self):
        """Test exit action name and description."""
        action = ExitAction()
        assert action.get_name() == "exit"
        assert "Exiting" in action.get_description()

    def test_exit_action_execute(self):
        """Test exit action execution."""
        action = ExitAction()
        result = action.execute()
        assert result.stop is True
        assert result.error is False


class TestListEntitiesAction:
    """Tests for ListEntitiesAction."""

    def test_list_action_properties(self, entity_service):
        """Test list action name and description."""
        action = ListEntitiesAction(entity_service)
        assert "List" in action.get_name()
        assert "Book" in action.get_name()
        assert "list" in action.get_description().lower()

    def test_list_empty_storage(self, entity_service, mock_io):
        """Test listing when storage is empty."""
        action = ListEntitiesAction(entity_service)
        result = action.execute()

        assert result.error is False
        assert any("No Books" in output for output in mock_io["outputs"])

    def test_list_with_entities(self, populated_service, mock_io):
        """Test listing with entities in storage."""
        action = ListEntitiesAction(populated_service)
        result = action.execute()

        assert result.error is False
        # Should show each book
        for book in populated_service.get_all():
            assert any(str(book.id) in output for output in mock_io["outputs"])


class TestAddEntityAction:
    """Tests for AddEntityAction."""

    def test_add_action_properties(self, entity_service):
        """Test add action name and description."""
        action = AddEntityAction(entity_service)
        assert "Add" in action.get_name()
        assert "Book" in action.get_name()
        assert "add" in action.get_description().lower()

    def test_add_entity_success(self, entity_service, mock_io):
        """Test successful entity addition."""
        action = AddEntityAction(entity_service)

        # Simulate user input
        mock_io["add_input"]("Clean Code")  # title
        mock_io["add_input"]("Robert Martin")  # author
        mock_io["add_input"]("2008")  # year
        mock_io["add_input"]("9780132350884")  # isbn
        mock_io["add_input"]("y")  # confirm

        result = action.execute()

        assert result.error is False
        assert len(entity_service.get_all()) == 1
        assert any("successfully added" in output.lower()
                   for output in mock_io["outputs"])

    def test_add_entity_cancel_during_input(self, entity_service, mock_io):
        """Test cancelling during field input."""
        action = AddEntityAction(entity_service)

        mock_io["add_input"]("cancel")  # cancel during first field

        result = action.execute()

        assert result.error is False
        assert len(entity_service.get_all()) == 0
        assert any("cancelled" in output.lower()
                   for output in mock_io["outputs"])

    def test_add_entity_cancel_at_confirmation(self, entity_service, mock_io):
        """Test cancelling at confirmation step."""
        action = AddEntityAction(entity_service)

        mock_io["add_input"]("Clean Code")
        mock_io["add_input"]("Robert Martin")
        mock_io["add_input"]("2008")
        mock_io["add_input"]("9780132350884")
        mock_io["add_input"]("n")  # don't confirm

        result = action.execute()

        assert result.error is False
        assert len(entity_service.get_all()) == 0

    def test_add_entity_validation_error(self, entity_service, mock_io):
        """Test validation error during input."""
        action = AddEntityAction(entity_service)

        # First try invalid year, then valid
        mock_io["add_input"]("Clean Code")
        mock_io["add_input"]("Robert Martin")
        mock_io["add_input"]("1300")  # invalid year
        mock_io["add_input"]("2008")  # valid year
        mock_io["add_input"]("9780132350884")
        mock_io["add_input"]("y")

        result = action.execute()

        assert result.error is False
        assert len(entity_service.get_all()) == 1
        # Should have shown error message
        assert any("year" in output.lower() and "between" in output.lower()
                   for output in mock_io["outputs"])


class TestDeleteEntityAction:
    """Tests for DeleteEntityAction."""

    def test_delete_action_properties(self, entity_service):
        """Test delete action name and description."""
        action = DeleteEntityAction(entity_service)
        assert "Delete" in action.get_name()
        assert "Book" in action.get_name()
        assert "delete" in action.get_description().lower()

    def test_delete_entity_success(self, populated_service, mock_io, multiple_books):
        """Test successful entity deletion."""
        action = DeleteEntityAction(populated_service)
        # Получим ID из сохраненного списка
        book_id = populated_service._test_book_ids[0]

        mock_io["add_input"](str(book_id))  # ID
        mock_io["add_input"]("y")  # confirm

        initial_count = len(populated_service.get_all())
        result = action.execute()

        assert result.error is False
        assert len(populated_service.get_all()) == initial_count - 1

    def test_delete_entity_not_found(self, populated_service, mock_io):
        """Test deleting non-existent entity."""
        action = DeleteEntityAction(populated_service)
        non_existent_id = uuid4()

        mock_io["add_input"](str(non_existent_id))

        result = action.execute()

        assert result.error is True
        assert any("not found" in output.lower()
                   for output in mock_io["outputs"])

    def test_delete_entity_cancel_at_confirmation(self, populated_service, mock_io, multiple_books):
        """Test cancelling deletion at confirmation."""
        action = DeleteEntityAction(populated_service)
        book_id = populated_service._test_book_ids[0]

        mock_io["add_input"](str(book_id))
        mock_io["add_input"]("n")  # don't confirm

        initial_count = len(populated_service.get_all())
        result = action.execute()

        assert result.error is False
        assert len(populated_service.get_all()) == initial_count  # No change

    def test_delete_entity_invalid_uuid(self, populated_service, mock_io):
        """Test deleting with invalid UUID format."""
        action = DeleteEntityAction(populated_service)

        mock_io["add_input"]("not-a-valid-uuid")

        result = action.execute()

        assert result.error is True
        assert any("Invalid UUID" in output for output in mock_io["outputs"])


class TestSearchEntityAction:
    """Tests for SearchEntityAction."""

    def test_search_action_properties(self, entity_service):
        """Test search action name and description."""
        action = SearchEntityAction(entity_service)
        assert "Search" in action.get_name()
        assert "Book" in action.get_name()
        assert "search" in action.get_description().lower()

    def test_search_by_id(self, populated_service, mock_io, multiple_books):
        """Test searching by ID."""
        action = SearchEntityAction(populated_service)
        book_id = populated_service._test_book_ids[0]

        mock_io["add_input"]("1")  # Choose ID search
        mock_io["add_input"](str(book_id))

        result = action.execute()

        assert result.error is False
        assert any(str(book_id) in output for output in mock_io["outputs"])

    def test_search_by_title(self, populated_service, mock_io):
        """Test searching by title."""
        action = SearchEntityAction(populated_service)

        mock_io["add_input"]("2")  # Choose title search
        mock_io["add_input"]("Clean")

        result = action.execute()

        assert result.error is False
        assert any("Found" in output for output in mock_io["outputs"])

    def test_search_by_author(self, populated_service, mock_io):
        """Test searching by author."""
        action = SearchEntityAction(populated_service)

        mock_io["add_input"]("3")  # Choose author search
        mock_io["add_input"]("Robert C. Martin")

        result = action.execute()

        assert result.error is False
        assert any("Found" in output for output in mock_io["outputs"])

    def test_search_by_isbn(self, populated_service, mock_io):
        """Test searching by ISBN."""
        action = SearchEntityAction(populated_service)

        mock_io["add_input"]("4")  # Choose ISBN search
        mock_io["add_input"]("9780134494166")

        result = action.execute()

        assert result.error is False
        assert any("Found" in output for output in mock_io["outputs"])

    def test_search_no_results(self, populated_service, mock_io):
        """Test search with no results."""
        action = SearchEntityAction(populated_service)

        mock_io["add_input"]("2")  # Title search
        mock_io["add_input"]("Nonexistent Book")

        result = action.execute()

        assert result.error is False
        assert any("not found" in output.lower() for output in mock_io["outputs"])

    def test_search_invalid_choice(self, populated_service, mock_io):
        """Test invalid menu choice."""
        action = SearchEntityAction(populated_service)

        mock_io["add_input"]("9")  # Invalid choice

        result = action.execute()

        assert result.error is False
        assert any("Wrong choice" in output for output in mock_io["outputs"])

    def test_search_empty_input(self, populated_service, mock_io):
        """Test search with empty input."""
        action = SearchEntityAction(populated_service)

        mock_io["add_input"]("2")  # Title search
        mock_io["add_input"]("")  # Empty input

        result = action.execute()

        assert result.error is False
        assert any("canceled" in output.lower() for output in mock_io["outputs"])


class TestUpdateEntityAction:
    """Tests for UpdateEntityAction."""

    def test_update_action_properties(self, entity_service):
        """Test update action name and description."""
        action = UpdateEntityAction(entity_service)
        assert "Update" in action.get_name()
        assert "Book" in action.get_name()
        assert "update" in action.get_description().lower()

    def test_update_entity_success(self, populated_service, mock_io, multiple_books):
        """Test successful entity update."""
        action = UpdateEntityAction(populated_service)
        book_id = populated_service._test_book_ids[0]
        book = populated_service.get_by_id(book_id)
        new_title = "Updated Title"

        # Search for the book by ID (более надежно)
        mock_io["add_input"]("1")  # ID search
        mock_io["add_input"](str(book_id))

        # Update fields
        mock_io["add_input"](new_title)  # New title
        mock_io["add_input"]("")  # Skip author (keep current)
        mock_io["add_input"]("")  # Skip year
        mock_io["add_input"]("")  # Skip ISBN
        mock_io["add_input"]("y")  # Confirm changes

        result = action.execute()

        assert result.error is False
        updated_book = populated_service.get_by_id(book_id)
        assert updated_book.title == new_title

    def test_update_multiple_fields(self, populated_service, mock_io, multiple_books):
        """Test updating multiple fields."""
        action = UpdateEntityAction(populated_service)
        # Используем ID из сохраненного списка
        book_id = populated_service._test_book_ids[0]

        # Search for the book by ID
        mock_io["add_input"]("1")  # ID search
        mock_io["add_input"](str(book_id))

        # Update fields
        mock_io["add_input"]("New Title")
        mock_io["add_input"]("")  # Skip author
        mock_io["add_input"]("2020")
        mock_io["add_input"]("")  # Skip ISBN
        mock_io["add_input"]("y")  # Confirm

        result = action.execute()

        assert result.error is False
        updated_book = populated_service.get_by_id(book_id)
        assert updated_book.title == "New Title"
        assert updated_book.year == 2020

    def test_update_cancel_during_search(self, populated_service, mock_io):
        """Test cancelling during search phase."""
        action = UpdateEntityAction(populated_service)

        mock_io["add_input"]("2")  # Title search
        mock_io["add_input"]("cancel")  # Cancel

        result = action.execute()

        assert result.error is False
        # Проверяем, что было сообщение об отмене
        assert any("cancelled" in output.lower() or "cancel" in output.lower()
                   for output in mock_io["outputs"])

    def test_update_cancel_during_field_update(self, populated_service, mock_io):
        """Test cancelling during field update."""
        action = UpdateEntityAction(populated_service)
        book_id = populated_service._test_book_ids[0]
        book = populated_service.get_by_id(book_id)

        # Search for the book by ID
        mock_io["add_input"]("1")  # ID search
        mock_io["add_input"](str(book_id))

        # Cancel during update
        mock_io["add_input"]("cancel")

        result = action.execute()

        assert result.error is False
        # Book should remain unchanged
        unchanged_book = populated_service.get_by_id(book_id)
        assert unchanged_book.title == book.title

    def test_update_no_changes(self, populated_service, mock_io, multiple_books):
        """Test update with no changes (all fields skipped)."""
        action = UpdateEntityAction(populated_service)
        book = multiple_books[0]

        # Search for the book
        mock_io["add_input"]("2")  # Title search
        mock_io["add_input"](book.title)

        # Skip all fields
        mock_io["add_input"]("")  # Skip title
        mock_io["add_input"]("")  # Skip author
        mock_io["add_input"]("")  # Skip year
        mock_io["add_input"]("")  # Skip ISBN

        result = action.execute()

        assert result.error is False
        assert any("No changes" in output for output in mock_io["outputs"])

    def test_update_multiple_results_selection(self, populated_service, mock_io):
        """Test selecting from multiple search results."""
        action = UpdateEntityAction(populated_service)

        # Search by author that has multiple books
        mock_io["add_input"]("3")  # Author search
        mock_io["add_input"]("Author 1")  # Author with 2 books

        # Select the second book
        mock_io["add_input"]("2")  # Choose second book

        # Skip all updates
        mock_io["add_input"]("")  # Skip title
        mock_io["add_input"]("")  # Skip author
        mock_io["add_input"]("")  # Skip year
        mock_io["add_input"]("")  # Skip ISBN

        result = action.execute()

        assert result.error is False
        # Should have shown multiple results
        assert any("Found 2" in output for output in mock_io["outputs"])

    def test_update_with_validation_error(self, populated_service, mock_io, multiple_books):
        """Test update with validation error."""
        action = UpdateEntityAction(populated_service)
        book = multiple_books[0]

        # Search for the book
        mock_io["add_input"]("2")  # Title search
        mock_io["add_input"](book.title)

        # Try to set invalid year
        mock_io["add_input"]("")  # Skip title
        mock_io["add_input"]("")  # Skip author
        mock_io["add_input"]("1300")  # Invalid year
        mock_io["add_input"]("")  # Skip ISBN

        # Should still be able to continue
        # Enter valid year
        mock_io["add_input"]("2020")  # Valid year
        mock_io["add_input"]("y")  # Confirm

        result = action.execute()

        assert result.error is False
        # Should have shown error message
        assert any("year" in output.lower() for output in mock_io["outputs"])


class TestEntityServiceAction:
    """Tests for EntityServiceAction base class."""

    def test_entity_name_property(self, entity_service):
        """Test entity_name property."""
        action = ListEntitiesAction(entity_service)
        assert action.entity_name == "Book"

    def test_editable_fields(self, entity_service):
        """Test getting editable fields."""
        action = ListEntitiesAction(entity_service)
        fields = action.editable_entity_fields_names()

        # Should include all fields except 'id'
        assert "id" not in fields
        assert "title" in fields
        assert "author" in fields
        assert "year" in fields
        assert "isbn" in fields

    def test_not_editable_fields_classvar(self, entity_service):
        """Test not_editable_fields class variable."""
        from src.actions.entity_service_action import EntityServiceAction
        assert "id" in EntityServiceAction.not_editable_fields
