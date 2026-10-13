from uuid import UUID, uuid7

from application.services.ports import AuthorRepository, BookRepository
from domain.author.author import Author
from domain.book.book import Book
from domain.book.publication_year import PublicationYear
from domain.book.title import Title
from domain.exceptions import NotFoundError, ValidationError


class BookService:
    def __init__(
        self,
        book_repo: BookRepository,
        author_repo: AuthorRepository,
    ) -> None:
        self.__book_repo = book_repo
        self.__author_repo = author_repo

    def add_book(
        self,
        title: Title,
        publication_year: PublicationYear,
        authors: list[Author],
    ) -> Book:
        author_ids: list[UUID] = []

        for author in authors:
            author_id = self.__save_author_if_new(author)

            if author_id in author_ids:
                raise ValidationError(
                    f"Автор «{author.name.value}» указан дважды"
                )

            author_ids.append(author_id)

        book = Book(
            book_id=uuid7(),
            title=title,
            author_ids=author_ids,
            publication_year=publication_year,
        )
        self.__book_repo.add(book)
        return book

    def get_book(self, book_id: UUID) -> Book:
        book = self.__book_repo.get_by_id(book_id)

        if book is None:
            raise NotFoundError(f"Книга {book_id} не найдена")

        return book

    def get_all_books(self) -> list[Book]:
        return self.__book_repo.get_all()

    def find_books_by_title(self, title: str) -> list[Book]:
        return self.__book_repo.find_by_title(title)

    def get_book_authors(self, book: Book) -> list[Author]:
        authors: list[Author] = []

        for author_id in book.author_ids:
            author = self.__author_repo.get_by_id(author_id)

            if author is not None:
                authors.append(author)

        return authors

    def update_book(
        self,
        book_id: UUID,
        title: Title,
        publication_year: PublicationYear,
    ) -> Book:
        book = self.get_book(book_id)

        updated = Book(
            book_id=book.id,
            title=title,
            author_ids=book.author_ids,
            publication_year=publication_year,
        )
        self.__book_repo.update(updated)
        return updated

    def delete_book(self, book_id: UUID) -> None:
        self.get_book(book_id)
        self.__book_repo.delete(book_id)

    def __save_author_if_new(self, author: Author) -> UUID:
        for existing in self.__author_repo.get_all():
            if existing.is_same_person(author):
                return existing.id

        self.__author_repo.add(author)
        return author.id
