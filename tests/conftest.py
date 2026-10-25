import pytest

from application.author_service import AuthorService
from application.book_service import BookService
from helpers import InMemoryAuthorRepository, InMemoryBookRepository


@pytest.fixture
def author_repository() -> InMemoryAuthorRepository:
    return InMemoryAuthorRepository()


@pytest.fixture
def book_repository() -> InMemoryBookRepository:
    return InMemoryBookRepository()


@pytest.fixture
def author_service(
    author_repository: InMemoryAuthorRepository,
    book_repository: InMemoryBookRepository,
) -> AuthorService:
    return AuthorService(
        author_repository=author_repository,
        book_repository=book_repository,
    )


@pytest.fixture
def book_service(
    book_repository: InMemoryBookRepository,
    author_repository: InMemoryAuthorRepository,
) -> BookService:
    return BookService(
        book_repository=book_repository,
        author_repository=author_repository,
    )
