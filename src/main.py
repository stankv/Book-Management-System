import logging
from pathlib import Path

from demo.demo_data import book1, book2, book3
from src.managers.book_manager import BookManager



def main():
    logging.basicConfig(level=logging.INFO)

    data_dir = Path(__file__).parent / "data"

    manager = BookManager(data_dir=data_dir)
    manager.run()

if __name__ == "__main__":
    main()
    print(book1)
    print(book2)
    print(book3)
