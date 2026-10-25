from datetime import date, timedelta
from uuid import uuid7

import pytest

from domain.author.author import Author
from domain.author.name import Name
from domain.exceptions import ValidationError


def test_author_keeps_data() -> None:
    author_id = uuid7()
    author = Author(
        author_id, Name("Лев Толстой"), date(1828, 9, 9), date(1910, 11, 20)
    )

    assert author.id == author_id
    assert author.name.value == "Лев Толстой"
    assert author.birth_date == date(1828, 9, 9)
    assert author.death_date == date(1910, 11, 20)


def test_death_date_is_optional() -> None:
    author = Author(uuid7(), Name("Виктор Пелевин"), date(1962, 11, 22))

    assert author.death_date is None


def test_birth_date_in_future_is_rejected() -> None:
    tomorrow = date.today() + timedelta(days=1)

    with pytest.raises(ValidationError):
        Author(uuid7(), Name("Автор"), tomorrow)


def test_death_before_birth_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Author(uuid7(), Name("Автор"), date(1900, 1, 2), date(1900, 1, 1))


def test_death_on_birth_day_is_allowed() -> None:
    author = Author(uuid7(), Name("Автор"), date(1900, 1, 1), date(1900, 1, 1))

    assert author.death_date == date(1900, 1, 1)


def test_life_years_of_living_author() -> None:
    author = Author(uuid7(), Name("Автор"), date(1962, 11, 22))

    assert author.life_years == "род. 1962"


def test_life_years_of_dead_author() -> None:
    author = Author(uuid7(), Name("Автор"), date(1828, 9, 9), date(1910, 1, 1))

    assert author.life_years == "1828–1910"


def test_same_person_ignores_id_and_name_case() -> None:
    first = Author(uuid7(), Name("Лев Толстой"), date(1828, 9, 9))
    second = Author(uuid7(), Name("лев толстой"), date(1828, 9, 9))

    assert first.is_same_person(second)


def test_different_birth_date_means_different_person() -> None:
    first = Author(uuid7(), Name("Алексей Толстой"), date(1817, 9, 5))
    second = Author(uuid7(), Name("Алексей Толстой"), date(1883, 1, 10))

    assert not first.is_same_person(second)
