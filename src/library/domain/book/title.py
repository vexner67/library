from domain.exceptions import ValidationError

MIN_TITLE_LENGTH = 1
MAX_TITLE_LENGTH = 200


class Title:
    def __init__(self, value: str) -> None:
        normalized = value.strip()

        if len(normalized) < MIN_TITLE_LENGTH:
            raise ValidationError("Название книги не может быть пустым")

        if len(normalized) > MAX_TITLE_LENGTH:
            raise ValidationError(
                f"Название книги не длиннее {MAX_TITLE_LENGTH} символов"
            )

        self.__value = normalized

    @property
    def value(self) -> str:
        return self.__value
