from uuid import UUID

from domain.book.publication_year import PublicationYear
from domain.book.title import Title
from domain.exceptions import ValidationError


# Книга хранит только id авторов, сами авторы лежат
# в отдельном хранилище.
class Book:
    def __init__(
            self,
            book_id: UUID,
            title: Title,
            author_ids: list[UUID],
            publication_year: PublicationYear
    ) -> None:
        if not author_ids:
            raise ValidationError("У книги должен быть хотя бы один автор")

        self.__id = book_id
        self.__title = title
        self.__author_ids = list(author_ids)
        self.__publication_year = publication_year

    @property
    def id(self) -> UUID:
        return self.__id

    @property
    def title(self) -> Title:
        return self.__title

    @property
    def author_ids(self) -> list[UUID]:
        # Копия, чтобы список нельзя было изменить снаружи.
        return list(self.__author_ids)

    @property
    def publication_year(self) -> PublicationYear:
        return self.__publication_year
