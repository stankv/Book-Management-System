"""Pytest configuration and fixtures for the Book Management System tests."""

import pytest
import shutil
from pathlib import Path
from uuid import UUID
from typing import Generator, Any

from src.models.book import Book
from src.storage.json_storage import JsonStorage
from src.services.entity_service import EntityService
from src.services.validation_service import ValidationService
from src.settings import MIN_PUBLICATION_YEAR, MAX_PUBLICATION_YEAR


# === Фикстуры для тестовых данных ===


@pytest.fixture(scope="function")  # Changed from session to function for better isolation
def test_data_dir() -> Generator[Path, None, None]:
    """Create and clean up test data directory.

    This fixture runs once per test function and ensures the test data
    directory is clean before each test.

    Yields:
        Path: Path to the test data directory
    """
    test_dir = Path(__file__).parent / "test_data"

    # Clean up any existing test data
    if test_dir.exists():
        shutil.rmtree(test_dir)

    # Create fresh test directory
    test_dir.mkdir(parents=True, exist_ok=True)

    yield test_dir

    # Cleanup after each test
    if test_dir.exists():
        shutil.rmtree(test_dir)


@pytest.fixture
def json_test_file(test_data_dir: Path) -> Path:
    """Create a path for a JSON test file.

    Args:
        test_data_dir: Test data directory fixture

    Returns:
        Path: Path to a JSON test file
    """
    return test_data_dir / "test_books.json"


@pytest.fixture
def json_storage(json_test_file: Path) -> JsonStorage:
    """Create a JsonStorage instance for testing.

    Args:
        json_test_file: JSON test file path fixture

    Returns:
        JsonStorage: Storage instance configured for testing
    """
    return JsonStorage(json_test_file)


# === Фикстуры для тестовых книг ===


@pytest.fixture
def sample_book_data() -> dict[str, Any]:
    """Provide sample book data.

    Returns:
        dict: Sample book data with valid values
    """
    return {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "year": 2008,
        "isbn": "9780132350884",
    }


@pytest.fixture
def sample_book(sample_book_data: dict[str, Any]) -> Book:
    """Create a sample book instance.

    Args:
        sample_book_data: Sample book data fixture

    Returns:
        Book: Book instance with sample data
    """
    return Book(**sample_book_data)


@pytest.fixture
def another_sample_book() -> Book:
    """Create another sample book instance.

    Returns:
        Book: Another book instance with different data
    """
    return Book(
        title="The Pragmatic Programmer", author="David Thomas", year=1999, isbn="9780201616224"
    )


@pytest.fixture
def book_with_uuid(sample_book: Book) -> Book:
    """Create a sample book with a specific UUID for testing.

    Args:
        sample_book: Sample book fixture

    Returns:
        Book: Book with a fixed UUID for predictable testing
    """
    book = sample_book
    book.id = UUID("12345678-1234-5678-1234-567812345678")
    return book


@pytest.fixture
def multiple_books() -> list[Book]:
    """Create multiple book instances for testing.

    Returns:
        list[Book]: List of book instances
    """
    return [
        Book(title="Book 1", author="Author 1", year=2000, isbn="9780000000001"),
        Book(title="Book 2", author="Author 2", year=2001, isbn="9780000000002"),
        Book(title="Book 3", author="Author 1", year=2002, isbn="9780000000003"),
        Book(title="Python Book", author="Author 3", year=2003, isbn="9780000000004"),
        Book(
            title="Clean Architecture", author="Robert C. Martin", year=2017, isbn="9780134494166"
        ),
    ]


# === Фикстуры для сервисов ===


@pytest.fixture
def entity_service(json_storage: JsonStorage) -> EntityService:
    """Create an EntityService instance for testing.

    Args:
        json_storage: JSON storage fixture

    Returns:
        EntityService: Service instance configured for testing
    """
    service = EntityService(entity_type=Book, storage=json_storage)
    # Clear any cached data
    service._entities_data = {}
    return service


@pytest.fixture
def populated_service(entity_service: EntityService, multiple_books: list[Book]) -> EntityService:
    """Create an EntityService pre-populated with test books.

    Args:
        entity_service: Entity service fixture
        multiple_books: Multiple books fixture

    Returns:
        EntityService: Service with books already added
    """
    # Clear any existing data
    entity_service._entities_data = {}

    # Add books and store their IDs
    entity_service._test_book_ids = []
    for book in multiple_books:
        new_book = Book(title=book.title, author=book.author, year=book.year, isbn=book.isbn)
        entity_service.add(new_book)
        entity_service._test_book_ids.append(new_book.id)

    return entity_service


