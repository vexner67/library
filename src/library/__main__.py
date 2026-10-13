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


def main() -> None:
    try:
        author_repository = XmlAuthorRepository("data/authors.xml")
        book_repository = XmlBookRepository("data/books.xml")
    except LibraryError as error:
        print(f"Не удалось подготовить хранилище: {error}")
        return

    author_service = AuthorService(
        author_repository=author_repository,
    )
    book_service = BookService(
        book_repo=book_repository,
        author_repo=author_repository,
    )

    console = Console(
        author_service=author_service,
        book_service=book_service,
    )
    console.run()


if __name__ == "__main__":
    main()
