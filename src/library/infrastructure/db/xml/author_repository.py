import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from uuid import UUID

from domain.author.author import Author
from domain.author.name import Name
from domain.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    StorageError,
    ValidationError,
)


class XmlAuthorRepository:
    def __init__(self, file_path: str | Path) -> None:
        self.__file_path = Path(file_path)

    def __load_root(self) -> ET.Element:
        if not self.__file_path.exists():
            return ET.Element("authors")

        root = self.__parse_file()

        if root.tag != "authors":
            raise StorageError(
                f"В файле {self.__file_path} корень должен быть <authors>"
            )

        return root

    def __parse_file(self) -> ET.Element:
        try:
            return ET.parse(self.__file_path).getroot()
        except ET.ParseError as error:
            raise StorageError(
                f"Файл {self.__file_path} повреждён: некорректный XML"
            ) from error
        except OSError as error:
            raise StorageError(
                f"Не удалось прочитать файл {self.__file_path}"
            ) from error

    def __save_root(self, root: ET.Element) -> None:
        try:
            self.__file_path.parent.mkdir(parents=True, exist_ok=True)
            ET.indent(root, space="    ")
            content = ET.tostring(
                root, encoding="utf-8", xml_declaration=True
            )
            self.__file_path.write_bytes(content)
        except (OSError, ValueError) as error:
            raise StorageError(
                f"Не удалось записать файл {self.__file_path}"
            ) from error

    def __to_author(self, element: ET.Element) -> Author:
        author_id = element.findtext("id")
        name = element.findtext("name")
        birth_date = element.findtext("birth_date")
        death_date = element.findtext("death_date")

        try:
            if not author_id or name is None or not birth_date:
                raise ValueError("не заполнены обязательные поля")

            return Author(
                author_id=UUID(author_id),
                name=Name(name),
                birth_date=date.fromisoformat(birth_date),
                death_date=(
                    date.fromisoformat(death_date)
                    if death_date
                    else None
                ),
            )
        except (ValueError, ValidationError) as error:
            raise StorageError(
                f"В файле {self.__file_path} повреждена запись автора"
            ) from error

    @staticmethod
    def __to_element(author: Author) -> ET.Element:
        element = ET.Element("author")

        ET.SubElement(element, "id").text = str(author.id)
        ET.SubElement(element, "name").text = author.name.value
        ET.SubElement(element, "birth_date").text = (
            author.birth_date.isoformat()
        )
        ET.SubElement(element, "death_date").text = (
            author.death_date.isoformat()
            if author.death_date is not None
            else ""
        )

        return element

    @staticmethod
    def __find_element(root: ET.Element, author_id: UUID) -> ET.Element | None:
        for element in root.findall("author"):
            if element.findtext("id") == str(author_id):
                return element

        return None

    def add(self, author: Author) -> None:
        root = self.__load_root()

        if self.__find_element(root, author.id) is not None:
            raise AlreadyExistsError(f"Автор {author.id} уже существует")

        root.append(self.__to_element(author))
        self.__save_root(root)

    def get_by_id(self, author_id: UUID) -> Author | None:
        element = self.__find_element(self.__load_root(), author_id)

        if element is None:
            return None

        return self.__to_author(element)

    def get_all(self) -> list[Author]:
        root = self.__load_root()

        return [
            self.__to_author(element)
            for element in root.findall("author")
        ]

    def find_by_name(self, name: str) -> list[Author]:
        normalized_name = name.strip().casefold()

        if not normalized_name:
            return []

        return [
            author
            for author in self.get_all()
            if normalized_name in author.name.value.casefold()
        ]

    def update(self, author: Author) -> None:
        root = self.__load_root()
        element = self.__find_element(root, author.id)

        if element is None:
            raise NotFoundError(f"Автор {author.id} не найден")

        index = list(root).index(element)
        root.remove(element)
        root.insert(index, self.__to_element(author))
        self.__save_root(root)

    def delete(self, author_id: UUID) -> None:
        root = self.__load_root()
        element = self.__find_element(root, author_id)

        if element is None:
            raise NotFoundError(f"Автор {author_id} не найден")

        root.remove(element)
        self.__save_root(root)
