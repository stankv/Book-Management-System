"""
Validation service for book-related data.
"""

import logging

from src.exceptions import BookISBNError, BookYearError, BookValidationError
from src.settings import MIN_PUBLICATION_YEAR, MAX_PUBLICATION_YEAR, ISBN_VALID_LENGTHS

log = logging.getLogger(__name__)


class ValidationService:
    """
    Service providing validation methods for book data.

    Centralizes validation logic to ensure consistency across
    different parts of the application (add, update actions, etc.).
    """

    @staticmethod
    def validate_isbn(isbn: str, field_name: str = "isbn") -> str:
        """
        Validate and normalize an ISBN.

        Args:
            isbn: The ISBN string to validate.
            field_name: The field name for error messages.

        Returns:
            str: The normalized ISBN (without hyphens or spaces).

        Raises:
            BookISBNError: If the ISBN is invalid.
        """

        if not isbn:
            return isbn  # Empty ISBN is allowed (optional field)

        # Remove hyphens and spaces
        isbn_clean = isbn.replace('-', '').replace(' ', '')

        # Check if it contains only digits
        if not isbn_clean.isdigit():
            raise BookISBNError(
                isbn,
                "ISBN must contain only digits, hyphens, or spaces"
            )

        # Check length
        if len(isbn_clean) not in ISBN_VALID_LENGTHS:
            valid_lengths = ", ".join(str(l) for l in sorted(ISBN_VALID_LENGTHS))
            raise BookISBNError(
                isbn,
                f"ISBN must be {valid_lengths} digits long (found {len(isbn_clean)})"
            )

        return isbn_clean

    @staticmethod
    def validate_year(year: int, field_name: str = "year", for_update: bool = False) -> int:
        """
        Validate a publication year.

        Args:
            year: The year to validate.
            field_name: The field name for error messages.
            for_update: If True, uses more lenient validation for updates.

        Returns:
            int: The validated year.

        Raises:
            BookYearError: If the year is invalid.
        """

        if year < MIN_PUBLICATION_YEAR or year > MAX_PUBLICATION_YEAR:
            if for_update:
                message = (
                    f"The year should be between {MIN_PUBLICATION_YEAR} "
                    f"and {MAX_PUBLICATION_YEAR} (including tolerance for pre-release books)"
                )
            else:
                message = (
                    f"The year must be between {MIN_PUBLICATION_YEAR} "
                    f"and {MAX_PUBLICATION_YEAR}"
                )
            raise BookYearError(year, message)

        return year

    @staticmethod
    def validate_required_field(value: str, field_name: str, entity_name: str = "Book") -> str:
        """
        Validate that a required field is not empty.

        Args:
            value: The field value to validate.
            field_name: The name of the field.
            entity_name: The entity type name.

        Returns:
            str: The validated value.

        Raises:
            BookValidationError: If the field is empty.
        """

        if not value or not value.strip():
            raise BookValidationError(
                field_name,
                f"{field_name} cannot be empty for {entity_name}"
            )
        return value.strip()
