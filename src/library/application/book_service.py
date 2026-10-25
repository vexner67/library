from uuid import UUID, uuid7

from domain.author.repository import AuthorRepository
from domain.book.repository import BookRepository
from domain.author.author import Author
from domain.book.title import Title
from domain.book.publication_year import PublicationYear
from domain.book.book import Book
from domain.exceptions import NotFoundError, ValidationError


# Сценарии работы с книгами. Новые авторы книги сохраняются
# вместе с ней, уже известные берутся из хранилища.
class BookService:
    def __init__(
        self,
        book_repository: BookRepository,
        author_repository: AuthorRepository,
    ) -> None:
        self.__book_repository = book_repository
        self.__author_repository = author_repository

    def add_book(
        self,
        title: Title,
        publication_year: PublicationYear,
        authors: list[Author],
    ) -> Book:
        author_ids = self.__save_authors(authors)
        book = Book(
            book_id=uuid7(),
            title=title,
            author_ids=author_ids,
            publication_year=publication_year,
        )
        self.__book_repository.add(book)
        return book

    def get_book(self, book_id: UUID) -> Book:
        book = self.__book_repository.get_by_id(book_id)

        if book is None:
            raise NotFoundError(f"Книга {book_id} не найдена")

        return book

    def get_all_books(self) -> list[Book]:
        return self.__book_repository.get_all()

    def find_books_by_title(self, title: str) -> list[Book]:
        return self.__book_repository.find_by_title(title)

    def get_book_authors(self, book: Book) -> list[Author]:
        authors: list[Author] = []

        for author_id in book.author_ids:
            author = self.__author_repository.get_by_id(author_id)

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

        # Объекты неизменяемые, поэтому создаем книгу заново с тем же id.
        updated = Book(
            book_id=book.id,
            title=title,
            author_ids=book.author_ids,
            publication_year=publication_year,
        )
        self.__book_repository.update(updated)
        return updated

    def update_book_authors(
        self,
        book_id: UUID,
        authors: list[Author],
    ) -> Book:
        book = self.get_book(book_id)

        # Тот же прием, что и в update_book: новая книга с тем же id.
        updated = Book(
            book_id=book.id,
            title=book.title,
            author_ids=self.__save_authors(authors),
            publication_year=book.publication_year,
        )
        self.__book_repository.update(updated)
        return updated

    def delete_book(self, book_id: UUID) -> None:
        self.__book_repository.delete(book_id)

    def __save_authors(self, authors: list[Author]) -> list[UUID]:
        # Сначала проверяем весь список, чтобы при ошибке
        # ничего не успело записаться в файл.
        self.__check_no_duplicates(authors)

        return [self.__save_author_if_new(author) for author in authors]

    @staticmethod
    def __check_no_duplicates(authors: list[Author]) -> None:
        checked: list[Author] = []

        for author in authors:
            if any(author.is_same_person(other) for other in checked):
                raise ValidationError(
                    f"Автор «{author.name.value}» указан дважды"
                )

            checked.append(author)

    # Если такой человек уже есть, используем его id, а не создаем дубликат.
    def __save_author_if_new(self, author: Author) -> UUID:
        existing = self.__find_same_person(author)

        if existing is not None:
            return existing.id

        self.__author_repository.add(author)
        return author.id

    def __find_same_person(self, author: Author) -> Author | None:
        for existing in self.__author_repository.get_all():
            if existing.is_same_person(author):
                return existing

        return None
