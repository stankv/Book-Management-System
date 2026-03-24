"""Unit tests for validation service."""

import pytest
from src.services.validation_service import ValidationService
from src.exceptions import BookISBNError, BookYearError, BookValidationError
from src.settings import MIN_PUBLICATION_YEAR, MAX_PUBLICATION_YEAR


class TestValidationService:
    """Tests for ValidationService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ValidationService()

    # === ISBN Validation Tests ===

    @pytest.mark.parametrize(
        "isbn",
        [
            "0132350882",  # 10 digit
            "9780132350884",  # 13 digit
            "0-13-235088-2",  # 10 with hyphens
            "978-0-13-235088-4",  # 13 with hyphens
            "0 13 235088 2",  # 10 with spaces
        ],
    )
    def test_validate_isbn_valid(self, isbn):
        """Test validation of valid ISBNs."""
        cleaned = self.service.validate_isbn(isbn)
        # Should remove hyphens and spaces
        assert "-" not in cleaned
        assert " " not in cleaned
        assert cleaned.isdigit()

    def test_validate_isbn_empty_allowed(self):
        """Test that empty ISBN is allowed (optional field)."""
        result = self.service.validate_isbn("")
        assert result == ""

    @pytest.mark.parametrize(
        "isbn",
        [
            "123",  # too short
            "9780132350884123",  # too long
            "abc",  # not digits
            "ISBN-13: 9780132350884",  # contains letters
        ],
    )
    def test_validate_isbn_invalid(self, isbn):
        """Test validation of invalid ISBNs raises appropriate errors."""
        with pytest.raises(BookISBNError) as exc_info:
            self.service.validate_isbn(isbn)
        assert "ISBN" in str(exc_info.value)

    # === Year Validation Tests ===

    @pytest.mark.parametrize(
        "year",
        [
            MIN_PUBLICATION_YEAR,
            2000,
            2020,
            MAX_PUBLICATION_YEAR,
        ],
    )
    def test_validate_year_valid(self, year):
        """Test validation of valid years."""
        result = self.service.validate_year(year)
        assert result == year

    @pytest.mark.parametrize(
        "year",
        [
            MIN_PUBLICATION_YEAR - 1,
            1400,
            MAX_PUBLICATION_YEAR + 1,
            2100,
        ],
    )
    def test_validate_year_invalid(self, year):
        """Test validation of invalid years raises BookYearError."""
        with pytest.raises(BookYearError) as exc_info:
            self.service.validate_year(year)
        assert "year" in str(exc_info.value).lower()

    def test_validate_year_with_update_flag(self):
        """Test year validation with for_update flag."""
        future_year = MAX_PUBLICATION_YEAR + 1

        # Without update flag - should raise error
        with pytest.raises(BookYearError):
            self.service.validate_year(future_year, for_update=False)

        # With update flag - should still raise error (different message)
        with pytest.raises(BookYearError) as exc_info:
            self.service.validate_year(future_year, for_update=True)
        assert "should be between" in str(exc_info.value)

    # === Required Field Validation Tests ===

    @pytest.mark.parametrize(
        "value,field",
        [
            ("Valid Title", "title"),
            ("Valid Author", "author"),
            ("  Trimmed  ", "title"),  # Should be stripped
        ],
    )
    def test_validate_required_field_valid(self, value, field):
        """Test validation of required fields with valid input."""
        result = self.service.validate_required_field(value, field)
        assert result == value.strip()

    @pytest.mark.parametrize(
        "value,field",
        [
            ("", "title"),
            ("   ", "author"),
            (None, "title"),
        ],
    )
    def test_validate_required_field_invalid(self, value, field):
        """Test validation of required fields with empty input."""
        with pytest.raises(BookValidationError) as exc_info:
            self.service.validate_required_field(value, field)
        assert "cannot be empty" in str(exc_info.value)
        assert field in str(exc_info.value)
