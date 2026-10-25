from application.author_service import AuthorService
from application.book_service import BookService
from domain.author.repository import AuthorRepository
from domain.book.repository import BookRepository
from domain.exceptions import LibraryError
from presentation.console import Console, read_line
from infrastructure.db.json.author_repository import (
    JsonAuthorRepository,
)
from infrastructure.db.json.book_repository import (
    JsonBookRepository,
)
from infrastructure.db.xml.author_repository import (
    XmlAuthorRepository,
)
from infrastructure.db.xml.book_repository import (
    XmlBookRepository,
)

STORAGE_FORMATS = {"1": "xml", "2": "json"}


def choose_storage_format() -> str:
    while True:
        choice = read_line(
            "Формат хранения данных (1 - XML, 2 - JSON): "
        ).strip()

        if choice in STORAGE_FORMATS:
            return STORAGE_FORMATS[choice]

        print("Введите 1 или 2")


def build_repositories(
    storage_format: str,
) -> tuple[AuthorRepository, BookRepository]:
    if storage_format == "json":
        return (
            JsonAuthorRepository("data/authors.json"),
            JsonBookRepository("data/books.json"),
        )

    return (
        XmlAuthorRepository("data/authors.xml"),
        XmlBookRepository("data/books.xml"),
    )


def build_console(storage_format: str) -> Console:
    author_repository, book_repository = build_repositories(storage_format)

    author_service = AuthorService(
        author_repository=author_repository,
        book_repository=book_repository,
    )
    book_service = BookService(
        book_repository=book_repository,
        author_repository=author_repository,
    )

    return Console(
        author_service=author_service,
        book_service=book_service,
    )


def main() -> None:
    try:
        storage_format = choose_storage_format()
    except (KeyboardInterrupt, EOFError):
        print()
        return

    try:
        console = build_console(storage_format)
    except LibraryError as error:
        print(f"Не удалось подготовить хранилище: {error}")
        return

    console.run()


if __name__ == "__main__":
    main()
