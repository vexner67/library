import pytest

from domain.exceptions import (
    AlreadyExistsError,
    LibraryError,
    NotFoundError,
    StorageError,
    ValidationError,
)


@pytest.mark.parametrize(
    "error_class",
    [ValidationError, NotFoundError, AlreadyExistsError, StorageError],
)
def test_errors_inherit_library_error(error_class: type[Exception]) -> None:
    assert issubclass(error_class, LibraryError)


def test_library_error_is_regular_exception() -> None:
    assert issubclass(LibraryError, Exception)