@pytest.fixture
def validation_service() -> ValidationService:
    """Create a ValidationService instance.

    Returns:
        ValidationService: Validation service instance
    """
    return ValidationService()


# === Фикстуры для тестирования действий (actions) ===


@pytest.fixture
def mock_action_result():
    """Create a mock action result for testing.

    Returns:
        dict: Mock action result structure
    """
    from src.actions.base_action import ActionResult

    return ActionResult


@pytest.fixture
def mock_io(monkeypatch):
    """Mock input/output for testing user interactions.

    This fixture provides a way to simulate user input and capture output.

    Args:
        monkeypatch: pytest monkeypatch fixture

    Returns:
        dict: Dictionary with input_queue and output_capture
    """
    inputs = []
    outputs = []

    def mock_input(prompt=""):
        if prompt:
            outputs.append(prompt)
        if inputs:
            return inputs.pop(0)
        return ""

    def mock_print(*args, **kwargs):
        outputs.append(" ".join(str(arg) for arg in args))

    monkeypatch.setattr("builtins.input", mock_input)
    monkeypatch.setattr("builtins.print", mock_print)

    return {
        "inputs": inputs,
        "outputs": outputs,
        "add_input": lambda x: inputs.append(x),
        "clear": lambda: (inputs.clear(), outputs.clear()),
    }


# === Фикстуры для тестирования граничных значений ===


@pytest.fixture
def valid_years() -> list[int]:
    """Provide a list of valid publication years.

    Returns:
        list[int]: Valid year values
    """
    return [MIN_PUBLICATION_YEAR, 2000, 2020, MAX_PUBLICATION_YEAR]


@pytest.fixture
def invalid_years() -> list[int]:
    """Provide a list of invalid publication years.

    Returns:
        list[int]: Invalid year values (too early or too late)
    """
    return [MIN_PUBLICATION_YEAR - 1, 1400, MAX_PUBLICATION_YEAR + 1, 2100]


@pytest.fixture
def valid_isbns() -> list[str]:
    """Provide a list of valid ISBNs.

    Returns:
        list[str]: Valid ISBNs (10 and 13 digit, with and without hyphens)
    """
    return [
        "0132350882",  # 10 digit
        "9780132350884",  # 13 digit
        "0-13-235088-2",  # 10 with hyphens
        "978-0-13-235088-4",  # 13 with hyphens
        "0 13 235088 2",  # 10 with spaces
    ]


@pytest.fixture
def invalid_isbns() -> list[str]:
    """Provide a list of invalid ISBNs.

    Returns:
        list[str]: Invalid ISBNs (wrong length, wrong characters)
    """
    return [
        "123",  # too short
        "9780132350884123",  # too long
        "978-0-13-235088-4-5",  # too many parts
        "ISBN-13: 9780132350884",  # contains letters
        "abc",  # not numbers
    ]


# === Фикстуры для создания временных файлов ===


@pytest.fixture
def temp_json_file(tmp_path: Path) -> Path:
    """Create a temporary JSON file path.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        Path: Path to temporary JSON file
    """
    return tmp_path / "temp_books.json"


@pytest.fixture
def corrupted_json_file(temp_json_file: Path) -> Path:
    """Create a corrupted JSON file for testing error handling.

    Args:
        temp_json_file: Temporary JSON file fixture

    Returns:
        Path: Path to corrupted JSON file
    """
    temp_json_file.write_text("This is not valid JSON")
    return temp_json_file


# === Фикстуры для тестирования исключений ===


@pytest.fixture
def expected_exception_messages() -> dict[str, str]:
    """Provide expected exception messages for testing.

    Returns:
        dict: Mapping of exception types to expected message patterns
    """
    return {
        "BookNotFoundError": "Book with ID",
        "BookValidationError": "Incorrect data for book",
        "BookISBNError": "Incorrect ISBN format",
        "BookYearError": "Incorrect year of publication",
        "StorageReadError": "Error reading data",
        "StorageWriteError": "Failed to save data",
    }
