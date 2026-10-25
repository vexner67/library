import pytest

from domain.book.title import MAX_TITLE_LENGTH, Title
from domain.exceptions import ValidationError


# Пробелы по краям названия отбрасываются.
def test_title_strips_spaces() -> None:
    assert Title("  Война и мир ").value == "Война и мир"


# Пустое название не принимается.
@pytest.mark.parametrize("value", ["", "   "])
def test_empty_title_is_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        Title(value)


# Граница: название максимальной длины еще допустимо.
def test_title_of_max_length_is_allowed() -> None:
    assert len(Title("а" * MAX_TITLE_LENGTH).value) == MAX_TITLE_LENGTH


# Граница: на один символ длиннее - уже ошибка.
def test_too_long_title_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Title("а" * (MAX_TITLE_LENGTH + 1))
