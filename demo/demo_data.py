from pathlib import Path

from src.models.book import Book

from src.services.entity_service import EntityService
from src.storage.json_storage import JsonStorage

book1 = Book(
    title="Book 1",
    author="Author1",
    year=1999,
    isbn="ISBN 978-5-6044166-1-7",
)
book2 = Book(
    title="Book 2",
    author="Author2",
    year=2004,
    isbn="ISBN 978-5-6032166-2-6",
)
book3 = Book(
    title="Book 3",
    author="Author3",
    year=2008,
    isbn="ISBN 978-5-6082166-3-5",
)

def main():
    # создание json-файла с демо данными
    data_dir = Path(__file__).parent.parent / "src" / "data"
    books_storage = JsonStorage(data_dir / "books.json")
    books_service = EntityService(entity_type=Book, storage=books_storage)
    books_service.add(book1)
    books_service.add(book2)
    books_service.add(book3)
    print("file books.json with demo data created!")

if __name__ == "__main__":
    main()
