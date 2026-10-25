import pytest

from domain.author.name import MAX_NAME_LENGTH, Name
from domain.exceptions import ValidationError


# Пробелы по краям имени отбрасываются.
def test_name_strips_spaces() -> None:
    assert Name("  Лев Толстой  ").value == "Лев Толстой"


# Пустое имя или имя из одних пробелов не принимается.
@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_empty_name_is_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        Name(value)


# Граница: имя ровно максимальной длины еще допустимо.
def test_name_of_max_length_is_allowed() -> None:
    assert len(Name("а" * MAX_NAME_LENGTH).value) == MAX_NAME_LENGTH


# Граница: на один символ длиннее - уже ошибка.
def test_too_long_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Name("а" * (MAX_NAME_LENGTH + 1))
