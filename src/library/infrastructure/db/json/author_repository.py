import json
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

from domain.author.author import Author
from domain.author.name import Name
from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    StorageError,
    ValidationError,
)


class JsonAuthorRepository:
    def __init__(self, file_path: str | Path) -> None:
        self.__file_path = Path(file_path)

    def __load_data(self) -> list[dict[str, Any]]:
        if not self.__file_path.exists():
            return []

        data = self.__read_file()

        if not isinstance(data, dict) or not isinstance(
            data.get("authors"), list
        ):
            raise StorageError(
                f"В файле {self.__file_path} нет списка authors"
            )

        authors: list[dict[str, Any]] = data["authors"]
        return authors

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

    def __save_data(self, authors: list[dict[str, Any]]) -> None:
        try:
            self.__file_path.parent.mkdir(parents=True, exist_ok=True)
            content = json.dumps(
                {"authors": authors}, ensure_ascii=False, indent=4
            )
            self.__file_path.write_bytes(content.encode("utf-8"))
        except (OSError, ValueError) as error:
            raise StorageError(
                f"Не удалось записать файл {self.__file_path}"
            ) from error

    def __to_author(self, data: dict[str, Any]) -> Author:
        try:
            return Author(
                author_id=UUID(data["id"]),
                name=Name(data["name"]),
                birth_date=date.fromisoformat(data["birth_date"]),
                death_date=(
                    date.fromisoformat(data["death_date"])
                    if data.get("death_date")
                    else None
                ),
            )
        except (
            KeyError,
            ValueError,
            TypeError,
            AttributeError,
            ValidationError,
        ) as error:
            raise StorageError(
                f"В файле {self.__file_path} повреждена запись автора"
            ) from error

    @staticmethod
    def __to_dict(author: Author) -> dict[str, Any]:
        return {
            "id": str(author.id),
            "name": author.name.value,
            "birth_date": author.birth_date.isoformat(),
            "death_date": (
                author.death_date.isoformat()
                if author.death_date is not None
                else None
            ),
        }

    @staticmethod
    def __find_index(
        authors: list[dict[str, Any]], author_id: UUID
    ) -> int | None:
        for index, item in enumerate(authors):
            if item.get("id") == str(author_id):
                return index

        return None

    def add(self, author: Author) -> None:
        authors = self.__load_data()

        if self.__find_index(authors, author.id) is not None:
            raise AlreadyExistsError(f"Автор {author.id} уже существует")

        authors.append(self.__to_dict(author))
        self.__save_data(authors)

    def get_by_id(self, author_id: UUID) -> Author | None:
        authors = self.__load_data()
        index = self.__find_index(authors, author_id)

        if index is None:
            return None

        return self.__to_author(authors[index])

    def get_all(self) -> list[Author]:
        return [
            self.__to_author(data)
            for data in self.__load_data()
        ]

    def find_by_name(self, name: str) -> list[Author]:
        normalized_name = name.strip().casefold()

        if not normalized_name:
            return []

        return [
            author
            for author in self.get_all()
            if normalized_name in author.name.value.casefold()
        ]

    def update(self, author: Author) -> None:
        authors = self.__load_data()
        index = self.__find_index(authors, author.id)

        if index is None:
            raise NotFoundError(f"Автор {author.id} не найден")

        authors[index] = self.__to_dict(author)
        self.__save_data(authors)

    def delete(self, author_id: UUID) -> None:
        authors = self.__load_data()
        index = self.__find_index(authors, author_id)

        if index is None:
            raise NotFoundError(f"Автор {author_id} не найден")

        del authors[index]
        self.__save_data(authors)
