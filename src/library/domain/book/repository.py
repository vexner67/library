from typing import Protocol
from uuid import UUID

from domain.book.book import Book


class BookRepository(Protocol):
    def add(self, book: Book) -> None:
        raise NotImplementedError

    def get_by_id(self, book_id: UUID) -> Book | None:
        raise NotImplementedError

    def get_all(self) -> list[Book]:
        raise NotImplementedError

    def find_by_title(self, title: str) -> list[Book]:
        raise NotImplementedError

    def update(self, book: Book) -> None:
        raise NotImplementedError

    def delete(self, book_id: UUID) -> None:
        raise NotImplementedError
