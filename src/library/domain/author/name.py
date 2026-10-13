from domain.exceptions import ValidationError

MIN_NAME_LENGTH = 1
MAX_NAME_LENGTH = 100


class Name:
    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValidationError("Имя должно быть строкой")

        normalized = value.strip()

        if len(normalized) < MIN_NAME_LENGTH:
            raise ValidationError("Имя автора не может быть пустым")

        if len(normalized) > MAX_NAME_LENGTH:
            raise ValidationError(
                f"Имя автора не длиннее {MAX_NAME_LENGTH} символов"
            )

        self.__value = normalized

    @property
    def value(self) -> str:
        return self.__value
