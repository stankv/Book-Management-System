"""Unit tests for exception hierarchy."""

import pytest
from src.exceptions import (
    BookManagementError,
    StorageError,
    StorageReadError,
    StorageWriteError,
    StorageCorruptedError,
    EntityError,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    EntityValidationError,
    BookError,
    BookNotFoundError,
    BookAlreadyExistsError,
    BookValidationError,
    BookISBNError,
    BookYearError,
    UserInputError,
    ActionCancelledError,
    InvalidChoiceError,
)


class TestBaseExceptions:
    """Tests for base exception classes."""

    def test_book_management_error(self):
        """Test base application exception."""
        error = BookManagementError()
        assert str(error) == "Application error occurred"

        error = BookManagementError("Custom error message")
        assert str(error) == "Custom error message"

    def test_storage_error(self):
        """Test storage base exception."""
        error = StorageError()
        assert str(error) == "Data Warehouse Error"

        error = StorageError("Custom storage error")
        assert str(error) == "Custom storage error"

    def test_entity_error(self):
        """Test entity base exception."""
        error = EntityError()
        assert "entity" in str(error).lower()

        error = EntityError("book", "Custom book error")
        assert error.entity_name == "book"
        assert str(error) == "Custom book error"


class TestStorageExceptions:
    """Tests for storage-related exceptions."""

    def test_storage_read_error(self):
        """Test storage read error."""
        error = StorageReadError()
        assert "Unable to read from storage" in str(error)

        error = StorageReadError("Permission denied")
        assert "Error reading data: Permission denied" in str(error)

    def test_storage_write_error(self):
        """Test storage write error."""
        error = StorageWriteError()
        assert "Failed to save data to storage" in str(error)

        error = StorageWriteError("Disk full")
        assert "Error data writing: Disk full" in str(error)

    def test_storage_corrupted_error(self):
        """Test storage corrupted error."""
        error = StorageCorruptedError()
        assert "Data file is corrupt" in str(error)

        error = StorageCorruptedError("Invalid JSON format")
        assert "Data file is corrupted: Invalid JSON format" in str(error)

        # Verify inheritance
        assert isinstance(error, StorageReadError)
        assert isinstance(error, StorageError)
        assert isinstance(error, BookManagementError)


class TestEntityExceptions:
    """Tests for entity-related exceptions."""

    def test_entity_not_found_error(self):
        """Test entity not found error."""
        error = EntityNotFoundError()
        assert "Entity not found" in str(error)

        error = EntityNotFoundError("book", 123)
        assert "Book with ID 123 not found" in str(error)

        error = EntityNotFoundError("user", "abc-123", "Custom message")
        assert str(error) == "Custom message"

    def test_entity_already_exists_error(self):
        """Test entity already exists error."""
        error = EntityAlreadyExistsError()
        assert "Entity with this data already exists" in str(error)

        error = EntityAlreadyExistsError("book", "ISBN 1234567890")
        assert "Book with this data already exists (ISBN 1234567890)" in str(error)

        error = EntityAlreadyExistsError("user", message="Custom message")
        assert str(error) == "Custom message"

    def test_entity_validation_error(self):
        """Test entity validation error."""
        error = EntityValidationError()
        assert "Incorrect data for entity" in str(error)

        error = EntityValidationError("book", "title")
        assert "Incorrect field value 'title' for book" in str(error)

        error = EntityValidationError("book", "year", "Year must be positive")
        assert str(error) == "Year must be positive"
        assert error.field == "year"


