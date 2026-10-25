import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from infrastructure.db.json.author_repository import JsonAuthorRepository
from infrastructure.db.json.book_repository import JsonBookRepository
from infrastructure.db.xml.author_repository import XmlAuthorRepository
from infrastructure.db.xml.book_repository import XmlBookRepository

MAIN_PATH = Path(__file__).parents[1] / "src" / "library" / "__main__.py"


# Имя __main__ занято самим pytest, поэтому модуль грузится из файла.
def load_main() -> ModuleType:
    spec = importlib.util.spec_from_file_location("library_main", MAIN_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


main_module = load_main()


@pytest.fixture(autouse=True)
def work_in_tmp_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)


def answer(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> None:
    remaining = iter(answers)

    def fake_input(prompt: str = "") -> str:
        try:
            return next(remaining)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake_input)


# 1 выбирает XML, 2 - JSON.
@pytest.mark.parametrize(("choice", "expected"), [("1", "xml"), ("2", "json")])
def test_choose_storage_format(
    monkeypatch: pytest.MonkeyPatch, choice: str, expected: str
) -> None:
    answer(monkeypatch, [choice])

    assert main_module.choose_storage_format() == expected


# Неверный ответ спрашивается заново.
def test_wrong_format_is_asked_again(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answer(monkeypatch, ["3", "json", " 2 "])

    assert main_module.choose_storage_format() == "json"
    assert capsys.readouterr().out.count("Введите 1 или 2") == 2


# Для JSON создаются JSON-хранилища и их файлы.
def test_build_json_repositories(tmp_path: Path) -> None:
    authors, books = main_module.build_repositories("json")

    assert isinstance(authors, JsonAuthorRepository)
    assert isinstance(books, JsonBookRepository)
    assert (tmp_path / "data" / "authors.json").exists()
    assert (tmp_path / "data" / "books.json").exists()


# Для XML создаются XML-хранилища и их файлы.
def test_build_xml_repositories(tmp_path: Path) -> None:
    authors, books = main_module.build_repositories("xml")

    assert isinstance(authors, XmlAuthorRepository)
    assert isinstance(books, XmlBookRepository)
    assert (tmp_path / "data" / "authors.xml").exists()
    assert (tmp_path / "data" / "books.xml").exists()


# После выбора формата запускается меню.
def test_main_runs_console(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answer(monkeypatch, ["2", "1", "0"])

    main_module.main()

    output = capsys.readouterr().out
    assert "Каталог пуст" in output
    assert "До свидания!" in output


# Ctrl+D на выборе формата закрывает программу
# и не создает файлов.
def test_main_stops_on_end_of_input(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    answer(monkeypatch, [])

    main_module.main()

    assert not (tmp_path / "data").exists()


# Ошибка хранилища выводится сообщением, а не трассировкой.
def test_main_reports_storage_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    (tmp_path / "data").write_text("это файл, а не папка")
    answer(monkeypatch, ["1"])

    main_module.main()

    assert "Не удалось подготовить хранилище" in capsys.readouterr().out
