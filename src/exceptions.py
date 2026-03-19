"""
Book Management System application exception hierarchy.
The base class is BookManagementError, from which all others inherit.
"""


class BookManagementError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str = "Application error occurred"):
        """Initialize the base application exception.

        Args:
            message: Error message describing what went wrong"""
        self.message = message
        super().__init__(self.message)


# === Storage errors ===
class StorageError(BookManagementError):
    """Base exception for storage errors."""

    def __init__(self, message: str = "Data Warehouse Error"):
        """Initialize storage base exception.

        Args:
            message: Error message describing the storage issue"""
        super().__init__(message)


class StorageReadError(StorageError):
    """Error reading from storage"""

    def __init__(self, details: str = ""):
        """Initialize storage read error.

        Args:
            details: Additional details about the read failure"""
        message = f"Error reading data: {details}" if details else "Unable to read from storage"
        super().__init__(message)


class StorageWriteError(StorageError):
    """Error writing to storage."""

    def __init__(self, details: str = ""):
        """Initialize storage write error.

        Args:
            details: Additional details about the write failure"""
        message = f"Error data writing: {details}" if details else "Failed to save data to storage"
        super().__init__(message)


class StorageCorruptedError(StorageReadError):
    """Error, the storage file is corrupt"""

    def __init__(self, details: str = ""):
        """Initialize storage corruption error.

        Args:
            details: Additional details about the corruption"""
        message = f"Data file is corrupted: {details}" if details else "Data file is corrupt"
        super().__init__(message)


# === Entity Errors ===
class EntityError(BookManagementError):
    """Base exception for entity errors."""

    def __init__(self, entity_name: str = "entity", message: str = ""):
        """Initialize entity base exception.

        Args:
            entity_name: Name of the entity type (e.g., 'book', 'user')
            message: Error message describing the entity issue"""
        self.entity_name = entity_name
        if not message:
            message = f"Error working with {entity_name}"
        super().__init__(message)


class EntityNotFoundError(EntityError):
    """Exception when entity is not found."""

    def __init__(self, entity_name: str = "entity", entity_id=None, message: str = ""):
        """Initialize entity not found error.

        Args:
            entity_name: Name of the entity type
            entity_id: ID of the entity that wasn't found
            message: Custom error message"""
        self.entity_id = entity_id
        if not message:
            if entity_id:
                message = f"{entity_name.capitalize()} with ID {entity_id} not found"
            else:
                message = f"{entity_name.capitalize()} not found"
        super().__init__(entity_name, message)


class EntityAlreadyExistsError(EntityError):
    """Exception when an entity with this data already exists."""

    def __init__(self, entity_name: str = "entity", details: str = "", message: str = ""):
        """Initialize entity already exists error.

        Args:
            entity_name: Name of the entity type
            details: Additional details about why it already exists
            message: Custom error message"""
        if not message:
            message = f"{entity_name.capitalize()} with this data already exists"
            if details:
                message += f" ({details})"
        super().__init__(entity_name, message)


class EntityValidationError(EntityError):
    """Entity data validation error exception."""

    def __init__(self, entity_name: str = "entity", field: str = "", message: str = ""):
        """Initialize entity validation error.

        Args:
            entity_name: Name of the entity type
            field: Name of the field that failed validation
            message: Custom error message"""
        self.field = field
        if not message:
            if field:
                message = f"Incorrect field value '{field}' for {entity_name}"
            else:
                message = f"Incorrect data for {entity_name}"
        super().__init__(entity_name, message)


# === Specific exceptions for books ===
class BookError(EntityError):
    """Base exception for book errors."""

    def __init__(self, message: str = "Book Error"):
        """Initialize book base exception.

        Args:
            message: Error message for book-related issues"""
        super().__init__("book", message)


class BookNotFoundError(BookError, EntityNotFoundError):
    """Book not found."""

    def __init__(self, book_id=None, message: str = ""):
        """Initialize book not found error.

        Args:
            book_id: ID of the book that wasn't found
            message: Custom error message"""
        EntityNotFoundError.__init__(self, "book", book_id, message)


class BookAlreadyExistsError(BookError, EntityAlreadyExistsError):
    """A book with this data already exists."""

    def __init__(self, details: str = "", message: str = ""):
        """Initialize book already exists error.

        Args:
            details: Additional details about why it already exists
            message: Custom error message"""
        EntityAlreadyExistsError.__init__(self, "book", details, message)


class BookValidationError(BookError, EntityValidationError):
    """Error validating book data."""

    def __init__(self, field: str = "", message: str = ""):
        """Initialize book validation error.

        Args:
            field: Name of the field that failed validation
            message: Custom error message"""
        EntityValidationError.__init__(self, "book", field, message)


class BookISBNError(BookValidationError):
    """Error in ISBN format."""

    def __init__(self, isbn: str = "", message: str = ""):
        """Initialize ISBN format error.

        Args:
            isbn: The invalid ISBN value
            message: Custom error message"""
        if not message:
            message = f"Incorrect ISBN format: {isbn}" if isbn else "Incorrect ISBN format"
        super().__init__("isbn", message)


class BookYearError(BookValidationError):
    """Error in year of publication."""

    def __init__(self, year: int = 0, message: str = ""):
        """Initialize year validation error.

        Args:
            year: The invalid year value
            message: Custom error message"""
        if not message:
            message = f"Incorrect year of publication: {year}" if year else "Incorrect year of publication"
        super().__init__("year", message)


# === User Action Errors ===
class UserInputError(BookManagementError):
    """User data input failed."""

    def __init__(self, message: str = "Incorrect data input"):
        """Initialize user input error.

        Args:
            message: Error message about the input issue"""
        super().__init__(message)


class ActionCancelledError(UserInputError):
    """The action was canceled by the user."""

    def __init__(self, message: str = "Operation cancelled"):
        """Initialize action cancelled error.

        Args:
            message: Message indicating the action was cancelled"""
        super().__init__(message)


class InvalidChoiceError(UserInputError):
    """A menu item that does not exist is selected."""

    def __init__(self, choice: str = "", message: str = ""):
        """Initialize invalid menu choice error.

        Args:
            choice: The invalid choice that was entered
            message: Custom error message"""
        if not message:
            message = f"Incorrect selection: {choice}" if choice else "Incorrect selection of menu item"
        super().__init__(message)
