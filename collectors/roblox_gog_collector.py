"""
Coletor de dados das plataformas Roblox e GOG.

Responsável: Vitor Costa
Saídas esperadas: data/raw/roblox_raw.json e data/raw/gog_raw.json

Fontes (todas públicas, sem autenticação):
- Roblox: Explore API (lista de jogos por "sort") + games.roblox.com (detalhes por universo).
- GOG: catálogo JSON paginado em catalog.gog.com.

Uso (a partir da raiz do repositório):
    python -m collectors.roblox_gog_collector
    python -m collectors.roblox_gog_collector --only gog --max-gog-pages 3
"""

from __future__ import annotations

import argparse
import uuid
from typing import Any

import requests

from collectors.utils import EthicalHTTPClient, save_raw_json, setup_logger

logger = setup_logger("roblox_gog_collector")

# --- Roblox -----------------------------------------------------------------
ROBLOX_EXPLORE_URL = "https://apis.roblox.com/explore-api/v1"
ROBLOX_DETAILS_URL = "https://games.roblox.com/v1/games"
ROBLOX_BATCH_SIZE = 50  # lotes de 100 retornam HTTP 400; 50 funcionam

# --- GOG --------------------------------------------------------------------
GOG_CATALOG_URL = "https://catalog.gog.com/v1/catalog"
GOG_PAGE_SIZE = 48

ROBLOX_FILENAME = "roblox_raw.json"
GOG_FILENAME = "gog_raw.json"


# ============================================================================
# Roblox
# ============================================================================
def _fetch_roblox_sorts(client: EthicalHTTPClient, session_id: str) -> list[dict[str, Any]]:
    """Retorna os sorts do tipo 'Games' (ex: top-trending, up-and-coming) da Explore API."""
    sorts: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        params: dict[str, Any] = {"sessionId": session_id}
        if page_token:
            params["sortsPageToken"] = page_token
        data = client.get_json(f"{ROBLOX_EXPLORE_URL}/get-sorts", params=params)
        sorts.extend(s for s in data.get("sorts", []) if s.get("contentType") == "Games")
        page_token = data.get("nextSortsPageToken")
        if not page_token:
            return sorts


def _fetch_roblox_universes(
    client: EthicalHTTPClient, max_games: int | None
) -> dict[int, dict[str, Any]]:
    """Coleta universeIds de cada sort e registra em quais sorts e posições cada jogo aparece."""
    session_id = str(uuid.uuid4())
    universes: dict[int, dict[str, Any]] = {}

    sorts = _fetch_roblox_sorts(client, session_id)
    logger.info("Roblox: %d sorts encontrados: %s", len(sorts), [s["sortId"] for s in sorts])

    for sort in sorts:
        sort_id = sort["sortId"]
        try:
            content = client.get_json(
                f"{ROBLOX_EXPLORE_URL}/get-sort-content",
                params={"sessionId": session_id, "sortId": sort_id},
            )
        except requests.RequestException as exc:
            logger.warning("Roblox: falha ao coletar sort '%s': %s", sort_id, exc)
            continue

        games = content.get("games", [])
        logger.info("Roblox: sort '%s' -> %d jogos", sort_id, len(games))

        for rank, game in enumerate(games, start=1):
            universe_id = game.get("universeId")
            if universe_id is None:
                continue
            if universe_id not in universes and max_games and len(universes) >= max_games:
                continue
            entry = universes.setdefault(universe_id, {"explore": game, "sorts": []})
            entry["sorts"].append({"sort_id": sort_id, "rank": rank})

    return universes


def collect_roblox(client: EthicalHTTPClient, max_games: int | None = None) -> list[dict[str, Any]]:
    """Coleta jogos da Roblox: detalhes do endpoint de jogos + contexto da Explore API."""
    universes = _fetch_roblox_universes(client, max_games)
    universe_ids = list(universes)
    logger.info("Roblox: %d universos únicos para detalhar", len(universe_ids))

    records: list[dict[str, Any]] = []
    for start in range(0, len(universe_ids), ROBLOX_BATCH_SIZE):
        batch = universe_ids[start : start + ROBLOX_BATCH_SIZE]
        try:
            details = client.get_json(
                ROBLOX_DETAILS_URL, params={"universeIds": ",".join(map(str, batch))}
            )
        except requests.RequestException as exc:
            logger.warning("Roblox: falha no lote %d-%d: %s", start, start + len(batch), exc)
            continue

        for item in details.get("data", []):
            context = universes.get(item.get("id"), {})
            record = dict(item)
            record["explore_sorts"] = context.get("sorts", [])
            record["explore_data"] = context.get("explore", {})
            records.append(record)

        logger.info("Roblox: %d/%d detalhados", len(records), len(universe_ids))

    return records


# ============================================================================
# GOG
# ============================================================================
def collect_gog(client: EthicalHTTPClient, max_pages: int | None = None) -> list[dict[str, Any]]:
    """Coleta o catálogo da GOG página a página até o fim (ou até max_pages)."""
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    page = 1
    total_pages: int | None = None

    while True:
        if max_pages and page > max_pages:
            break
        if total_pages is not None and page > total_pages:
            break

        try:
            data = client.get_json(
                GOG_CATALOG_URL,
                params={
                    "limit": GOG_PAGE_SIZE,
                    "page": page,
                    "order": "desc:trending",
                    "productType": "in:game,pack",
                },
            )
        except requests.RequestException as exc:
            logger.warning("GOG: falha na página %d: %s", page, exc)
            page += 1
            continue

        total_pages = data.get("pages", total_pages)
        products = data.get("products", [])
        if not products:
            break

        for product in products:
            product_id = str(product.get("id"))
            if product_id in seen_ids:
                continue
            seen_ids.add(product_id)
            records.append(product)

        logger.info("GOG: página %d/%s -> %d registros acumulados", page, total_pages, len(records))
        page += 1

    return records


# ============================================================================
# Execução
# ============================================================================
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Coletor Roblox e GOG (IMD1152).")
    parser.add_argument("--only", choices=["roblox", "gog"], help="Coleta apenas uma plataforma.")
    parser.add_argument("--max-roblox-games", type=int, default=None, help="Limite de jogos Roblox.")
    parser.add_argument("--max-gog-pages", type=int, default=None, help="Limite de páginas da GOG.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    with EthicalHTTPClient() as client:
        if args.only in (None, "roblox"):
            roblox = collect_roblox(client, max_games=args.max_roblox_games)
            path = save_raw_json(roblox, ROBLOX_FILENAME, platform="roblox")
            logger.info("Roblox: %d registros salvos em %s", len(roblox), path)

        if args.only in (None, "gog"):
            gog = collect_gog(client, max_pages=args.max_gog_pages)
            path = save_raw_json(gog, GOG_FILENAME, platform="gog")
            logger.info("GOG: %d registros salvos em %s", len(gog), path)


if __name__ == "__main__":
    main()
