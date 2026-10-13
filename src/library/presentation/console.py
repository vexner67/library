import readline  # noqa: F401
from collections.abc import Callable
from datetime import date
from typing import Protocol
from uuid import UUID, uuid7

from domain.author.author import Author
from domain.author.name import Name
from domain.book.book import Book
from domain.book.publication_year import PublicationYear
from domain.book.title import Title
from domain.exceptions import LibraryError, ValidationError


def read_line(prompt: str) -> str:
    raw = input(prompt)
    return raw.encode("utf-8", "surrogateescape").decode("utf-8", "ignore")


class AuthorServicePort(Protocol):
    def get_all_authors(self) -> list[Author]:
        raise NotImplementedError

    def update_author(self, author: Author) -> None:
        raise NotImplementedError


class BookServicePort(Protocol):
    def add_book(
        self,
        title: Title,
        publication_year: PublicationYear,
        authors: list[Author],
    ) -> Book:
        raise NotImplementedError

    def get_all_books(self) -> list[Book]:
        raise NotImplementedError

    def find_books_by_title(self, title: str) -> list[Book]:
        raise NotImplementedError

    def get_book_authors(self, book: Book) -> list[Author]:
        raise NotImplementedError

    def update_book(
        self,
        book_id: UUID,
        title: Title,
        publication_year: PublicationYear,
    ) -> Book:
        raise NotImplementedError

    def delete_book(self, book_id: UUID) -> None:
        raise NotImplementedError


