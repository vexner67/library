import pytest

from domain.book.title import MAX_TITLE_LENGTH, Title
from domain.exceptions import ValidationError


def test_title_strips_spaces() -> None:
    assert Title("  Война и мир ").value == "Война и мир"


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_title_is_rejected(value: str) -> None:
    with pytest.raises(ValidationError):
        Title(value)


def test_title_of_max_length_is_allowed() -> None:
    assert len(Title("а" * MAX_TITLE_LENGTH).value) == MAX_TITLE_LENGTH


def test_too_long_title_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Title("а" * (MAX_TITLE_LENGTH + 1))
