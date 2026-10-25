from datetime import date
from uuid import uuid7

import pytest

from application.author_service import AuthorService
from domain.author.author import Author
from domain.author.name import Name
from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    ValidationError,
)
from helpers import (
    InMemoryAuthorRepository,
    InMemoryBookRepository,
    make_author,
    make_book,
)


# Добавленного автора можно получить по id.
def test_add_and_get_author(author_service: AuthorService) -> None:
    author = make_author()

    author_service.add_author(author)

    assert author_service.get_author(author.id) is author


# Повторное добавление того же автора - ошибка.
def test_author_with_same_id_is_not_added_twice(
    author_service: AuthorService,
) -> None:
    author = make_author()
    author_service.add_author(author)

    with pytest.raises(AlreadyExistsError):
        author_service.add_author(author)


# Поиск несуществующего id дает NotFoundError.
def test_get_missing_author_raises(author_service: AuthorService) -> None:
    with pytest.raises(NotFoundError):
        author_service.get_author(uuid7())


# Список авторов возвращается в порядке добавления.
def test_get_all_authors(author_service: AuthorService) -> None:
    first = make_author("Лев Толстой")
    second = make_author("Антон Чехов", date(1860, 1, 29))
    author_service.add_author(first)
    author_service.add_author(second)

    assert author_service.get_all_authors() == [first, second]


# Поиск работает по части имени без учета регистра.
def test_find_authors_by_part_of_name(author_service: AuthorService) -> None:
    tolstoy = make_author("Лев Толстой")
    author_service.add_author(tolstoy)
    author_service.add_author(make_author("Антон Чехов", date(1860, 1, 29)))

    assert author_service.find_authors_by_name("толст") == [tolstoy]


# Изменения автора сохраняются в хранилище.
def test_update_author(author_service: AuthorService) -> None:
    author = make_author()
    author_service.add_author(author)
    updated = Author(
        author.id, Name("Л. Н. Толстой"), author.birth_date, date(1910, 11, 20)
    )

    author_service.update_author(updated)

    stored = author_service.get_author(author.id)
    assert stored.name.value == "Л. Н. Толстой"
    assert stored.death_date == date(1910, 11, 20)


# Нельзя изменить автора, которого нет.
def test_update_missing_author_raises(author_service: AuthorService) -> None:
    with pytest.raises(NotFoundError):
        author_service.update_author(make_author())


# Автора без книг можно удалить.
def test_delete_author_without_books(
    author_service: AuthorService,
    author_repository: InMemoryAuthorRepository,
) -> None:
    author = make_author()
    author_service.add_author(author)

    author_service.delete_author(author.id)

    assert author_repository.authors == {}


# Автора с книгами удалить нельзя, и он остается в хранилище.
def test_author_with_books_is_not_deleted(
    author_service: AuthorService,
    author_repository: InMemoryAuthorRepository,
    book_repository: InMemoryBookRepository,
) -> None:
    author = make_author()
    author_service.add_author(author)
    book_repository.add(make_book([author.id]))

    with pytest.raises(ValidationError, match="Война и мир"):
        author_service.delete_author(author.id)

    assert author.id in author_repository.authors


# Удаление несуществующего автора - ошибка.
def test_delete_missing_author_raises(author_service: AuthorService) -> None:
    with pytest.raises(NotFoundError):
        author_service.delete_author(uuid7())
