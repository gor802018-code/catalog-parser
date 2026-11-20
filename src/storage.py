"""Выгрузка собранных данных в CSV и XLSX."""

from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from src.parser import Item

COLUMNS = ("sku", "title", "price", "availability", "url")
HEADERS = {
    "sku": "Артикул",
    "title": "Наименование",
    "price": "Цена, ₽",
    "availability": "Наличие",
    "url": "Ссылка",
}
COLUMN_WIDTHS = {"sku": 18, "title": 52, "price": 12, "availability": 16, "url": 46}


class StorageError(RuntimeError):
    """Не удалось сохранить результат."""


def _prepare(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def save_csv(items: list[Item], path: str | Path) -> Path:
    target = _prepare(path)
    try:
        with target.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(COLUMNS), delimiter=";")
            writer.writerow(dict(zip(COLUMNS, (HEADERS[name] for name in COLUMNS), strict=True)))
            for item in items:
                writer.writerow(item.as_row())
    except OSError as error:
        raise StorageError(f"Не удалось записать {target}: {error}") from error
    return target


def save_xlsx(items: list[Item], path: str | Path) -> Path:
    target = _prepare(path)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Каталог"

    for column, name in enumerate(COLUMNS, start=1):
        cell = sheet.cell(row=1, column=column, value=HEADERS[name])
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        sheet.column_dimensions[get_column_letter(column)].width = COLUMN_WIDTHS[name]

    for row, item in enumerate(items, start=2):
        data = item.as_row()
        for column, name in enumerate(COLUMNS, start=1):
            sheet.cell(row=row, column=column, value=data[name])

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{max(len(items) + 1, 1)}"

    try:
        workbook.save(target)
    except OSError as error:
        raise StorageError(f"Не удалось записать {target}: {error}") from error
    return target
