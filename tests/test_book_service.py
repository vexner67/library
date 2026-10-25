from datetime import date
from uuid import uuid7

import pytest

from application.book_service import BookService
from domain.book.publication_year import PublicationYear
from domain.book.title import Title
from domain.exceptions import NotFoundError, ValidationError
from helpers import (
    InMemoryAuthorRepository,
    InMemoryBookRepository,
    make_author,
    make_book,
)


# Вместе с книгой сохраняются ее новые авторы.
def test_add_book_saves_book_and_new_authors(
    book_service: BookService,
    author_repository: InMemoryAuthorRepository,
    book_repository: InMemoryBookRepository,
) -> None:
    ilf = make_author("Илья Ильф", date(1897, 10, 15))
    petrov = make_author("Евгений Петров", date(1902, 12, 13))

    book = book_service.add_book(
        Title("Двенадцать стульев"), PublicationYear(1928), [ilf, petrov]
    )

    assert book_repository.books == {book.id: book}
    assert book.author_ids == [ilf.id, petrov.id]
    assert set(author_repository.authors) == {ilf.id, petrov.id}


# Если автор уже есть, берется его id, дубликат не создается.
def test_add_book_reuses_existing_author(
    book_service: BookService,
    author_repository: InMemoryAuthorRepository,
) -> None:
    existing = make_author("Лев Толстой")
    author_repository.add(existing)

    book = book_service.add_book(
        Title("Анна Каренина"),
        PublicationYear(1878),
        [make_author("лев толстой")],
    )

    assert book.author_ids == [existing.id]
    assert list(author_repository.authors) == [existing.id]


# Автор, указанный дважды, - ошибка, и в хранилище
# ничего не попадает, даже первый автор из списка.
def test_duplicate_authors_are_rejected_before_saving(
    book_service: BookService,
    author_repository: InMemoryAuthorRepository,
    book_repository: InMemoryBookRepository,
) -> None:
    authors = [
        make_author("Антон Чехов", date(1860, 1, 29)),
        make_author("Лев Толстой"),
        make_author("ЛЕВ ТОЛСТОЙ"),
    ]

    with pytest.raises(ValidationError, match="указан дважды"):
        book_service.add_book(Title("Сборник"), PublicationYear(1900), authors)

    assert author_repository.authors == {}
    assert book_repository.books == {}


# Поиск несуществующей книги дает NotFoundError.
def test_get_missing_book_raises(book_service: BookService) -> None:
    with pytest.raises(NotFoundError):
        book_service.get_book(uuid7())


# Список всех книг и поиск по части названия.
def test_get_all_and_find_books(
    book_service: BookService,
    book_repository: InMemoryBookRepository,
) -> None:
    author_id = uuid7()
    war = make_book([author_id], "Война и мир")
    anna = make_book([author_id], "Анна Каренина", 1878)
    book_repository.add(war)
    book_repository.add(anna)

    assert book_service.get_all_books() == [war, anna]
    assert book_service.find_books_by_title("МИР") == [war]


# Если автора книги нет в хранилище, он пропускается.
def test_get_book_authors_skips_missing(
    book_service: BookService,
    author_repository: InMemoryAuthorRepository,
) -> None:
    author = make_author()
    author_repository.add(author)
    book = make_book([author.id, uuid7()])

    assert book_service.get_book_authors(book) == [author]


# Изменение книги меняет название и год, но не id и авторов.
def test_update_book_keeps_id_and_authors(
    book_service: BookService,
    book_repository: InMemoryBookRepository,
) -> None:
    book = make_book([uuid7()])
    book_repository.add(book)

    updated = book_service.update_book(
        book.id, Title("Война и мир. Том 1"), PublicationYear(1867)
    )

    assert updated.id == book.id
    assert updated.author_ids == book.author_ids
    assert book_repository.books[book.id].title.value == "Война и мир. Том 1"
    assert book_repository.books[book.id].publication_year.value == 1867


# Нельзя изменить книгу, которой нет.
def test_update_missing_book_raises(book_service: BookService) -> None:
    with pytest.raises(NotFoundError):
        book_service.update_book(
            uuid7(), Title("Книга"), PublicationYear(2000)
        )


# Авторов книги можно заменить, новые авторы сохраняются.
def test_update_book_authors(
    book_service: BookService,
    author_repository: InMemoryAuthorRepository,
    book_repository: InMemoryBookRepository,
) -> None:
    old_author = make_author()
    author_repository.add(old_author)
    book = make_book([old_author.id])
    book_repository.add(book)
    new_author = make_author("Антон Чехов", date(1860, 1, 29))

    updated = book_service.update_book_authors(book.id, [new_author])

    assert updated.author_ids == [new_author.id]
    assert updated.title.value == book.title.value
    assert book_repository.books[book.id].author_ids == [new_author.id]
    assert new_author.id in author_repository.authors


# Нельзя сменить авторов у книги, которой нет.
def test_update_authors_of_missing_book_raises(
    book_service: BookService,
) -> None:
    with pytest.raises(NotFoundError):
        book_service.update_book_authors(uuid7(), [make_author()])


# Книга удаляется из хранилища.
def test_delete_book(
    book_service: BookService,
    book_repository: InMemoryBookRepository,
) -> None:
    book = make_book([uuid7()])
    book_repository.add(book)

    book_service.delete_book(book.id)

    assert book_repository.books == {}


# Удаление несуществующей книги - ошибка.
def test_delete_missing_book_raises(book_service: BookService) -> None:
    with pytest.raises(NotFoundError):
        book_service.delete_book(uuid7())
