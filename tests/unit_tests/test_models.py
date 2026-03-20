"""Unit tests for models module."""

import pytest
from uuid import UUID, uuid4
from src.models.base_entity import BaseEntity
from src.models.book import Book


class TestBaseEntity:
    """Tests for BaseEntity class."""

    def test_base_entity_creation(self):
        """Test that BaseEntity creates with a valid UUID."""
        entity = BaseEntity()
        assert isinstance(entity.id, UUID)
        assert entity.id is not None

    def test_base_entity_unique_ids(self):
        """Test that two entities have different IDs."""
        entity1 = BaseEntity()
        entity2 = BaseEntity()
        assert entity1.id != entity2.id

    def test_base_entity_with_specific_id(self):
        """Test that BaseEntity can be created with a specific ID."""
        specific_id = uuid4()
        entity = BaseEntity(id=specific_id)
        assert entity.id == specific_id


class TestBook:
    """Tests for Book class."""

    def test_book_creation_with_defaults(self):
        """Test book creation with default values."""
        book = Book()
        assert isinstance(book.id, UUID)
        assert book.title == ""
        assert book.author == ""
        assert book.year == 0
        assert book.isbn == ""

    def test_book_creation_with_values(self, sample_book_data):
        """Test book creation with provided values."""
        book = Book(**sample_book_data)
        assert book.title == sample_book_data["title"]
        assert book.author == sample_book_data["author"]
        assert book.year == sample_book_data["year"]
        assert book.isbn == sample_book_data["isbn"]

    def test_book_string_representation(self, sample_book):
        """Test the string representation of a book."""
        book_str = str(sample_book)
        assert sample_book.title in book_str
        assert sample_book.author in book_str
        assert str(sample_book.year) in book_str
        assert sample_book.isbn in book_str

    @pytest.mark.parametrize("field", ["title", "author", "year", "isbn"])
    def test_book_field_access(self, sample_book, field):
        """Test that book fields can be accessed."""
        assert hasattr(sample_book, field)
        value = getattr(sample_book, field)
        assert value is not None

    def test_book_inherits_from_base_entity(self):
        """Test that Book inherits from BaseEntity."""
        book = Book()
        assert isinstance(book, BaseEntity)
        assert hasattr(book, "id")
        