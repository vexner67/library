from datetime import date

from domain.exceptions import ValidationError

MIN_PUBLICATION_YEAR = 1450


class PublicationYear:
    def __init__(self, year: int) -> None:
        current_year = date.today().year

        if not MIN_PUBLICATION_YEAR <= year <= current_year:
            raise ValidationError(
                f"Год издания должен быть от {MIN_PUBLICATION_YEAR} "
                f"до {current_year}"
            )

        self.__value = year

    @property
    def value(self) -> int:
        return self.__value
