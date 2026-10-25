import json
from pathlib import Path
from typing import Any
from uuid import UUID

from domain.book.book import Book
from domain.book.publication_year import PublicationYear
from domain.book.title import Title
from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    StorageError,
    ValidationError,
)


# Хранит книги в JSON-файле вида {"books": [...]}.
# Каждая операция заново читает файл и сразу записывает изменения.
class JsonBookRepository:
    def __init__(self, file_path: str | Path) -> None:
        self.__file_path = Path(file_path)

        # Пустой файл создается сразу, чтобы чтение всегда находило его.
        if not self.__file_path.exists():
            self.__write_data([])

    def __read_data(self) -> list[dict[str, Any]]:
        data = self.__read_file()

        if not isinstance(data, dict) or not isinstance(
            data.get("books"), list
        ):
            raise StorageError(f"В файле {self.__file_path} нет списка books")

        books: list[dict[str, Any]] = data["books"]
        return books

    def __read_file(self) -> Any:
        try:
            with self.__file_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise StorageError(
                f"Файл {self.__file_path} повреждён: некорректный JSON"
            ) from error
        except OSError as error:
            raise StorageError(
                f"Не удалось прочитать файл {self.__file_path}"
            ) from error

    def __write_data(self, books: list[dict[str, Any]]) -> None:
        try:
            self.__file_path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(
                {"books": books}, ensure_ascii=False, indent=4
            )
            self.__file_path.write_bytes(content.encode("utf-8"))
        except (OSError, ValueError) as error:
            raise StorageError(
                f"Не удалось записать файл {self.__file_path}"
            ) from error

    # Любая ошибка в записи файла превращается в StorageError
    # с понятным сообщением вместо KeyError или ValueError.
    def __to_book(self, item: dict[str, Any]) -> Book:
        try:
            return Book(
                book_id=UUID(item["id"]),
                title=Title(item["title"]),
                publication_year=PublicationYear(item["publication_year"]),
                author_ids=[
                    UUID(author_id)
                    for author_id in item["author_ids"]
                ],
            )
        except (
            KeyError,
            ValueError,
            TypeError,
            AttributeError,
            ValidationError,
        ) as error:
            raise StorageError(
                f"В файле {self.__file_path} повреждена запись книги"
            ) from error

    @staticmethod
    def __to_dict(book: Book) -> dict[str, Any]:
        return {
            "id": str(book.id),
            "title": book.title.value,
            "publication_year": book.publication_year.value,
            "author_ids": [
                str(author_id)
                for author_id in book.author_ids
            ],
        }

    @staticmethod
    def __find_index(
        books: list[dict[str, Any]], book_id: UUID
    ) -> int | None:
        for index, item in enumerate(books):
            if item.get("id") == str(book_id):
                return index

        return None

    def add(self, book: Book) -> None:
        books = self.__read_data()

        if self.__find_index(books, book.id) is not None:
            raise AlreadyExistsError(f"Книга {book.id} уже существует")

        books.append(self.__to_dict(book))
        self.__write_data(books)

    def get_by_id(self, book_id: UUID) -> Book | None:
        books = self.__read_data()
        index = self.__find_index(books, book_id)

        if index is None:
            return None

        return self.__to_book(books[index])

    def get_all(self) -> list[Book]:
        return [
            self.__to_book(item)
            for item in self.__read_data()
        ]

    def find_by_title(self, title: str) -> list[Book]:
        normalized_title = title.strip().casefold()

        return [
            book
            for book in self.get_all()
            if normalized_title in book.title.value.casefold()
        ]

    def update(self, book: Book) -> None:
        books = self.__read_data()
        index = self.__find_index(books, book.id)

        if index is None:
            raise NotFoundError(f"Книга {book.id} не найдена")

        books[index] = self.__to_dict(book)
        self.__write_data(books)

    def delete(self, book_id: UUID) -> None:
        books = self.__read_data()
        index = self.__find_index(books, book_id)

        if index is None:
            raise NotFoundError(f"Книга {book_id} не найдена")

        del books[index]
        self.__write_data(books)