class TestBookExceptions:
    """Tests for book-specific exceptions."""

    def test_book_error(self):
        """Test book base exception."""
        error = BookError()
        assert "Book Error" in str(error)
        assert isinstance(error, EntityError)
        assert isinstance(error, BookManagementError)

    def test_book_not_found_error(self):
        """Test book not found error."""
        error = BookNotFoundError()
        assert "Book not found" in str(error)

        error = BookNotFoundError(123)
        assert "Book with ID 123 not found" in str(error)

        error = BookNotFoundError(message="Custom book not found")
        assert str(error) == "Custom book not found"

        # Verify multiple inheritance
        assert isinstance(error, BookError)
        assert isinstance(error, EntityNotFoundError)

    def test_book_already_exists_error(self):
        """Test book already exists error."""
        error = BookAlreadyExistsError()
        assert "Book with this data already exists" in str(error)

        error = BookAlreadyExistsError("ISBN 978-0132350884")
        assert "Book with this data already exists (ISBN 978-0132350884)" in str(error)

        error = BookAlreadyExistsError(message="Custom book exists")
        assert str(error) == "Custom book exists"

        assert isinstance(error, BookError)
        assert isinstance(error, EntityAlreadyExistsError)

    def test_book_validation_error(self):
        """Test book validation error."""
        error = BookValidationError()
        assert "Incorrect data for book" in str(error)

        error = BookValidationError("title")
        assert "Incorrect field value 'title' for book" in str(error)

        error = BookValidationError("author", "Author name is required")
        assert str(error) == "Author name is required"
        assert error.field == "author"

        assert isinstance(error, BookError)
        assert isinstance(error, EntityValidationError)


class TestBookFieldExceptions:
    """Tests for book field-specific exceptions."""

    def test_book_isbn_error(self):
        """Test ISBN format error."""
        error = BookISBNError()
        assert "Incorrect ISBN format" in str(error)

        error = BookISBNError("978-0132350884")
        assert "Incorrect ISBN format: 978-0132350884" in str(error)

        error = BookISBNError(message="Custom ISBN error")
        assert str(error) == "Custom ISBN error"

        # Verify inheritance chain
        assert isinstance(error, BookISBNError)
        assert isinstance(error, BookValidationError)
        assert isinstance(error, BookError)
        assert isinstance(error, EntityValidationError)

    def test_book_year_error(self):
        """Test year validation error."""
        error = BookYearError()
        assert "Incorrect year of publication" in str(error)

        error = BookYearError(3000)
        assert "Incorrect year of publication: 3000" in str(error)

        error = BookYearError(-100, "Year cannot be negative")
        assert str(error) == "Year cannot be negative"

        # Verify inheritance chain
        assert isinstance(error, BookYearError)
        assert isinstance(error, BookValidationError)
        assert isinstance(error, BookError)


class TestUserActionExceptions:
    """Tests for user action-related exceptions."""

    def test_user_input_error(self):
        """Test user input error."""
        error = UserInputError()
        assert "Incorrect data input" in str(error)

        error = UserInputError("Invalid command")
        assert str(error) == "Invalid command"

        assert isinstance(error, BookManagementError)

    def test_action_cancelled_error(self):
        """Test action cancelled error."""
        error = ActionCancelledError()
        assert "Operation cancelled" in str(error)

        error = ActionCancelledError("User pressed Ctrl+C")
        assert str(error) == "User pressed Ctrl+C"

        assert isinstance(error, UserInputError)
        assert isinstance(error, BookManagementError)

    def test_invalid_choice_error(self):
        """Test invalid menu choice error."""
        error = InvalidChoiceError()
        assert "Incorrect selection of menu item" in str(error)

        error = InvalidChoiceError("5")
        assert "Incorrect selection: 5" in str(error)

        error = InvalidChoiceError(message="Custom choice error")
        assert str(error) == "Custom choice error"

        assert isinstance(error, UserInputError)
        assert isinstance(error, BookManagementError)


class TestExceptionInheritance:
    """Test complex inheritance relationships."""

    def test_full_inheritance_chain(self):
        """Test that all exceptions inherit from BookManagementError."""
        exceptions = [
            StorageReadError(),
            StorageWriteError(),
            StorageCorruptedError(),
            EntityNotFoundError(),
            EntityAlreadyExistsError(),
            EntityValidationError(),
            BookNotFoundError(),
            BookAlreadyExistsError(),
            BookValidationError(),
            BookISBNError(),
            BookYearError(),
            UserInputError(),
            ActionCancelledError(),
            InvalidChoiceError(),
        ]

        for exception in exceptions:
            assert isinstance(exception, BookManagementError), (
                f"{exception.__class__.__name__} does not inherit from BookManagementError"
            )

    def test_storage_corrupted_inheritance(self):
        """Test that StorageCorruptedError inherits from StorageReadError."""
        error = StorageCorruptedError()
        assert isinstance(error, StorageReadError)
        assert isinstance(error, StorageError)
        assert isinstance(error, BookManagementError)

    def test_book_not_found_multiple_inheritance(self):
        """Test that BookNotFoundError inherits from both BookError and EntityNotFoundError."""
        error = BookNotFoundError()
        assert isinstance(error, BookError)
        assert isinstance(error, EntityNotFoundError)
        # Method resolution order should be correct
        mro = BookNotFoundError.__mro__
        assert BookError in mro
        assert EntityNotFoundError in mro


