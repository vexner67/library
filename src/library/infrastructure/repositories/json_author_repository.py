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

        try:
            with self.__file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise StorageError(
                f"Файл {self.__file_path} повреждён: некорректный JSON"
            ) from error
        except OSError as error:
            raise StorageError(
                f"Не удалось прочитать файл {self.__file_path}"
            ) from error

        if not isinstance(data, dict) or not isinstance(
            data.get("authors"), list
        ):
            raise StorageError(
                f"В файле {self.__file_path} нет списка authors"
            )

        authors: list[dict[str, Any]] = data["authors"]
        return authors

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
        except (KeyError, ValueError, TypeError, ValidationError) as error:
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

    def add(self, author: Author) -> None:
        authors = self.__load_data()

        for item in authors:
            if item.get("id") == str(author.id):
                raise AlreadyExistsError(f"Автор {author.id} уже существует")

        authors.append(self.__to_dict(author))
        self.__save_data(authors)

    def get_by_id(self, author_id: UUID) -> Author | None:
        for data in self.__load_data():
            if data.get("id") == str(author_id):
                return self.__to_author(data)

        return None

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

        for index, item in enumerate(authors):
            if item.get("id") == str(author.id):
                authors[index] = self.__to_dict(author)
                self.__save_data(authors)
                return

        raise NotFoundError(f"Автор {author.id} не найден")

    def delete(self, author_id: UUID) -> None:
        authors = self.__load_data()

        for index, item in enumerate(authors):
            if item.get("id") == str(author_id):
                del authors[index]
                self.__save_data(authors)
                return

        raise NotFoundError(f"Автор {author_id} не найден")
