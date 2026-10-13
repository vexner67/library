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
        self.__menu: list[tuple[str, str, Callable[[], None]]] = [
            ("1", "Показать все книги", self.__show_books),
            ("2", "Найти книгу по названию", self.__find_books),
            ("3", "Добавить книгу", self.__add_book),
            ("4", "Изменить книгу", self.__update_book),
            ("5", "Удалить книгу", self.__delete_book),
            ("6", "Показать всех авторов", self.__show_authors),
            ("7", "Изменить автора", self.__update_author),
        ]

    def run(self) -> None:
        print("\nДобро пожаловать в библиотеку!")

        while True:
            self.__print_menu()

            try:
                choice = read_line("\nВыберите действие: ").strip()

                if choice == "0":
                    break

                self.__run_action(choice)
            except LibraryError as error:
                print(f"\nОшибка: {error}")
            except ValueError as error:
                print(f"\nОшибка в данных: {error}")
            except (KeyboardInterrupt, EOFError):
                print()
                break

        print("\nДо свидания!")

    def __print_menu(self) -> None:
        print()

        for key, label, _ in self.__menu:
            print(f"{key}. {label}")

        print("0. Выход")

    def __run_action(self, choice: str) -> None:
        for key, _, action in self.__menu:
            if key == choice:
                action()
                return

        print("\nНеизвестная команда")

    def __show_books(self) -> None:
        books = self.__book_service.get_all_books()

        if not books:
            print("\nКаталог пуст")
            return

        self.__print_books(books)

    def __find_books(self) -> None:
        title = read_line("\nВведите название или его часть: ")
        books = self.__book_service.find_books_by_title(title)

        if not books:
            print("\nКниги не найдены")
            return

        self.__print_books(books)

    def __add_book(self) -> None:
        print()
        title = self.__ask_title()
        year = self.__ask_year()
        authors = self.__read_authors()

        book = self.__book_service.add_book(title, year, authors)
        print(f"\nКнига «{book.title.value}» добавлена")

    def __update_book(self) -> None:
        book = self.__pick_book("Номер книги: ")

        if book is None:
            return

        print("Оставьте поле пустым, чтобы не менять его")
        title = self.__ask_title(book.title)
        year = self.__ask_year(book.publication_year)

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
        updated = self.__read_author_changes(author)

        self.__author_service.update_author(updated)
        print("\nАвтор изменён")

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

    def __read_authors(self) -> list[Author]:
        authors = [self.__read_author()]

        while self.__confirm("Добавить ещё одного автора?"):
            authors.append(self.__read_author())

        return authors

    def __read_author(self) -> Author:
        print("\nДанные автора")
        author_id = uuid7()
        name = self.__ask_name()
        birth_date = self.__ask_birth_date(author_id, name)

        return self.__ask_death_date(
            "Дата смерти (Enter, если жив или неизвестна): ",
            author_id,
            name,
            birth_date,
        )

    def __read_author_changes(self, author: Author) -> Author:
        name = self.__ask_name(author.name)
        birth_date = self.__ask_birth_date(
            author.id, name, author.birth_date
        )
        death_label = (
            author.death_date.isoformat() if author.death_date else "нет"
        )

        return self.__ask_death_date(
            f"Дата смерти [{death_label}] (- чтобы убрать): ",
            author.id,
            name,
            birth_date,
            author.death_date,
        )

    def __ask_title(self, current: Title | None = None) -> Title:
        if current is None:
            return self.__ask("Название книги: ", Title)

        return self.__ask(
            f"Название [{current.value}]: ",
            lambda raw: Title(raw) if raw else current,
        )

    def __ask_year(
        self, current: PublicationYear | None = None
    ) -> PublicationYear:
        if current is None:
            return self.__ask(
                "Год издания: ",
                lambda raw: PublicationYear(self.__parse_int(raw)),
            )

        return self.__ask(
            f"Год издания [{current.value}]: ",
            lambda raw: (
                PublicationYear(self.__parse_int(raw)) if raw else current
            ),
        )

    def __ask_name(self, current: Name | None = None) -> Name:
        if current is None:
            return self.__ask("Имя: ", Name)

        return self.__ask(
            f"Имя [{current.value}]: ",
            lambda raw: Name(raw) if raw else current,
        )

    def __ask_birth_date(
        self,
        author_id: UUID,
        name: Name,
        current: date | None = None,
    ) -> date:
        def to_birth_date(raw: str) -> date:
            birth_date = (
                current
                if current is not None and not raw
                else self.__parse_date(raw)
            )
            return Author(author_id, name, birth_date).birth_date

        if current is None:
            return self.__ask("Дата рождения (ГГГГ-ММ-ДД): ", to_birth_date)

        return self.__ask(
            f"Дата рождения [{current.isoformat()}]: ", to_birth_date
        )

    def __ask_death_date(
        self,
        prompt: str,
        author_id: UUID,
        name: Name,
        birth_date: date,
        current: date | None = None,
    ) -> Author:
        def to_author(raw: str) -> Author:
            death_date = self.__parse_death_date(raw, current)
            return Author(author_id, name, birth_date, death_date)

        return self.__ask(prompt, to_author)

    def __print_books(self, books: list[Book]) -> None:
        for index, book in enumerate(books, start=1):
            authors = self.__book_service.get_book_authors(book)

            print(f"\n{index}. {book.title.value} "
                  f"({book.publication_year.value})")
            print(f"   {self.__format_authors(authors)}")

    @staticmethod
    def __format_authors(authors: list[Author]) -> str:
        label = "Автор" if len(authors) == 1 else "Авторы"
        names = ", ".join(
            f"{author.name.value} ({author.life_years})"
            for author in authors
        )

        return f"{label}: {names or 'неизвестен'}"

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

    def __parse_death_date(
        self, raw: str, current: date | None
    ) -> date | None:
        if raw == "-":
            return None

        if not raw:
            return current

        return self.__parse_date(raw)

    @staticmethod
    def __ask[T](prompt: str, parse: Callable[[str], T]) -> T:
        while True:
            raw = read_line(prompt).strip()

            try:
                return parse(raw)
            except ValidationError as error:
                print(f"Ошибка: {error}. Повторите ввод")

    def __choose(self, count: int, prompt: str) -> int:
        def to_index(raw: str) -> int:
            number = self.__parse_int(raw)

            if not 1 <= number <= count:
                raise ValidationError(f"Нужен номер от 1 до {count}")

            return number - 1

        print()
        return self.__ask(prompt, to_index)

    @staticmethod
    def __confirm(question: str) -> bool:
        answer = read_line(f"{question} (да/нет): ").strip().casefold()
        return answer in ("да", "д", "yes", "y")
