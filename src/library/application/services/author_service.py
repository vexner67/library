from uuid import UUID

from application.services.ports import AuthorRepository
from domain.author.author import Author
from domain.exceptions import AlreadyExistsError, NotFoundError


class AuthorService:
    def __init__(
        self,
        author_repository: AuthorRepository,
    ) -> None:
        self.__author_repository = author_repository

    def add_author(self, author: Author) -> None:
        if self.__author_repository.get_by_id(author.id) is not None:
            raise AlreadyExistsError(f"Автор {author.id} уже существует")

        self.__author_repository.add(author)

    def get_author(self, author_id: UUID) -> Author:
        author = self.__author_repository.get_by_id(author_id)

        if author is None:
            raise NotFoundError(f"Автор {author_id} не найден")

        return author

    def get_all_authors(self) -> list[Author]:
        return self.__author_repository.get_all()

    def find_authors_by_name(self, name: str) -> list[Author]:
        return self.__author_repository.find_by_name(name)

    def update_author(self, author: Author) -> None:
        self.get_author(author.id)
        self.__author_repository.update(author)

    def delete_author(self, author_id: UUID) -> None:
        self.get_author(author_id)
        self.__author_repository.delete(author_id)
