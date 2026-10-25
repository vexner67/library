from collections.abc import Callable
from pathlib import Path
from uuid import uuid7

import pytest

from domain.book.book import Book
from domain.book.publication_year import PublicationYear
from domain.book.repository import BookRepository
from domain.book.title import Title
from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    StorageError,
)
from helpers import make_book
from infrastructure.db.json.author_repository import JsonAuthorRepository
from infrastructure.db.json.book_repository import JsonBookRepository
from infrastructure.db.xml.author_repository import XmlAuthorRepository
from infrastructure.db.xml.book_repository import XmlBookRepository

REPOSITORIES: dict[str, Callable[[Path], BookRepository]] = {
    "json": JsonBookRepository,
    "xml": XmlBookRepository,
}

# Содержимое испорченных файлов для каждого формата.
BROKEN_FILES = {
    "json": [
        "[1, 2",
        '{"authors": []}',
        '{"books": [{"id": "0192f0a2-1d4f-7b20-8c3e-4f5a6b7c8d91"}]}',
        '{"books": [{"id": "0192f0a2-1d4f-7b20-8c3e-4f5a6b7c8d91", '
        '"title": "Книга", "publication_year": 1000, "author_ids": '
        '["0192f0a1-5c3e-7a10-9b2d-3f4e5a6b7c81"]}]}',
        '{"books": [{"id": "0192f0a2-1d4f-7b20-8c3e-4f5a6b7c8d91", '
        '"title": "Книга", "publication_year": 2000, "author_ids": []}]}',
    ],
    "xml": [
        "<books><book>",
        "<authors/>",
        "<books><book><id>0192f0a2-1d4f-7b20-8c3e-4f5a6b7c8d91</id>"
        "<title>Книга</title><publication_year>две тысячи"
        "</publication_year></book></books>",
        "<books><book><id>0192f0a2-1d4f-7b20-8c3e-4f5a6b7c8d91</id>"
        "<title>Книга</title><publication_year>2000</publication_year>"
        "<author_ids><author_id>не uuid</author_id></author_ids>"
        "</book></books>",
    ],
}


def open_repository(file_format: str, file_path: Path) -> BookRepository:
    return REPOSITORIES[file_format](file_path)


@pytest.fixture(params=REPOSITORIES)
def file_format(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture
def file_path(file_format: str, tmp_path: Path) -> Path:
    return tmp_path / "data" / f"books.{file_format}"


@pytest.fixture
def repository(file_format: str, file_path: Path) -> BookRepository:
    return open_repository(file_format, file_path)


def test_file_is_created_on_init(
    repository: BookRepository, file_path: Path
) -> None:
    assert file_path.exists()
    assert repository.get_all() == []


def test_book_is_saved_with_all_fields(
    file_format: str, file_path: Path, repository: BookRepository
) -> None:
    author_ids = [uuid7(), uuid7()]
    book = make_book(author_ids, "Двенадцать стульев", 1928)
    repository.add(book)

    stored = open_repository(file_format, file_path).get_by_id(book.id)

    assert stored is not None
    assert stored.id == book.id
    assert stored.title.value == "Двенадцать стульев"
    assert stored.publication_year.value == 1928
    assert stored.author_ids == author_ids


def test_book_with_same_id_is_not_added_twice(
    repository: BookRepository,
) -> None:
    book = make_book([uuid7()])
    repository.add(book)

    with pytest.raises(AlreadyExistsError):
        repository.add(book)


def test_missing_book_is_none(repository: BookRepository) -> None:
    assert repository.get_by_id(uuid7()) is None


def test_find_by_title_ignores_case(repository: BookRepository) -> None:
    war = make_book([uuid7()], "Война и мир")
    repository.add(war)
    repository.add(make_book([uuid7()], "Анна Каренина", 1878))

    found = repository.find_by_title(" МИР ")

    assert [book.id for book in found] == [war.id]


def test_find_by_empty_title_returns_all(repository: BookRepository) -> None:
    repository.add(make_book([uuid7()], "Война и мир"))
    repository.add(make_book([uuid7()], "Анна Каренина", 1878))

    assert len(repository.find_by_title("")) == 2


def test_update_keeps_order(repository: BookRepository) -> None:
    first = make_book([uuid7()], "Война и мир")
    second = make_book([uuid7()], "Анна Каренина", 1878)
    repository.add(first)
    repository.add(second)

    repository.update(Book(
        first.id, Title("Война и мир. Том 1"), first.author_ids,
        PublicationYear(1867),
    ))

    titles = [book.title.value for book in repository.get_all()]
    assert titles == ["Война и мир. Том 1", "Анна Каренина"]


def test_update_missing_book_raises(repository: BookRepository) -> None:
    with pytest.raises(NotFoundError):
        repository.update(make_book([uuid7()]))


def test_delete_book(repository: BookRepository) -> None:
    first = make_book([uuid7()], "Война и мир")
    second = make_book([uuid7()], "Анна Каренина", 1878)
    repository.add(first)
    repository.add(second)

    repository.delete(first.id)

    assert [book.id for book in repository.get_all()] == [second.id]


def test_delete_missing_book_raises(repository: BookRepository) -> None:
    with pytest.raises(NotFoundError):
        repository.delete(uuid7())


def test_broken_file_raises_storage_error(
    file_format: str, file_path: Path
) -> None:
    for content in BROKEN_FILES[file_format]:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        repository = open_repository(file_format, file_path)

        with pytest.raises(StorageError):
            repository.get_all()


def test_unwritable_path_raises_storage_error(
    file_format: str, tmp_path: Path
) -> None:
    (tmp_path / "data").write_text("это файл, а не папка")

    with pytest.raises(StorageError):
        open_repository(file_format, tmp_path / "data" / "books.db")


def test_example_files_from_docs_are_consistent(file_format: str) -> None:
    docs = Path(__file__).parents[1] / "docs"
    books = open_repository(
        file_format, docs / f"books.{file_format}"
    ).get_all()
    authors = (
        JsonAuthorRepository(docs / "authors.json")
        if file_format == "json"
        else XmlAuthorRepository(docs / "authors.xml")
    )

    assert books
    for book in books:
        for author_id in book.author_ids:
            assert authors.get_by_id(author_id) is not None
