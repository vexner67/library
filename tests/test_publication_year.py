from datetime import date

import pytest

from domain.book.publication_year import (
    MIN_PUBLICATION_YEAR,
    PublicationYear,
)
from domain.exceptions import ValidationError


@pytest.mark.parametrize(
    "year", [MIN_PUBLICATION_YEAR, 1869, date.today().year]
)
def test_valid_year_is_kept(year: int) -> None:
    assert PublicationYear(year).value == year


@pytest.mark.parametrize(
    "year", [MIN_PUBLICATION_YEAR - 1, date.today().year + 1, 0, -5]
)
def test_year_out_of_range_is_rejected(year: int) -> None:
    with pytest.raises(ValidationError):
        PublicationYear(year)
