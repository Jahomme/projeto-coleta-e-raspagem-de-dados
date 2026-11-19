"""Utilitários compartilhados: cliente HTTP ético, logging e salvamento em data/raw/."""

from __future__ import annotations

import csv
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import (
    BACKOFF_FACTOR,
    DEFAULT_HEADERS,
    MAX_RETRIES,
    RATE_LIMIT_SECONDS,
    RAW_DIR,
    REQUEST_TIMEOUT,
    RETRY_STATUS_CODES,
)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Cria ou recupera um logger padronizado para console."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    return logger


def utc_now_iso() -> str:
    """Retorna o timestamp atual em UTC no formato ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


class EthicalHTTPClient:
    """Cliente HTTP baseado em requests.Session com User-Agent acadêmico, rate limit e retries."""

    def __init__(
        self,
        rate_limit_seconds: float = RATE_LIMIT_SECONDS,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        backoff_factor: float = BACKOFF_FACTOR,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.rate_limit_seconds = rate_limit_seconds
        self.timeout = timeout
        self.logger = setup_logger(self.__class__.__name__)
        self._last_request_time: float | None = None

        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        if headers:
            self.session.headers.update(headers)

        retry_strategy = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=list(RETRY_STATUS_CODES),
            allowed_methods=frozenset(["GET", "HEAD"]),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _apply_rate_limit(self) -> None:
        """Aguarda o intervalo mínimo configurado entre requisições consecutivas."""
        if self._last_request_time is None or self.rate_limit_seconds <= 0:
            return

        elapsed = time.monotonic() - self._last_request_time
        remaining = self.rate_limit_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> requests.Response:
        """Executa requisição GET aplicando rate limiting, timeout e validação de status."""
        self._apply_rate_limit()
        effective_timeout = self.timeout if timeout is None else timeout

        self.logger.debug("GET %s | params=%s", url, params)
        response = self.session.get(
            url,
            params=params,
            headers=headers,
            timeout=effective_timeout,
        )
        self._last_request_time = time.monotonic()
        response.raise_for_status()
        return response

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> Any:
        """Executa requisição GET e retorna o corpo decodificado como JSON."""
        response = self.get(url, params=params, headers=headers, timeout=timeout)
        return response.json()

    def get_text(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> str:
        """Executa requisição GET e retorna o corpo textual da resposta."""
        response = self.get(url, params=params, headers=headers, timeout=timeout)
        return response.text

    def close(self) -> None:
        """Fecha a sessão HTTP subjacente."""
        self.session.close()

    def __enter__(self) -> EthicalHTTPClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


def _enrich_raw_records(
    records: list[dict[str, Any]],
    platform: str,
) -> list[dict[str, Any]]:
    """Garante os metadados de rastreabilidade 'platform' e 'collected_at' em cada registro."""
    batch_timestamp = utc_now_iso()
    enriched: list[dict[str, Any]] = []
    for record in records:
        item = dict(record)
        item.setdefault("platform", platform)
        item.setdefault("collected_at", batch_timestamp)
        enriched.append(item)
    return enriched


def save_raw_json(
    records: list[dict[str, Any]],
    filename: str,
    platform: str,
    output_dir: Path = RAW_DIR,
) -> Path:
    """Salva lista de registros brutos em JSON UTF-8 preservando estrutura da fonte."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    enriched = _enrich_raw_records(records, platform)

    with output_path.open("w", encoding="utf-8") as file_obj:
        json.dump(enriched, file_obj, ensure_ascii=False, indent=2)

    return output_path


def save_raw_csv(
    records: list[dict[str, Any]],
    filename: str,
    platform: str,
    output_dir: Path = RAW_DIR,
) -> Path:
    """Salva lista de registros brutos em CSV UTF-8 preservando todas as chaves encontradas."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    enriched = _enrich_raw_records(records, platform)

    if not enriched:
        output_path.write_text("", encoding="utf-8")
        return output_path

    # Preserva a ordem de aparição das colunas entre todos os registros do lote
    fieldnames: list[str] = list(dict.fromkeys(key for row in enriched for key in row.keys()))

    with output_path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched)

    return output_path
