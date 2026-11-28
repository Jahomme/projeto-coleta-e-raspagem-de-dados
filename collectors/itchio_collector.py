"""
Coletor de dados via Web Scraping HTML (BeautifulSoup) do catálogo Itch.io.

Responsável: Victor Emanuel Oliveira Silva
Saída: data/raw/itchio_raw.csv
Executar: python -m collectors.itchio_collector

Percorre páginas de listagem por gênero e tag, extrai os dados
dos cards de jogos e salva o resultado bruto em data/raw/itchio_raw.csv.

Uso ético:
- Respeita o robots.txt do itch.io (evita /search, /checkout e /download)
- Utiliza o EthicalHTTPClient com rate limiting e User-Agent acadêmico
- Coleta apenas informações públicas da listagem
"""

from __future__ import annotations

import logging
from typing import Any

from bs4 import BeautifulSoup

from collectors.utils import EthicalHTTPClient, save_raw_csv

logger = logging.getLogger(__name__)

# Local da Coleta
BASE_URL = "https://itch.io"

# Caminhos de navegação por gênero e tag (públicos e permitidos pelo robots.txt)
BROWSE_PATHS = [
    "/games/genre-action",
    "/games/genre-adventure",
    "/games/genre-rpg",
    "/games/genre-strategy",
    "/games/genre-simulation",
    "/games/genre-puzzle",
    "/games/tag-horror",
    "/games/tag-pixel-art",
    "/games/tag-platformer",
    "/games/tag-shooter",
    "/games/tag-roguelike",
    "/games/tag-jrpg",
    "/games/tag-turn-based",
    "/games/tag-action-rpg",
    "/games/tag-visual-novel",
    "/games/tag-point-and-click",
    "/games/tag-interactive-fiction",
    "/games/tag-tower-defense",
    "/games/tag-card-game",
    "/games/tag-tactics",
    "/games/tag-management",
    "/games/tag-life-simulation",
    "/games/tag-sandbox",
    "/games/tag-logic",
    "/games/tag-physics",
    "/games/tag-escape-room",
    "/games/tag-psychological-horror",
    "/games/tag-survival-horror",
]

# Limite máximo de páginas por caminho (evitar sobrecaregar o servidor)
MAX_PAGES_PER_PATH = 5


# Funções auxiliares de extração
def _parse_game_cell(cell: Any) -> dict[str, Any] | None:
    
    # Extrai os dados de um único card `.game_cell`
    # Retorna None se o card não contiver as informações mínimas (Título e URL)
    
    title_tag = cell.select_one(".title.game_link")
    if not title_tag:
        return None

    title = title_tag.get_text(strip=True)
    url = title_tag.get("href", "")

    # Gênero principal
    genre_tag = cell.select_one(".game_genre")
    genre = genre_tag.get_text(strip=True) if genre_tag else ""

    # Autor/Desenvolvedor
    author_tag = cell.select_one(".game_author a")
    author = author_tag.get_text(strip=True) if author_tag else ""
    author_url = author_tag.get("href", "") if author_tag else ""

    # Preço (Ausência de .price_value indica jogo gratuito)
    price_tag = cell.select_one(".price_tag .price_value")
    price = price_tag.get_text(strip=True) if price_tag else "Free"

    # Descrição curta
    desc_tag = cell.select_one(".game_text")
    description = desc_tag.get_text(strip=True) if desc_tag else ""

    # Rating
    rating_tag = cell.select_one(".game_rating")
    rating = rating_tag.get_text(strip=True) if rating_tag else ""

    return {
        "title": title,
        "url": url,
        "genre": genre,
        "author": author,
        "author_url": author_url,
        "price": price,
        "description": description,
        "rating": rating,
        "source_path": cell.get("data-path", ""),
    }


def _extract_games_from_page(html: str, source_path: str) -> list[dict[str, Any]]:
    # Recebe o HTML de uma página de listagem e retorna uma lista de registros
    
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict[str, Any]] = []

    for cell in soup.select(".game_cell"):
        record = _parse_game_cell(cell)
        if record:
            record["source_path"] = source_path
            records.append(record)

    return records


def _has_next_page(soup: BeautifulSoup) -> bool:
    # Verifica se a página atual possui um link para a próxima página
    return soup.select_one('link[rel="next"]') is not None


# Funções principais de coleta
def _scrape_browse_path(
    client: EthicalHTTPClient,
    path: str,
    max_pages: int = MAX_PAGES_PER_PATH,
) -> list[dict[str, Any]]:
    
    # Iterar pelas páginas de um caminho de navegação (Gênero ou Tag)
    # Retorna todos os registros coletados.
    
    all_records: list[dict[str, Any]] = []
    page = 1

    while page <= max_pages:
        url = f"{BASE_URL}{path}?page={page}"
        logger.info("Raspando: %s", url)

        try:
            html = client.get_text(url)
        except Exception as exc:
            logger.error("Falha ao acessar %s: %s", url, exc)
            break

        soup = BeautifulSoup(html, "html.parser")
        records = _extract_games_from_page(html, path)
        all_records.extend(records)

        logger.info(
            "Página %d: %d jogos extraídos (total acumulado: %d)",
            page,
            len(records),
            len(all_records),
        )

        # Interrompe se não houver mais páginas ou se nenhum jogo foi encontrado
        if not _has_next_page(soup) or not records:
            break

        page += 1

    return all_records


def main() -> None:
    # Executar a raspagem e salvar o CSV bruto
    logger.info("Iniciando coleta do itch.io...")

    # Instancia o cliente HTTP ético (rate limit e retries já configurados)
    with EthicalHTTPClient() as client:
        all_games: list[dict[str, Any]] = []

        for path in BROWSE_PATHS:
            logger.info("Coletando caminho: %s", path)
            records = _scrape_browse_path(client, path)
            all_games.extend(records)

    if not all_games:
        logger.warning("Nenhum registro coletado. Verifique os seletores ou a conectividade.")
        return

    # Salvar os dados brutos em CSV utilizando a função utilitária do projeto
    output_path = save_raw_csv(
        records=all_games,
        filename="itchio_raw.csv",
        platform="itchio",
    )

    logger.info(
        "Coleta finalizada: %d jogos salvos em %s",
        len(all_games),
        output_path,
    )


if __name__ == "__main__":
    main()