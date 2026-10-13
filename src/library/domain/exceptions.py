class LibraryError(Exception):
    pass


class ValidationError(LibraryError):
    pass


class NotFoundError(LibraryError):
    pass


class AlreadyExistsError(LibraryError):
    pass


class StorageError(LibraryError):
    pass
