import logging
from pathlib import Path

from src.managers.book_manager import BookManager


def main():
    """Main entry point for the Book Management System application.

    Initializes logging, creates the data directory path, instantiates the BookManager,
    and starts the application loop.

    The data directory is created as a 'data' subdirectory in the same location
    as this script.

    Returns:
        None"""

    logging.basicConfig(level=logging.INFO)

    data_dir = Path(__file__).parent / "data"

    manager = BookManager(data_dir=data_dir)
    manager.run()

if __name__ == "__main__":
    main()