class Console:
    def __init__(
        self,
        book_service: BookServicePort,
        author_service: AuthorServicePort,
    ) -> None:
        self.__book_service = book_service
        self.__author_service = author_service

    def run(self) -> None:
        menu: list[tuple[str, str, Callable[[], None]]] = [
            ("1", "Показать все книги", self.__show_books),
            ("2", "Найти книгу по названию", self.__find_books),
            ("3", "Добавить книгу", self.__add_book),
            ("4", "Изменить книгу", self.__update_book),
            ("5", "Удалить книгу", self.__delete_book),
            ("6", "Показать всех авторов", self.__show_authors),
            ("7", "Изменить автора", self.__update_author),
        ]
        actions = {key: action for key, _, action in menu}

        print("\nДобро пожаловать в библиотеку!")

        while True:
            print()

            for key, label, _ in menu:
                print(f"{key}. {label}")

            print("0. Выход")

            try:
                choice = read_line("\nВыберите действие: ").strip()

                if choice == "0":
                    print("\nДо свидания!")
                    return

                action = actions.get(choice)

                if action is None:
                    print("\nНеизвестная команда")
                    continue

                action()
            except LibraryError as error:
                print(f"\nОшибка: {error}")
            except ValueError as error:
                print(f"\nОшибка в данных: {error}")
            except (KeyboardInterrupt, EOFError):
                print("\n\nДо свидания!")
                return

    def __show_books(self) -> None:
        books = self.__book_service.get_all_books()

        if not books:
            print("\nКаталог пуст")
            return

        self.__print_books(books)

    def __pick_book(self, prompt: str) -> Book | None:
        books = self.__book_service.get_all_books()

        if not books:
            print("\nКаталог пуст")
            return None

        self.__print_books(books)
        return books[self.__choose(len(books), prompt)]

    def __pick_author(self, prompt: str) -> Author | None:
        authors = self.__author_service.get_all_authors()

        if not authors:
            print("\nАвторов пока нет")
            return None

        self.__print_authors(authors)
        return authors[self.__choose(len(authors), prompt)]

    def __find_books(self) -> None:
        title = read_line("\nВведите название или его часть: ")
        books = self.__book_service.find_books_by_title(title)

        if not books:
            print("\nКниги не найдены")
            return

        self.__print_books(books)

    def __add_book(self) -> None:
        title = Title(read_line("\nНазвание книги: "))
        year = PublicationYear(self.__read_int("Год издания: "))

        authors = [self.__read_author()]

        while self.__confirm("Добавить ещё одного автора?"):
            authors.append(self.__read_author())

        book = self.__book_service.add_book(title, year, authors)
        print(f"\nКнига «{book.title.value}» добавлена")

    def __update_book(self) -> None:
        book = self.__pick_book("Номер книги: ")

        if book is None:
            return

        print("Оставьте поле пустым, чтобы не менять его")
        raw_title = read_line(f"Название [{book.title.value}]: ").strip()
        raw_year = read_line(
            f"Год издания [{book.publication_year.value}]: "
        ).strip()

        title = Title(raw_title) if raw_title else book.title
        year = (
            PublicationYear(self.__parse_int(raw_year))
            if raw_year
            else book.publication_year
        )

        self.__book_service.update_book(book.id, title, year)
        print("\nКнига изменена")

    def __delete_book(self) -> None:
        book = self.__pick_book("Номер книги для удаления: ")

        if book is None:
            return

        if not self.__confirm(f"Удалить «{book.title.value}»?"):
            print("\nУдаление отменено")
            return

        self.__book_service.delete_book(book.id)
        print("\nКнига удалена")

    def __print_books(self, books: list[Book]) -> None:
        for index, book in enumerate(books, start=1):
            authors = self.__book_service.get_book_authors(book)
            names = ", ".join(
                f"{author.name.value} ({author.life_years})"
                for author in authors
            )
            label = "Автор" if len(authors) == 1 else "Авторы"

            print(f"\n{index}. {book.title.value} "
                  f"({book.publication_year.value})")
            print(f"   {label}: {names or 'неизвестен'}")

    def __show_authors(self) -> None:
        authors = self.__author_service.get_all_authors()

        if not authors:
            print("\nАвторов пока нет")
            return

        self.__print_authors(authors)

    def __update_author(self) -> None:
        author = self.__pick_author("Номер автора: ")

        if author is None:
            return

        print("Оставьте поле пустым, чтобы не менять его")
        raw_name = read_line(f"Имя [{author.name.value}]: ").strip()
        raw_birth = read_line(
            f"Дата рождения [{author.birth_date.isoformat()}]: "
        ).strip()
        current_death = (
            author.death_date.isoformat() if author.death_date else "нет"
        )
        raw_death = read_line(
            f"Дата смерти [{current_death}] (- чтобы убрать): "
        ).strip()

        death_date = author.death_date
        if raw_death == "-":
            death_date = None
        elif raw_death:
            death_date = self.__parse_date(raw_death)

        updated = Author(
            author_id=author.id,
            name=Name(raw_name) if raw_name else author.name,
            birth_date=(
                self.__parse_date(raw_birth)
                if raw_birth
                else author.birth_date
            ),
            death_date=death_date,
        )

        self.__author_service.update_author(updated)
        print("\nАвтор изменён")

    def __read_author(self) -> Author:
        print("\nДанные автора")
        name = Name(read_line("Имя: "))
        birth_date = self.__parse_date(
            read_line("Дата рождения (ГГГГ-ММ-ДД): ").strip()
        )
        raw_death = read_line(
            "Дата смерти (Enter, если жив или неизвестна): "
        ).strip()

        return Author(
            author_id=uuid7(),
            name=name,
            birth_date=birth_date,
            death_date=self.__parse_date(raw_death) if raw_death else None,
        )

    @staticmethod
    def __print_authors(authors: list[Author]) -> None:
        for index, author in enumerate(authors, start=1):
            print(f"\n{index}. {author.name.value} ({author.life_years})")

    @staticmethod
    def __parse_int(raw: str) -> int:
        try:
            return int(raw)
        except ValueError as error:
            raise ValidationError(f"«{raw}» — не целое число") from error

    @staticmethod
    def __parse_date(raw: str) -> date:
        try:
            return date.fromisoformat(raw)
        except ValueError as error:
            raise ValidationError(
                f"«{raw}» — неверная дата, нужен формат ГГГГ-ММ-ДД"
            ) from error

    def __read_int(self, prompt: str) -> int:
        return self.__parse_int(read_line(prompt).strip())

    def __choose(self, count: int, prompt: str) -> int:
        number = self.__read_int(f"\n{prompt}")

        if not 1 <= number <= count:
            raise ValidationError(f"Нужен номер от 1 до {count}")

        return number - 1

    @staticmethod
    def __confirm(question: str) -> bool:
        answer = read_line(f"{question} (да/нет): ").strip().casefold()
        return answer in ("да", "д", "yes", "y")
