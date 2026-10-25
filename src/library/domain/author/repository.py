from typing import Protocol
from uuid import UUID

from domain.author.author import Author


# Интерфейс хранилища. Его реализуют репозитории JSON и XML,
# поэтому сервисы не зависят от формата файла.
class AuthorRepository(Protocol):
    def add(self, author: Author) -> None:
        raise NotImplementedError

    def get_by_id(self, author_id: UUID) -> Author | None:
        raise NotImplementedError

    def get_all(self) -> list[Author]:
        raise NotImplementedError

    def find_by_name(self, name: str) -> list[Author]:
        raise NotImplementedError

    def update(self, author: Author) -> None:
        raise NotImplementedError

    def delete(self, author_id: UUID) -> None:
        raise NotImplementedError
