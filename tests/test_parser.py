"""Тесты разбора страницы и цены."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import ParserConfig, Selectors, load_config  # noqa: E402
from src.parser import ParseError, build_page_url, deduplicate, parse_page, parse_price  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "catalog.html"
SELECTORS = Selectors(
    card="div.product-card",
    title="h2.product-title",
    price="span.product-price",
    link="a.product-link",
    sku="span.product-sku",
    availability="span.product-stock",
)


class PriceTest(unittest.TestCase):
    def test_plain_price(self):
        self.assertEqual(parse_price("1 500 ₽"), 1500)

    def test_decimal_price_rounds(self):
        self.assertEqual(parse_price("2 349,50 руб."), 2350)

    def test_price_with_nbsp(self):
        self.assertEqual(parse_price("990\u00a0₽"), 990)

    def test_non_numeric_price_returns_none(self):
        self.assertIsNone(parse_price("по запросу"))

    def test_empty_price_returns_none(self):
        self.assertIsNone(parse_price(""))


class ParsePageTest(unittest.TestCase):
    def setUp(self):
        self.items = parse_page(FIXTURE.read_text(encoding="utf-8"), SELECTORS)

    def test_finds_all_cards(self):
        self.assertEqual(len(self.items), 5)

    def test_first_item_parsed(self):
        first = self.items[0]
        self.assertEqual(first.sku, "SKU-1001")
        self.assertEqual(first.price, 1500)
        self.assertEqual(first.url, "/product/1001")
        self.assertEqual(first.availability, "В наличии")

    def test_item_without_price(self):
        last = self.items[-1]
        self.assertEqual(last.sku, "SKU-1005")
        self.assertIsNone(last.price)

    def test_missing_card_selector_raises(self):
        broken = SELECTORS.model_copy(update={"card": "div.no-such-card"})
        with self.assertRaises(ParseError):
            parse_page(FIXTURE.read_text(encoding="utf-8"), broken)

    def test_titles_are_normalised(self):
        self.assertTrue(all("\n" not in item.title for item in self.items))


class DeduplicateTest(unittest.TestCase):
    def test_duplicates_by_sku_removed(self):
        items = parse_page(FIXTURE.read_text(encoding="utf-8"), SELECTORS)
        unique, removed = deduplicate(items)
        self.assertEqual(len(unique), 4)
        self.assertEqual(removed, 1)

    def test_order_preserved(self):
        items = parse_page(FIXTURE.read_text(encoding="utf-8"), SELECTORS)
        unique, _ = deduplicate(items)
        self.assertEqual([item.sku for item in unique], ["SKU-1001", "SKU-1002", "SKU-1003", "SKU-1005"])


class PaginationTest(unittest.TestCase):
    def test_url_built_from_template(self):
        self.assertEqual(build_page_url("https://shop.test/catalog?page={page}", 3), "https://shop.test/catalog?page=3")

    def test_config_requires_placeholder(self):
        with self.assertRaises(Exception):
            ParserConfig(
                site="https://shop.test",
                start_url="https://shop.test/catalog",
                max_pages=2,
                delay_seconds=0,
                timeout_seconds=10,
                retries=1,
                user_agent="test",
                selectors=SELECTORS,
                output={"csv": "out.csv", "xlsx": "out.xlsx"},
            )

    def test_project_config_is_valid(self):
        config = load_config(ROOT / "config" / "parser.json")
        self.assertGreaterEqual(config.max_pages, 1)
        self.assertIn("{page}", config.start_url)


if __name__ == "__main__":
    unittest.main()
