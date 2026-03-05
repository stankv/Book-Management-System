import logging
from pathlib import Path

from src.managers.book_manager import BookManager


def main():
    logging.basicConfig(level=logging.INFO)

    data_dir = Path(__file__).parent / "data"

    manager = BookManager(data_dir=data_dir)
    manager.run()

if __name__ == "__main__":

    # Загрузка демо-данных и создание json-файла
    # from src.models.book import Book
    # from src.services.entity_service import EntityService
    # from src.storage.json_storage import JsonStorage
    # from demo.demo_data import book1, book2, book3
    #
    # data_dir = Path(__file__).parent / "data"
    # books_storage = JsonStorage(data_dir / "books.json")
    # books_service = EntityService(entity_type=Book, storage=books_storage)
    # books_service.add(book1)
    # books_service.add(book2)
    # books_service.add(book3)

    main()
