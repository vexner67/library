from uuid import uuid7

import pytest

from domain.book.book import Book
from domain.book.publication_year import PublicationYear
from domain.book.title import Title
from domain.exceptions import ValidationError


# Книга возвращает те же данные, с которыми была создана.
def test_book_keeps_data() -> None:
    book_id = uuid7()
    author_ids = [uuid7(), uuid7()]
    book = Book(book_id, Title("Двенадцать стульев"), author_ids,
                PublicationYear(1928))

    assert book.id == book_id
    assert book.title.value == "Двенадцать стульев"
    assert book.author_ids == author_ids
    assert book.publication_year.value == 1928


# Книга без авторов не создается.
def test_book_without_authors_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Book(uuid7(), Title("Книга"), [], PublicationYear(2000))


# Список авторов копируется, поэтому его нельзя
# изменить ни через исходный список, ни через свойство.
def test_author_ids_cannot_be_changed_from_outside() -> None:
    author_ids = [uuid7()]
    book = Book(uuid7(), Title("Книга"), author_ids, PublicationYear(2000))

    author_ids.append(uuid7())
    book.author_ids.append(uuid7())

    assert len(book.author_ids) == 1
