from domain.exceptions import ValidationError

MIN_NAME_LENGTH = 1
MAX_NAME_LENGTH = 100


# Объект-значение: имя автора проверяется один раз при создании,
# поэтому дальше в коде можно не повторять проверки.
class Name:
    def __init__(self, value: str) -> None:
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
