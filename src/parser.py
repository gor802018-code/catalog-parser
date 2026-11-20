"""Разбор HTML-страницы каталога в набор записей."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from src.config import Selectors


class ParseError(RuntimeError):
    """Страница не похожа на ожидаемую: нет карточек товара."""


_PRICE_CLEAN = re.compile(r"[^\d,.\-]")


def parse_price(raw: str) -> int | None:
    """«1 500 ₽» и «2 349,50 руб.» превращает в 1500 и 2350.

    Ориентируется на русскую запись: запятая — десятичный разделитель,
    точки внутри числа считаются разделителями тысяч.
    """
    cleaned = _PRICE_CLEAN.sub("", raw or "").strip(".,")
    if not cleaned:
        return None
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return int(round(float(cleaned)))
    except ValueError:
        return None


def normalize_text(raw: str) -> str:
    return " ".join(raw.split())


@dataclass
class Item:
    sku: str
    title: str
    price: int | None
    availability: str
    url: str
    extra: dict[str, str] = field(default_factory=dict)

    def as_row(self) -> dict[str, str | int | None]:
        return {
            "sku": self.sku,
            "title": self.title,
            "price": self.price,
            "availability": self.availability,
            "url": self.url,
        }


def _text_of(node, selector: str) -> str:
    found = node.select_one(selector)
    return normalize_text(found.get_text()) if found else ""


def parse_page(html: str, selectors: Selectors) -> list[Item]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(selectors.card)
    if not cards:
        raise ParseError(
            "На странице не найдено ни одной карточки по селектору "
            f"'{selectors.card}'. Проверьте разметку сайта и настройки."
        )

    items: list[Item] = []
    for card in cards:
        link = card.select_one(selectors.link)
        items.append(
            Item(
                sku=_text_of(card, selectors.sku),
                title=_text_of(card, selectors.title),
                price=parse_price(_text_of(card, selectors.price)),
                availability=_text_of(card, selectors.availability),
                url=link.get("href", "") if link else "",
            )
        )
    return items


def deduplicate(items: list[Item]) -> tuple[list[Item], int]:
    """Убирает повторы по артикулу, сохраняя порядок."""
    seen: set[str] = set()
    unique: list[Item] = []
    for item in items:
        key = item.sku or item.url or f"{item.title}|{item.price}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique, len(items) - len(unique)


def pages_range(max_pages: int) -> range:
    return range(1, max_pages + 1)


def build_page_url(template: str, page: int) -> str:
    return template.format(page=page)
