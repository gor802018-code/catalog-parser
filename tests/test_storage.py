"""Тесты выгрузки в CSV и XLSX."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from openpyxl import load_workbook  # noqa: E402

from src.parser import Item  # noqa: E402
from src.storage import COLUMNS, HEADERS, save_csv, save_xlsx  # noqa: E402

ITEMS = [
    Item(sku="SKU-1", title="Кабель", price=1500, availability="В наличии", url="/p/1"),
    Item(sku="SKU-2", title="Адаптер", price=None, availability="Под заказ", url="/p/2"),
]


class SaveCsvTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "nested" / "catalog.csv"

    def test_file_created_with_headers(self):
        saved = save_csv(ITEMS, self.path)
        self.assertTrue(saved.exists())
        with saved.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle, delimiter=";"))
        self.assertEqual(rows[0], [HEADERS[name] for name in COLUMNS])
        self.assertEqual(len(rows), 3)

    def test_empty_price_kept_as_empty_cell(self):
        saved = save_csv(ITEMS, self.path)
        with saved.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle, delimiter=";"))
        self.assertEqual(rows[2][2], "")


class SaveXlsxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "catalog.xlsx"

    def test_workbook_has_header_and_rows(self):
        saved = save_xlsx(ITEMS, self.path)
        workbook = load_workbook(saved)
        sheet = workbook.active
        self.assertEqual(sheet.max_row, 3)
        self.assertEqual(sheet.cell(row=1, column=1).value, HEADERS["sku"])
        self.assertEqual(sheet.cell(row=2, column=3).value, 1500)

    def test_filter_and_freeze_panes(self):
        saved = save_xlsx(ITEMS, self.path)
        sheet = load_workbook(saved).active
        self.assertEqual(sheet.freeze_panes, "A2")
        self.assertIsNotNone(sheet.auto_filter.ref)


if __name__ == "__main__":
    unittest.main()
