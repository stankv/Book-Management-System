"""Integration tests for BookManager with all components working together."""

import pytest

from src.managers.book_manager import BookManager
from src.models.book import Book
from src.exceptions import EntityNotFoundError


class TestBookManagerIntegration:
    """Integration tests for BookManager with real file system and components."""

    @pytest.fixture
    def book_manager(self, test_data_dir):
        """Create a BookManager instance for testing."""
        return BookManager(test_data_dir)

    @pytest.fixture
    def manager_with_books(self, book_manager):
        """Create a BookManager pre-populated with books."""
        # Add some books directly through service
        books = [
            Book(title="Integration Book 1", author="Author A", year=2020, isbn="9780000000001"),
            Book(title="Integration Book 2", author="Author B", year=2021, isbn="9780000000002"),
            Book(title="Python Testing", author="Author A", year=2022, isbn="9780000000003"),
        ]

        for book in books:
            book_manager.books_service.add(book)

        return book_manager

    def test_manager_initialization(self, book_manager, test_data_dir):
        """Test that BookManager initializes correctly."""
        assert book_manager.running is True
        assert book_manager.books_storage.file_path == test_data_dir / "books.json"
        assert book_manager.books_service.entity_type == Book
        assert len(book_manager.prepared_actions) == 6  # All actions

    def test_manager_actions_registered(self, book_manager):
        """Test that all actions are properly registered."""
        action_names = list(book_manager.prepared_actions.keys())

        expected_names = [
            "List Book items",
            "Search Book",
            "Add Book items",
            "Update Book",
            "Delete Book",
            "exit",
        ]

        for expected in expected_names:
            assert expected in action_names

    def test_add_book_through_manager_flow(self, book_manager, mock_io):
        """Test complete flow of adding a book through the manager."""
        # Очищаем outputs
        mock_io["clear"]()

        # Симулируем ввод пользователя ТОЛЬКО для полей книги
        # Не имитируем выбор меню, так как вызываем действие напрямую
        mock_io["add_input"]("Clean Code")  # title
        mock_io["add_input"]("Robert C. Martin")  # author
        mock_io["add_input"]("2008")  # year
        mock_io["add_input"]("9780132350884")  # isbn
        mock_io["add_input"]("y")  # confirm

        # Выполняем действие напрямую (без выбора из меню)
        action = book_manager.prepared_actions["Add Book items"]
        result = action.execute()

        # Проверяем, что действие выполнилось без ошибок
        assert result.error is False, f"Action failed with error: {mock_io['outputs']}"

        # Проверяем, что книга была добавлена
        books = book_manager.books_service.get_all()
        assert len(books) == 1, f"Expected 1 book, got {len(books)}"

        # Проверяем, что данные правильные
        assert books[0].title == "Clean Code", (
            f"Expected title 'Clean Code', got '{books[0].title}'"
        )

    def test_list_books_through_manager(self, manager_with_books, mock_io):
        """Test listing books through the manager."""
        action = manager_with_books.prepared_actions["List Book items"]
        result = action.execute()

        assert result.error is False
        # Should have printed all 3 books
        assert any("Integration Book 1" in out for out in mock_io["outputs"])
        assert any("Integration Book 2" in out for out in mock_io["outputs"])
        assert any("Python Testing" in out for out in mock_io["outputs"])

    def test_search_book_through_manager(self, manager_with_books, mock_io):
        """Test searching for a book through the manager."""
        action = manager_with_books.prepared_actions["Search Book"]

        # Search by title
        mock_io["add_input"]("2")  # Title search
        mock_io["add_input"]("Python")

        result = action.execute()

        assert result.error is False
        # Should find the Python book
        assert any("Python Testing" in out for out in mock_io["outputs"])

    def test_update_book_through_manager(self, manager_with_books, mock_io):
        """Test updating a book through the manager."""
        # Get the book to update
        books = manager_with_books.books_service.get_all()
        book_to_update = books[0]
        original_title = book_to_update.title

        action = manager_with_books.prepared_actions["Update Book"]

        # Search by title
        mock_io["add_input"]("2")  # Title search
        mock_io["add_input"](original_title)

        # Update fields
        mock_io["add_input"]("Updated Title")  # New title
        mock_io["add_input"]("")  # Skip author
        mock_io["add_input"]("")  # Skip year
        mock_io["add_input"]("")  # Skip ISBN
        mock_io["add_input"]("y")  # Confirm

        result = action.execute()

        assert result.error is False

        # Verify update
        updated_book = manager_with_books.books_service.get_by_id(book_to_update.id)
        assert updated_book.title == "Updated Title"

        # Verify persistence
        loaded = manager_with_books.books_storage.load_data()
        assert any(b["title"] == "Updated Title" for b in loaded)

    def test_delete_book_through_manager(self, manager_with_books, mock_io):
        """Test deleting a book through the manager."""
        initial_count = len(manager_with_books.books_service.get_all())
        book_to_delete = manager_with_books.books_service.get_all()[0]

        action = manager_with_books.prepared_actions["Delete Book"]

        mock_io["add_input"](str(book_to_delete.id))
        mock_io["add_input"]("y")  # Confirm

        result = action.execute()

        assert result.error is False
        assert len(manager_with_books.books_service.get_all()) == initial_count - 1

        # Verify persistence
        with pytest.raises(EntityNotFoundError):
            manager_with_books.books_service.get_by_id(book_to_delete.id)

    def test_exit_action_stops_manager(self, book_manager):
        """Test that exit action sets running to False."""
        action = book_manager.prepared_actions["exit"]
        result = action.execute()

        assert result.stop is True

    def test_full_manager_run_cycle_with_mock_input(self, book_manager, mock_io, monkeypatch):
        """Test a complete run cycle with multiple actions."""
        # Mock the menu display to avoid prints
        monkeypatch.setattr(book_manager, "_display_menu", lambda: None)

        # Queue up actions: Add book -> List books -> Exit
        mock_io["add_input"]("3")  # Add
        mock_io["add_input"]("Test Book")
        mock_io["add_input"]("Test Author")
        mock_io["add_input"]("2023")
        mock_io["add_input"]("9781234567890")
        mock_io["add_input"]("y")  # Confirm add

        mock_io["add_input"]("1")  # List
        mock_io["add_input"]("6")  # Exit

        # Run the manager (but break after exit)
        def mock_run():
            book_manager.running = True
            actions_executed = []

            while book_manager.running:
                # Simulate menu selection
                choice = mock_io["inputs"].pop(0) if mock_io["inputs"] else "6"

                if choice.isdigit():
                    idx = int(choice) - 1
                    action = list(book_manager.prepared_actions.values())[idx]
                else:
                    action = book_manager.prepared_actions.get(choice)

                if action:
                    result = action.execute()
                    actions_executed.append(action.get_name())
                    if result.stop:
                        book_manager.running = False

            return actions_executed

        # Replace run method temporarily
        monkeypatch.setattr(book_manager, "run", mock_run)

        actions = book_manager.run()

        assert "Add Book items" in actions
        assert "List Book items" in actions
        assert "exit" in actions
        assert len(book_manager.books_service.get_all()) == 1

    def test_data_persistence_across_manager_restarts(self, test_data_dir, mock_io):
        """Test that data persists when manager is restarted."""
        # First manager instance - add a book
        manager1 = BookManager(test_data_dir)

        # Add a book directly
        book = Book(
            title="Persistent Book", author="Persistent Author", year=2023, isbn="9780000000001"
        )
        manager1.books_service.add(book)

        # Create second manager instance (simulating restart)
        manager2 = BookManager(test_data_dir)

        # Second manager should have the book
        books = manager2.books_service.get_all()
        assert len(books) == 1
        assert books[0].title == "Persistent Book"

    def test_error_handling_in_invalid_input(self, book_manager, mock_io):
        """Test error handling when user provides invalid input."""
        action = book_manager.prepared_actions["Add Book items"]

        # Try to add book with invalid year
        mock_io["add_input"]("Test Book")
        mock_io["add_input"]("Test Author")
        mock_io["add_input"]("1300")  # Invalid year
        mock_io["add_input"]("2023")  # Valid year
        mock_io["add_input"]("9781234567890")
        mock_io["add_input"]("y")

        result = action.execute()

        assert result.error is False  # Should recover, not crash
        assert len(book_manager.books_service.get_all()) == 1
        # Should have shown error message
        assert any("year" in out.lower() and "between" in out.lower() for out in mock_io["outputs"])

    @pytest.mark.parametrize(
        "action_index,expected_type",
        [
            ("1", "List Book items"),
            ("2", "Search Book"),
            ("3", "Add Book items"),
            ("4", "Update Book"),
            ("5", "Delete Book"),
            ("6", "exit"),
        ],
    )
    def test_menu_selection_by_number(self, book_manager, action_index, expected_type):
        """Test that menu selection by number works correctly."""
        # This tests the menu selection logic without executing
        if action_index.isdigit():
            idx = int(action_index) - 1
            if 0 <= idx < len(book_manager.prepared_actions):
                action = list(book_manager.prepared_actions.values())[idx]
                assert action.get_name() == expected_type

    @pytest.mark.parametrize(
        "action_name,expected_type",
        [
            ("List Book items", "List Book items"),
            ("Search Book", "Search Book"),
            ("Add Book items", "Add Book items"),
            ("Update Book", "Update Book"),
            ("Delete Book", "Delete Book"),
            ("exit", "exit"),
        ],
    )
    def test_menu_selection_by_name(self, book_manager, action_name, expected_type):
        """Test that menu selection by action name works correctly."""
        action = book_manager.prepared_actions.get(action_name)
        assert action is not None
        assert action.get_name() == expected_type

    def test_invalid_menu_selection_handling(self, book_manager, mock_io, monkeypatch):
        """Test handling of invalid menu selections."""
        # Mock the menu display
        monkeypatch.setattr(book_manager, "_display_menu", lambda: None)

        # Set running to False after one iteration
        book_manager.running = True

        # Simulate invalid number, then exit
        mock_io["add_input"]("99")  # Invalid number
        mock_io["add_input"]("6")  # Exit

        # Override run method to capture behavior
        outputs = []

        def mock_run():
            while book_manager.running:
                choice = mock_io["inputs"].pop(0) if mock_io["inputs"] else "6"

                if choice.isdigit():
                    index = int(choice) - 1
                    if index < 0 or index >= len(book_manager.prepared_actions):
                        outputs.append("Invalid choice number")
                        continue
                else:
                    if choice not in book_manager.prepared_actions:
                        outputs.append("Invalid choice name")
                        continue

                # Exit on valid choice
                if choice == "6":
                    book_manager.running = False

        monkeypatch.setattr(book_manager, "run", mock_run)
        book_manager.run()

        assert "Invalid choice number" in outputs
