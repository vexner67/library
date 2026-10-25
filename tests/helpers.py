from datetime import date
from uuid import UUID, uuid7

from domain.author.author import Author
from domain.author.name import Name
from domain.book.book import Book
from domain.book.publication_year import PublicationYear
from domain.book.title import Title
from domain.exceptions import AlreadyExistsError, NotFoundError


def make_author(
    name: str = "Лев Толстой",
    birth_date: date = date(1828, 9, 9),
    death_date: date | None = None,
) -> Author:
    return Author(uuid7(), Name(name), birth_date, death_date)


def make_book(
    author_ids: list[UUID],
    title: str = "Война и мир",
    year: int = 1869,
) -> Book:
    return Book(uuid7(), Title(title), author_ids, PublicationYear(year))


# Хранилища в памяти: сервисы и консоль проверяются без файлов.
class InMemoryAuthorRepository:
    def __init__(self) -> None:
        self.authors: dict[UUID, Author] = {}

    def add(self, author: Author) -> None:
        if author.id in self.authors:
            raise AlreadyExistsError(f"Автор {author.id} уже существует")

        self.authors[author.id] = author

    def get_by_id(self, author_id: UUID) -> Author | None:
        return self.authors.get(author_id)

    def get_all(self) -> list[Author]:
        return list(self.authors.values())

    def find_by_name(self, name: str) -> list[Author]:
        query = name.strip().casefold()
        return [
            author for author in self.authors.values()
            if query and query in author.name.value.casefold()
        ]

    def update(self, author: Author) -> None:
        if author.id not in self.authors:
            raise NotFoundError(f"Автор {author.id} не найден")

        self.authors[author.id] = author

    def delete(self, author_id: UUID) -> None:
        if author_id not in self.authors:
            raise NotFoundError(f"Автор {author_id} не найден")

        del self.authors[author_id]


class InMemoryBookRepository:
    def __init__(self) -> None:
        self.books: dict[UUID, Book] = {}

    def add(self, book: Book) -> None:
        if book.id in self.books:
            raise AlreadyExistsError(f"Книга {book.id} уже существует")

        self.books[book.id] = book

    def get_by_id(self, book_id: UUID) -> Book | None:
        return self.books.get(book_id)

    def get_all(self) -> list[Book]:
        return list(self.books.values())

    def find_by_title(self, title: str) -> list[Book]:
        query = title.strip().casefold()
        return [
            book for book in self.books.values()
            if query in book.title.value.casefold()
        ]

    def update(self, book: Book) -> None:
        if book.id not in self.books:
            raise NotFoundError(f"Книга {book.id} не найдена")

        self.books[book.id] = book

    def delete(self, book_id: UUID) -> None:
        if book_id not in self.books:
            raise NotFoundError(f"Книга {book_id} не найдена")

        del self.books[book_id]
