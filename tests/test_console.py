from collections.abc import Callable
from datetime import date

import pytest

from application.author_service import AuthorService
from application.book_service import BookService
from helpers import (
    InMemoryAuthorRepository,
    InMemoryBookRepository,
    make_author,
    make_book,
)
from presentation.console import Console, read_line

RunConsole = Callable[[list[str]], str]


# Подставляет ответы пользователя вместо input() и возвращает вывод.
# Когда ответы заканчиваются, input() бросает EOFError, как при Ctrl+D.
@pytest.fixture
def run_console(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    book_service: BookService,
    author_service: AuthorService,
) -> RunConsole:
    def run(answers: list[str]) -> str:
        remaining = iter(answers)

        def fake_input(prompt: str = "") -> str:
            print(prompt, end="")
            try:
                return next(remaining)
            except StopIteration:
                raise EOFError from None

        monkeypatch.setattr("builtins.input", fake_input)
        Console(book_service, author_service).run()
        assert next(remaining, None) is None, "не все ответы использованы"
        return capsys.readouterr().out

    return run


def test_exit(run_console: RunConsole) -> None:
    output = run_console(["0"])

    assert "Добро пожаловать" in output
    assert "До свидания!" in output


def test_end_of_input_closes_program(run_console: RunConsole) -> None:
    assert "До свидания!" in run_console([])


def test_unknown_command(run_console: RunConsole) -> None:
    assert "Неизвестная команда" in run_console(["42", "0"])


def test_empty_catalog(run_console: RunConsole) -> None:
    output = run_console(["1", "4", "7", "0"])

    assert output.count("Каталог пуст") == 2
    assert "Авторов пока нет" in output


def test_show_books_with_authors(
    run_console: RunConsole,
    author_repository: InMemoryAuthorRepository,
    book_repository: InMemoryBookRepository,
) -> None:
    ilf = make_author("Илья Ильф", date(1897, 10, 15), date(1937, 4, 13))
    petrov = make_author("Евгений Петров", date(1902, 12, 13))
    author_repository.add(ilf)
    author_repository.add(petrov)
    book_repository.add(make_book([ilf.id, petrov.id], "12 стульев", 1928))

    output = run_console(["1", "0"])

    assert "1. 12 стульев (1928)" in output
    assert "Авторы: Илья Ильф (1897–1937), Евгений Петров (род. 1902)" \
        in output


def test_find_books(
    run_console: RunConsole,
    author_repository: InMemoryAuthorRepository,
    book_repository: InMemoryBookRepository,
) -> None:
    author = make_author()
    author_repository.add(author)
    book_repository.add(make_book([author.id], "Война и мир"))

    output = run_console(["2", "война", "2", "Идиот", "0"])

    assert "Война и мир (1869)" in output
    assert "Книги не найдены" in output


def test_add_book(
    run_console: RunConsole,
    author_repository: InMemoryAuthorRepository,
    book_repository: InMemoryBookRepository,
) -> None:
    output = run_console([
        "3", "Двенадцать стульев", "1928",
        "Илья Ильф", "1897-10-15", "1937-04-13", "да",
        "Евгений Петров", "1902-12-13", "", "нет",
        "0",
    ])

    assert "Книга «Двенадцать стульев» добавлена" in output
    [book] = book_repository.get_all()
    assert book.publication_year.value == 1928
    names = [author.name.value for author in author_repository.get_all()]
    assert names == ["Илья Ильф", "Евгений Петров"]
    assert author_repository.get_all()[1].death_date is None


def test_invalid_answers_are_asked_again(
    run_console: RunConsole,
    book_repository: InMemoryBookRepository,
) -> None:
    output = run_console([
        "3", "   ", "Книга", "год", "1000", "2000",
        "", "Автор", "15.01.1990", "3000-01-01", "1990-01-15",
        "1980-01-01", "", "нет",
        "0",
    ])

    assert "Название книги не может быть пустым" in output
    assert "«год» — не целое число" in output
    assert "Год издания должен быть" in output
    assert "Имя автора не может быть пустым" in output
    assert "неверная дата" in output
    assert "Дата рождения не может быть в будущем" in output
    assert "Дата смерти должна быть позже даты рождения" in output
    assert len(book_repository.get_all()) == 1


def test_duplicate_author_is_reported(
    run_console: RunConsole,
    book_repository: InMemoryBookRepository,
) -> None:
    output = run_console([
        "3", "Книга", "2000",
        "Автор", "1990-01-01", "", "да",
        "автор", "1990-01-01", "", "нет",
        "0",
    ])

    assert "Ошибка: Автор «автор» указан дважды" in output
    assert book_repository.get_all() == []


def test_update_book_keeps_empty_fields(
    run_console: RunConsole,
    book_repository: InMemoryBookRepository,
) -> None:
    book = make_book([make_author().id], "Война и мир", 1869)
    book_repository.add(book)

    run_console(["4", "5", "1", "", "1867", "0"])

    [stored] = book_repository.get_all()
    assert stored.title.value == "Война и мир"
    assert stored.publication_year.value == 1867


def test_update_book_authors(
    run_console: RunConsole,
    author_repository: InMemoryAuthorRepository,
    book_repository: InMemoryBookRepository,
) -> None:
    old_author = make_author()
    author_repository.add(old_author)
    book_repository.add(make_book([old_author.id]))

    output = run_console([
        "5", "1", "Антон Чехов", "1860-01-29", "1904-07-15", "нет", "0",
    ])

    assert "Авторы книги изменены" in output
    [book] = book_repository.get_all()
    [author] = [author_repository.authors[i] for i in book.author_ids]
    assert author.name.value == "Антон Чехов"


def test_delete_book_asks_confirmation(
    run_console: RunConsole,
    book_repository: InMemoryBookRepository,
) -> None:
    book_repository.add(make_book([make_author().id]))

    output = run_console(["6", "1", "нет", "6", "1", "да", "0"])

    assert "Удаление отменено" in output
    assert "Книга удалена" in output
    assert book_repository.get_all() == []


def test_update_author_removes_death_date(
    run_console: RunConsole,
    author_repository: InMemoryAuthorRepository,
) -> None:
    author = make_author("Лев Толстой", date(1828, 9, 9), date(1910, 11, 20))
    author_repository.add(author)

    output = run_console(["8", "1", "Л. Н. Толстой", "", "-", "0"])

    assert "Автор изменён" in output
    stored = author_repository.authors[author.id]
    assert stored.name.value == "Л. Н. Толстой"
    assert stored.birth_date == date(1828, 9, 9)
    assert stored.death_date is None


def test_author_with_books_is_not_deleted(
    run_console: RunConsole,
    author_repository: InMemoryAuthorRepository,
    book_repository: InMemoryBookRepository,
) -> None:
    author = make_author()
    author_repository.add(author)
    book_repository.add(make_book([author.id], "Война и мир"))

    output = run_console(["9", "1", "да", "0"])

    assert "Нельзя удалить автора «Лев Толстой»" in output
    assert author.id in author_repository.authors


def test_delete_author(
    run_console: RunConsole,
    author_repository: InMemoryAuthorRepository,
) -> None:
    author_repository.add(make_author())

    output = run_console(["9", "1", "да", "0"])

    assert "Автор удалён" in output
    assert author_repository.authors == {}


def test_read_line_drops_broken_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Половина буквы «я» приходит как суррогат и отбрасывается.
    monkeypatch.setattr("builtins.input", lambda prompt: "Толстой\udcd1")

    assert read_line("") == "Толстой"