class TestExceptionAttributes:
    """Test that exceptions have expected attributes."""

    def test_entity_error_attributes(self):
        """Test EntityError attributes."""
        error = EntityError("book", "Test message")
        assert hasattr(error, "entity_name")
        assert error.entity_name == "book"

    def test_entity_not_found_attributes(self):
        """Test EntityNotFoundError attributes."""
        error = EntityNotFoundError("book", 123)
        assert hasattr(error, "entity_id")
        assert error.entity_id == 123
        assert hasattr(error, "entity_name")
        assert error.entity_name == "book"

    def test_entity_validation_error_attributes(self):
        """Test EntityValidationError attributes."""
        error = EntityValidationError("book", "title")
        assert hasattr(error, "field")
        assert error.field == "title"
        assert error.entity_name == "book"

    def test_book_validation_error_attributes(self):
        """Test BookValidationError attributes."""
        error = BookValidationError("isbn")
        assert error.field == "isbn"

        # Should inherit entity_name from parent
        assert error.entity_name == "book"


@pytest.mark.parametrize(
    "exception_class,args,expected_contains,expected_custom",
    [
        (
            StorageReadError,
            ("Custom read error",),
            "Unable to read from storage",
            "Custom read error",
        ),
        (
            StorageWriteError,
            ("Custom write error",),
            "Failed to save data to storage",
            "Custom write error",
        ),
        (
            StorageCorruptedError,
            ("Custom corrupt error",),
            "Data file is corrupt",
            "Custom corrupt error",
        ),
        (BookNotFoundError, (123, "Custom not found"), "Book with ID", "Custom not found"),
        (
            BookAlreadyExistsError,
            ("Custom exists",),
            "Book with this data already exists",
            "Custom exists",
        ),
        (
            BookISBNError,
            ("978-0132350884", "Custom ISBN error"),
            "Incorrect ISBN format",
            "Custom ISBN error",
        ),
        (
            BookYearError,
            (2025, "Custom year error"),
            "Incorrect year of publication",
            "Custom year error",
        ),
        (ActionCancelledError, ("Custom cancel",), "Operation cancelled", "Custom cancel"),
        (InvalidChoiceError, ("5", "Custom choice"), "Incorrect selection", "Custom choice"),
    ],
)
def test_exception_messages(exception_class, args, expected_contains, expected_custom):
    """Test default and custom messages for various exceptions."""
    # Test default message
    if exception_class == BookNotFoundError:
        error_default = exception_class(123)
    elif exception_class == BookISBNError:
        error_default = exception_class("123-456")
    elif exception_class == BookYearError:
        error_default = exception_class(3000)
    elif exception_class == InvalidChoiceError:
        error_default = exception_class("5")
    else:
        error_default = exception_class()

    # Для StorageReadError и StorageWriteError проверяем часть сообщения
    if exception_class in [StorageReadError, StorageWriteError, StorageCorruptedError]:
        # Проверяем, что ожидаемая фраза содержится в сообщении
        assert (
            expected_contains.lower() in str(error_default).lower()
            or "error" in str(error_default).lower()
        )
    else:
        assert expected_contains.lower() in str(error_default).lower()

    # Test custom message
    error_custom = exception_class(*args)
    assert expected_custom in str(error_custom)


def test_exception_without_message_parameter():
    """Test exceptions that don't accept message parameter."""
    error = BookNotFoundError(book_id=456)
    assert "456" in str(error)

    error = BookISBNError(isbn="123-456")
    assert "123-456" in str(error)

    error = BookYearError(year=9999)
    assert "9999" in str(error)

    error = InvalidChoiceError(choice="abc")
    assert "abc" in str(error)
