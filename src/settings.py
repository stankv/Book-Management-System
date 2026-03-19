# src/config.py
"""
Configuration constants for the Book Management System.
"""

from datetime import datetime

# Year validation constants
MIN_PUBLICATION_YEAR = 1450  # Year of Gutenberg's printing press invention
MAX_PUBLICATION_YEAR = datetime.now().year

# ISBN validation constants
ISBN_VALID_LENGTHS = {10, 13}

# Field requirements
REQUIRED_FIELDS = {
    "Book": ["title", "author"],  # Fields that cannot be empty for Book entity
}

# Storage constants
JSON_INDENT = 2
