import pytest

from domain.exceptions import (
    AlreadyExistsError,
    LibraryError,
    NotFoundError,
    StorageError,
    ValidationError,
)


# Все ошибки приложения наследуются от LibraryError,
# поэтому консоль может перехватить их одним except.
@pytest.mark.parametrize(
    "error_class",
    [ValidationError, NotFoundError, AlreadyExistsError, StorageError],
)
def test_errors_inherit_library_error(error_class: type[Exception]) -> None:
    assert issubclass(error_class, LibraryError)


# LibraryError - обычное исключение, а не системное вроде KeyboardInterrupt.
def test_library_error_is_regular_exception() -> None:
    assert issubclass(LibraryError, Exception)
