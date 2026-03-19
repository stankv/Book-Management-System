"""
Book Management System application exception hierarchy.
The base class is BookManagementError, from which all others inherit.
"""


class BookManagementError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str = "Application error occurred"):
        self.message = message
        super().__init__(self.message)


# === Storage errors ===
class StorageError(BookManagementError):
    """Base exception for storage errors."""

    def __init__(self, message: str = "Data Warehouse Error"):
        super().__init__(message)


class StorageReadError(StorageError):
    """Error reading from storage"""

    def __init__(self, details: str = ""):
        message = f"Error reading data: {details}" if details else "Unable to read from storage"
        super().__init__(message)


class StorageWriteError(StorageError):
    """Error writing to storage."""

    def __init__(self, details: str = ""):
        message = f"Error data writing: {details}" if details else "Failed to save data to storage"
        super().__init__(message)


class StorageCorruptedError(StorageReadError):
    """Error, the storage file is corrupt"""

    def __init__(self, details: str = ""):
        message = f"Data file is corrupted: {details}" if details else "Data file is corrupt"
        super().__init__(message)


# === Entity Errors ===
class EntityError(BookManagementError):
    """Base exception for entity errors."""

    def __init__(self, entity_name: str = "entity", message: str = ""):
        self.entity_name = entity_name
        if not message:
            message = f"Error working with {entity_name}"
        super().__init__(message)


class EntityNotFoundError(EntityError):
    """Exception when entity is not found."""

    def __init__(self, entity_name: str = "entity", entity_id=None, message: str = ""):
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
        if not message:
            message = f"{entity_name.capitalize()} with this data already exists"
            if details:
                message += f" ({details})"
        super().__init__(entity_name, message)


class EntityValidationError(EntityError):
    """Entity data validation error exception."""

    def __init__(self, entity_name: str = "entity", field: str = "", message: str = ""):
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
        super().__init__("book", message)


class BookNotFoundError(BookError, EntityNotFoundError):
    """Book not found."""

    def __init__(self, book_id=None, message: str = ""):
        EntityNotFoundError.__init__(self, "book", book_id, message)


class BookAlreadyExistsError(BookError, EntityAlreadyExistsError):
    """A book with this data already exists."""

    def __init__(self, details: str = "", message: str = ""):
        EntityAlreadyExistsError.__init__(self, "book", details, message)


class BookValidationError(BookError, EntityValidationError):
    """Error validating book data."""

    def __init__(self, field: str = "", message: str = ""):
        EntityValidationError.__init__(self, "book", field, message)


class BookISBNError(BookValidationError):
    """Error in ISBN format."""

    def __init__(self, isbn: str = "", message: str = ""):
        if not message:
            message = f"Incorrect ISBN format: {isbn}" if isbn else "Incorrect ISBN format"
        super().__init__("isbn", message)


class BookYearError(BookValidationError):
    """Error in year of publication."""

    def __init__(self, year: int = 0, message: str = ""):
        if not message:
            message = f"Incorrect year of publication: {year}" if year else "Incorrect year of publication"
        super().__init__("year", message)


# === User Action Errors ===
class UserInputError(BookManagementError):
    """User data input failed."""

    def __init__(self, message: str = "Incorrect data input"):
        super().__init__(message)


class ActionCancelledError(UserInputError):
    """The action was canceled by the user."""

    def __init__(self, message: str = "Operation cancelled"):
        super().__init__(message)


class InvalidChoiceError(UserInputError):
    """A menu item that does not exist is selected."""

    def __init__(self, choice: str = "", message: str = ""):
        if not message:
            message = f"Incorrect selection: {choice}" if choice else "Incorrect selection of menu item"
        super().__init__(message)
