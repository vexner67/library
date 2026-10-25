from application.author_service import AuthorService
from application.book_service import BookService
from domain.exceptions import LibraryError
from presentation.console import Console
from infrastructure.db.xml.author_repository import (
    XmlAuthorRepository,
)
from infrastructure.db.xml.book_repository import (
    XmlBookRepository,
)


def build_console() -> Console:
    author_repository = XmlAuthorRepository("data/authors.xml")
    book_repository = XmlBookRepository("data/books.xml")

    author_service = AuthorService(
        author_repository=author_repository,
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
        console = build_console()
    except LibraryError as error:
        print(f"Не удалось подготовить хранилище: {error}")
        return

    console.run()


if __name__ == "__main__":
    main()
