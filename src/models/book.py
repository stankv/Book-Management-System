from src.models.base_entity import BaseEntity
from dataclasses import dataclass


@dataclass
class Book(BaseEntity):
    title: str = ""
    author: str = ""
    year: int = 0
    isbn: str = ""

    def __str__(self):
        return f"Title: {self.title}, Author: {self.author}, Year: {self.year}, ISBN: {self.isbn}"
