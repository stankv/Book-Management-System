import logging
from pathlib import Path

from demo.demo_data import book1, book2, book3
from src.managers.base_manager import BaseManager
from src.models.book import Book
from src.services.entity_service import EntityService
from src.storage.json_storage import JsonStorage

log = logging.getLogger(__name__)

class BookManager(BaseManager):
    def __init__(self, data_dir: Path):
        self.running = True
        self.books_storage = JsonStorage(data_dir / "books.json")
        self.books_service = EntityService(entity_type=Book, storage=self.books_storage)

    def _display_menu(self):
        print("Book Manager menu:")
        print("Choose an option: (WIP)")


    def run(self):
        log.info("Start Book Manager")

        while self.running:
            self.running = False
            self._display_menu()
            self.books_service.add(book1)
            self.books_service.add(book2)
            self.books_service.add(book3)
