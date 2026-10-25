from collections.abc import Callable
from datetime import date
from pathlib import Path
from uuid import uuid7

import pytest

from domain.author.author import Author
from domain.author.name import Name
from domain.author.repository import AuthorRepository
from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    StorageError,
)
from helpers import make_author
from infrastructure.db.json.author_repository import JsonAuthorRepository
from infrastructure.db.xml.author_repository import XmlAuthorRepository

REPOSITORIES: dict[str, Callable[[Path], AuthorRepository]] = {
    "json": JsonAuthorRepository,
    "xml": XmlAuthorRepository,
}

# Содержимое испорченных файлов для каждого формата.
BROKEN_FILES = {
    "json": [
        "{",
        '{"books": []}',
        '{"authors": {}}',
        '{"authors": [{"id": "1", "name": "Автор"}]}',
        '{"authors": [{"id": "0192f0a1-5c3e-7a10-9b2d-3f4e5a6b7c81", '
        '"name": "", "birth_date": "1900-01-01"}]}',
    ],
    "xml": [
        "<authors>",
        "<books/>",
        "<authors><author><id>1</id></author></authors>",
        "<authors><author>"
        "<id>0192f0a1-5c3e-7a10-9b2d-3f4e5a6b7c81</id><name>Автор</name>"
        "<birth_date>01.01.1900</birth_date>"
        "</author></authors>",
    ],
}


def open_repository(file_format: str, file_path: Path) -> AuthorRepository:
    return REPOSITORIES[file_format](file_path)


@pytest.fixture(params=REPOSITORIES)
def file_format(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture
def file_path(file_format: str, tmp_path: Path) -> Path:
    return tmp_path / "data" / f"authors.{file_format}"


@pytest.fixture
def repository(file_format: str, file_path: Path) -> AuthorRepository:
    return open_repository(file_format, file_path)


def test_file_is_created_on_init(
    repository: AuthorRepository, file_path: Path
) -> None:
    assert file_path.exists()
    assert repository.get_all() == []


def test_existing_file_is_not_overwritten(
    file_format: str, file_path: Path, repository: AuthorRepository
) -> None:
    repository.add(make_author())

    assert len(open_repository(file_format, file_path).get_all()) == 1


def test_author_is_saved_with_all_fields(
    file_format: str, file_path: Path, repository: AuthorRepository
) -> None:
    author = make_author("Лев Толстой", date(1828, 9, 9), date(1910, 11, 20))
    repository.add(author)

    stored = open_repository(file_format, file_path).get_by_id(author.id)

    assert stored is not None
    assert stored.id == author.id
    assert stored.name.value == "Лев Толстой"
    assert stored.birth_date == date(1828, 9, 9)
    assert stored.death_date == date(1910, 11, 20)


def test_author_without_death_date_is_saved(
    repository: AuthorRepository,
) -> None:
    author = make_author(death_date=None)
    repository.add(author)

    stored = repository.get_by_id(author.id)

    assert stored is not None
    assert stored.death_date is None


def test_author_with_same_id_is_not_added_twice(
    repository: AuthorRepository,
) -> None:
    author = make_author()
    repository.add(author)

    with pytest.raises(AlreadyExistsError):
        repository.add(author)


def test_missing_author_is_none(repository: AuthorRepository) -> None:
    assert repository.get_by_id(uuid7()) is None


def test_find_by_name_ignores_case(repository: AuthorRepository) -> None:
    tolstoy = make_author("Лев Толстой")
    repository.add(tolstoy)
    repository.add(make_author("Антон Чехов", date(1860, 1, 29)))

    found = repository.find_by_name("  ТОЛСТ ")

    assert [author.id for author in found] == [tolstoy.id]


def test_find_by_empty_name_returns_nothing(
    repository: AuthorRepository,
) -> None:
    repository.add(make_author())

    assert repository.find_by_name("   ") == []


def test_update_keeps_order(repository: AuthorRepository) -> None:
    first = make_author("Лев Толстой")
    second = make_author("Антон Чехов", date(1860, 1, 29))
    repository.add(first)
    repository.add(second)

    repository.update(
        Author(first.id, Name("Л. Н. Толстой"), first.birth_date)
    )

    names = [author.name.value for author in repository.get_all()]
    assert names == ["Л. Н. Толстой", "Антон Чехов"]


def test_update_missing_author_raises(repository: AuthorRepository) -> None:
    with pytest.raises(NotFoundError):
        repository.update(make_author())


def test_delete_author(repository: AuthorRepository) -> None:
    first = make_author("Лев Толстой")
    second = make_author("Антон Чехов", date(1860, 1, 29))
    repository.add(first)
    repository.add(second)

    repository.delete(first.id)

    assert [author.id for author in repository.get_all()] == [second.id]


def test_delete_missing_author_raises(repository: AuthorRepository) -> None:
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
        open_repository(file_format, tmp_path / "data" / "authors.db")


def test_example_file_from_docs_is_readable(file_format: str) -> None:
    docs = Path(__file__).parents[1] / "docs"
    authors = open_repository(
        file_format, docs / f"authors.{file_format}"
    ).get_all()

    assert [author.name.value for author in authors][0] == "Михаил Булгаков"
