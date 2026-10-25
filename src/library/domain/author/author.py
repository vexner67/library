from datetime import date
from uuid import UUID

from domain.author.name import Name
from domain.exceptions import ValidationError


# Автор книги. Поля закрыты и доступны только для чтения,
# изменение автора - это создание нового объекта с тем же id.
class Author:
    def __init__(
            self,
            author_id: UUID,
            name: Name,
            birth_date: date,
            death_date: date | None = None
    ) -> None:
        if birth_date > date.today():
            raise ValidationError("Дата рождения не может быть в будущем")

        if death_date is not None and death_date < birth_date:
            raise ValidationError("Дата смерти раньше даты рождения")

        self.__id = author_id
        self.__name = name
        self.__birth_date = birth_date
        self.__death_date = death_date

    @property
    def id(self) -> UUID:
        return self.__id

    @property
    def name(self) -> Name:
        return self.__name

    @property
    def birth_date(self) -> date:
        return self.__birth_date

    @property
    def death_date(self) -> date | None:
        return self.__death_date

    @property
    def life_years(self) -> str:
        if self.__death_date is None:
            return f"род. {self.__birth_date.year}"

        return f"{self.__birth_date.year}–{self.__death_date.year}"

    # Один и тот же человек: совпадают имя без учета регистра
    # и дата рождения. id при этом может быть разным.
    def is_same_person(self, other: "Author") -> bool:
        return (
            self.__name.value.casefold() == other.name.value.casefold()
            and self.__birth_date == other.birth_date
        )
