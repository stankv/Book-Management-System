from src.models.base_entity import BaseEntity
from dataclasses import dataclass


@dataclass
class Book(BaseEntity):
    title: str = ""
    author: str = ""
    year: int = 0
    isbn: str = ""

    def __str__(self):
        return f"{self.title}, {self.author}, {self.year}, {self.isbn}"