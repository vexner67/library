import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import UUID

from domain.book.book import Book
from domain.book.publication_year import PublicationYear
from domain.book.title import Title
from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    StorageError,
    ValidationError,
)


class XmlBookRepository:
    def __init__(self, path: str | Path) -> None:
        self.__path = Path(path)

        if not self.__path.exists():
            self.__write_root(ET.Element("books"))

    def __read_root(self) -> ET.Element:
        root = self.__parse_file()

        if root.tag != "books":
            raise StorageError(
                f"В файле {self.__path} корень должен быть <books>"
            )

        return root

    def __parse_file(self) -> ET.Element:
        try:
            return ET.parse(self.__path).getroot()
        except ET.ParseError as error:
            raise StorageError(
                f"Файл {self.__path} повреждён: некорректный XML"
            ) from error
        except OSError as error:
            raise StorageError(
                f"Не удалось прочитать файл {self.__path}"
            ) from error

    def __write_root(self, root: ET.Element) -> None:
        try:
            self.__path.parent.mkdir(parents=True, exist_ok=True)
            ET.indent(root, space="    ")
            content = ET.tostring(
                root, encoding="utf-8", xml_declaration=True
            )
            self.__path.write_bytes(content)
        except (OSError, ValueError) as error:
            raise StorageError(
                f"Не удалось записать файл {self.__path}"
            ) from error

    @staticmethod
    def __book_to_element(book: Book) -> ET.Element:
        element = ET.Element("book")

        ET.SubElement(element, "id").text = str(book.id)
        ET.SubElement(element, "title").text = book.title.value
        ET.SubElement(
            element,
            "publication_year",
        ).text = str(book.publication_year.value)

        author_ids_element = ET.SubElement(element, "author_ids")

        for author_id in book.author_ids:
            ET.SubElement(
                author_ids_element,
                "author_id",
            ).text = str(author_id)

        return element

    def __element_to_book(self, element: ET.Element) -> Book:
        try:
            book_id = element.findtext("id")
            title = element.findtext("title")
            year = element.findtext("publication_year")

            if not book_id or title is None or not year:
                raise ValueError("не заполнены обязательные поля")

            return Book(
                book_id=UUID(book_id),
                title=Title(title),
                publication_year=PublicationYear(int(year)),
                author_ids=self.__read_author_ids(element),
            )
        except (ValueError, ValidationError) as error:
            raise StorageError(
                f"В файле {self.__path} повреждена запись книги"
            ) from error

    @staticmethod
    def __read_author_ids(element: ET.Element) -> list[UUID]:
        author_ids: list[UUID] = []

        for item in element.findall("author_ids/author_id"):
            if item.text:
                author_ids.append(UUID(item.text))

        return author_ids

    @staticmethod
    def __find_element(root: ET.Element, book_id: UUID) -> ET.Element | None:
        for element in root.findall("book"):
            if element.findtext("id") == str(book_id):
                return element

        return None

    def add(self, book: Book) -> None:
        root = self.__read_root()

        if self.__find_element(root, book.id) is not None:
            raise AlreadyExistsError(f"Книга {book.id} уже существует")

        root.append(self.__book_to_element(book))
        self.__write_root(root)

    def get_by_id(self, book_id: UUID) -> Book | None:
        element = self.__find_element(self.__read_root(), book_id)

        if element is None:
            return None

        return self.__element_to_book(element)

    def get_all(self) -> list[Book]:
        root = self.__read_root()

        return [
            self.__element_to_book(element)
            for element in root.findall("book")
        ]

    def find_by_title(self, title: str) -> list[Book]:
        normalized_title = title.strip().casefold()

        return [
            book
            for book in self.get_all()
            if normalized_title in book.title.value.casefold()
        ]

    def update(self, book: Book) -> None:
        root = self.__read_root()
        element = self.__find_element(root, book.id)

        if element is None:
            raise NotFoundError(f"Книга {book.id} не найдена")

        index = list(root).index(element)
        root.remove(element)
        root.insert(index, self.__book_to_element(book))
        self.__write_root(root)

    def delete(self, book_id: UUID) -> None:
        root = self.__read_root()
        element = self.__find_element(root, book_id)

        if element is None:
            raise NotFoundError(f"Книга {book_id} не найдена")

        root.remove(element)
        self.__write_root(root)
