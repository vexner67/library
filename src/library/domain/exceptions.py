# Базовое исключение приложения: консоль перехватывает его
# и показывает пользователю сообщение вместо трассировки.
class LibraryError(Exception):
    pass


# Данные нарушают правила предметной области.
class ValidationError(LibraryError):
    pass


# Записи с указанным id нет в хранилище.
class NotFoundError(LibraryError):
    pass


# Запись с таким id уже есть в хранилище.
class AlreadyExistsError(LibraryError):
    pass


# Файл хранилища не удалось прочитать, записать или разобрать.
class StorageError(LibraryError):
    pass
