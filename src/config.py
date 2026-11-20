"""Схема настроек парсера и их проверка."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class ConfigError(RuntimeError):
    """Настройки не читаются или заполнены неверно."""


class Selectors(BaseModel):
    model_config = ConfigDict(extra="forbid")

    card: str = Field(min_length=1)
    title: str = Field(min_length=1)
    price: str = Field(min_length=1)
    link: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    availability: str = Field(min_length=1)


class Output(BaseModel):
    model_config = ConfigDict(extra="forbid")

    csv: str = Field(min_length=1)
    xlsx: str = Field(min_length=1)


class ParserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site: str = Field(min_length=1)
    start_url: str = Field(min_length=1)
    max_pages: int = Field(ge=1, le=100)
    delay_seconds: float = Field(ge=0.0, le=60.0)
    timeout_seconds: int = Field(ge=1, le=300)
    retries: int = Field(ge=0, le=10)
    user_agent: str = Field(min_length=1)
    selectors: Selectors
    output: Output

    @field_validator("start_url")
    @classmethod
    def url_must_have_page_placeholder(cls, value: str) -> str:
        if "{page}" not in value:
            msg = "start_url должен содержать {page}: по нему строится пагинация"
            raise ValueError(msg)
        return value


def load_config(path: str | Path) -> ParserConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Файл настроек не найден: {config_path}")

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(
            f"В файле {config_path.name} сломан JSON: строка {error.lineno}, колонка {error.colno}. {error.msg}"
        ) from error

    try:
        return ParserConfig.model_validate(raw)
    except ValidationError as error:
        lines = ["Настройки заполнены неверно:"]
        for issue in error.errors():
            field_path = ".".join(str(part) for part in issue["loc"]) or "корень"
            lines.append(f"  {field_path}: {issue['msg']}")
        raise ConfigError("\n".join(lines)) from error
