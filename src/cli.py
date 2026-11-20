"""Запуск парсера: сбор страниц, разбор, выгрузка в CSV и XLSX."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.config import ConfigError, load_config
from src.fetcher import FetchError, Fetcher
from src.parser import Item, ParseError, build_page_url, deduplicate, parse_page, pages_range
from src.storage import StorageError, save_csv, save_xlsx

LOGGER = logging.getLogger("parser")
ROOT = Path(__file__).resolve().parents[1]


def collect(config, fetcher: Fetcher) -> list[Item]:
    items: list[Item] = []
    for page in pages_range(config.max_pages):
        url = build_page_url(config.start_url, page)
        LOGGER.info("Страница %s: %s", page, url)
        html = fetcher.get(url)
        try:
            page_items = parse_page(html, config.selectors)
        except ParseError:
            LOGGER.warning("Страница %s: карточек не найдено, останавливаюсь", page)
            break
        LOGGER.info("Страница %s: найдено %s карточек", page, len(page_items))
        items.extend(page_items)
        fetcher.wait()
    return items


def parse_local(path: Path, config) -> list[Item]:
    html = path.read_text(encoding="utf-8")
    return parse_page(html, config.selectors)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Парсер каталога: сбор карточек и выгрузка в Excel")
    parser.add_argument("--config", default=str(ROOT / "config" / "parser.json"))
    parser.add_argument("--source", help="локальный HTML-файл вместо запросов к сайту")
    parser.add_argument("--pages", type=int, help="сколько страниц обойти (переопределяет настройки)")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as error:
        LOGGER.error("%s", error)
        return 1

    if args.pages:
        config.max_pages = args.pages

    try:
        if args.source:
            LOGGER.info("Источник: локальный файл %s", args.source)
            items = parse_local(Path(args.source), config)
        else:
            fetcher = Fetcher(
                user_agent=config.user_agent,
                timeout_seconds=config.timeout_seconds,
                retries=config.retries,
                delay_seconds=config.delay_seconds,
            )
            items = collect(config, fetcher)
    except (FetchError, ParseError) as error:
        LOGGER.error("%s", error)
        return 1

    if not items:
        LOGGER.error("Ничего не собрано, выгрузка не создана")
        return 1

    unique, duplicates = deduplicate(items)
    if duplicates:
        LOGGER.info("Удалено повторов по артикулу: %s", duplicates)

    try:
        csv_path = save_csv(unique, ROOT / config.output.csv)
        xlsx_path = save_xlsx(unique, ROOT / config.output.xlsx)
    except StorageError as error:
        LOGGER.error("%s", error)
        return 1

    LOGGER.info("Готово: %s записей", len(unique))
    LOGGER.info("CSV: %s", csv_path)
    LOGGER.info("XLSX: %s", xlsx_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
