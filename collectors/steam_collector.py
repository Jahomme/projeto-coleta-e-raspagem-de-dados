"""
Coletor de dados da plataforma Steam / SteamSpy.

Fontes combinadas (APIs REST públicas):
1. SteamSpy API (https://steamspy.com/api.php):
   - Rankings de engajamento (`top100in2weeks`, `top100forever`, `all`)
   - Detalhes por jogo (`appdetails`): gêneros (`genre`), subgêneros/tags votadas pela
     comunidade (`tags`), estimativa de donos (`owners`), jogadores simultâneos (`ccu`),
     tempo médio/mediano de jogo (`average_2weeks`, `average_forever`) e avaliações.
2. Steam Web API pública (https://api.steampowered.com):
   - `ISteamUserStats/GetNumberOfCurrentPlayers/v1/`: snapshot em tempo real de
     jogadores online no momento da coleta (`live_player_count`).
"""

from __future__ import annotations

import argparse
from typing import Any

import requests

from collectors.utils import EthicalHTTPClient, save_raw_json, setup_logger
from config.settings import RATE_LIMIT_SECONDS

STEAMSPY_API_URL = "https://steamspy.com/api.php"
STEAM_CURRENT_PLAYERS_URL = (
    "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
)

DEFAULT_MODES = ("top100in2weeks", "top100forever")
DEFAULT_LIMIT = 100
SAMPLE_LIMIT = 10
OUTPUT_FILENAME = "steam_raw.json"

logger = setup_logger("steam_collector")


def fetch_steamspy_ranking(
    client: EthicalHTTPClient,
    mode: str,
    page: int = 0,
) -> dict[str, dict[str, Any]]:
    """
    Busca um lote de jogos do SteamSpy de acordo com o modo especificado.

    Modos suportados pela API do SteamSpy:
    - 'top100in2weeks': Top 100 jogos por jogadores nas últimas 2 semanas (tendência/ascensão)
    - 'top100forever': Top 100 jogos mais jogados desde o lançamento
    - 'top100owned': Top 100 jogos por número de donos
    - 'all': Catálogo geral paginado (1000 jogos por página; limite de 1 req/60s no SteamSpy)
    """
    params: dict[str, Any] = {"request": mode}
    if mode == "all":
        params["page"] = page

    logger.info("Consultando ranking SteamSpy (request=%s)...", mode)
    data = client.get_json(STEAMSPY_API_URL, params=params)

    if not isinstance(data, dict):
        logger.warning("Resposta inesperada do SteamSpy para request=%s", mode)
        return {}

    return data


def fetch_steamspy_appdetails(
    client: EthicalHTTPClient,
    appid: int | str,
) -> dict[str, Any]:
    """
    Busca detalhes completos de um jogo no SteamSpy (inclui 'genre' e dicionário 'tags').
    """
    params = {"request": "appdetails", "appid": str(appid)}
    data = client.get_json(STEAMSPY_API_URL, params=params)
    return data if isinstance(data, dict) else {}


def fetch_steam_live_players(
    client: EthicalHTTPClient,
    appid: int | str,
) -> int | None:
    """
    Consulta a API oficial pública da Steam para obter a contagem de jogadores online
    no exato momento da coleta (ISteamUserStats/GetNumberOfCurrentPlayers/v1).
    """
    try:
        data = client.get_json(STEAM_CURRENT_PLAYERS_URL, params={"appid": str(appid)})
        response_block = data.get("response", {}) if isinstance(data, dict) else {}
        if response_block.get("result") == 1:
            player_count = response_block.get("player_count")
            return int(player_count) if player_count is not None else None
    except requests.RequestException as exc:
        logger.debug("Não foi possível obter live_player_count para appid=%s: %s", appid, exc)
    except (ValueError, TypeError):
        pass
    return None


def collect_candidate_games(
    client: EthicalHTTPClient,
    modes: list[str],
    limit: int,
) -> list[tuple[str, dict[str, Any], list[str]]]:
    """
    Coleta e deduplica os jogos candidatos a partir dos rankings do SteamSpy,
    registrando em quais listas cada jogo apareceu (ex.: ['top100in2weeks', 'top100forever']).
    """
    candidates: dict[str, dict[str, Any]] = {}
    sources_by_appid: dict[str, list[str]] = {}

    for mode in modes:
        try:
            ranking_data = fetch_steamspy_ranking(client, mode=mode)
        except requests.RequestException as exc:
            logger.error("Falha ao consultar modo '%s' no SteamSpy: %s", mode, exc)
            continue

        for appid_str, summary in ranking_data.items():
            if not isinstance(summary, dict):
                continue
            appid_key = str(summary.get("appid", appid_str))
            if appid_key not in candidates:
                candidates[appid_key] = summary
                sources_by_appid[appid_key] = [mode]
            elif mode not in sources_by_appid[appid_key]:
                sources_by_appid[appid_key].append(mode)

    # Ordena priorizando maior CCU (jogadores simultâneos) reportado no resumo inicial
    sorted_items = sorted(
        candidates.items(),
        key=lambda item: int(item[1].get("ccu") or 0),
        reverse=True,
    )

    selected = sorted_items[:limit]
    return [
        (appid, summary, sources_by_appid.get(appid, []))
        for appid, summary in selected
    ]


def collect_steam_games(
    limit: int = DEFAULT_LIMIT,
    modes: list[str] | None = None,
    include_live_ccu: bool = True,
    rate_limit_seconds: float = RATE_LIMIT_SECONDS,
) -> list[dict[str, Any]]:
    """
    Executa o pipeline completo de coleta da Steam:
    1. Obtém lista de jogos a partir dos rankings do SteamSpy.
    2. Enriquece cada jogo via `appdetails` do SteamSpy (gêneros e tags de subgêneros).
    3. Opcionalmente anexa `live_player_count` via API oficial da Steam.
    """
    effective_modes = modes or list(DEFAULT_MODES)
    records: list[dict[str, Any]] = []

    with EthicalHTTPClient(rate_limit_seconds=rate_limit_seconds) as client:
        candidates = collect_candidate_games(client, modes=effective_modes, limit=limit)
        total = len(candidates)
        logger.info("Total de jogos únicos selecionados para enriquecimento: %d", total)

        for idx, (appid, summary, ranking_sources) in enumerate(candidates, start=1):
            game_name = summary.get("name", f"App {appid}")
            logger.info("[%d/%d] Coletando detalhes de '%s' (appid=%s)...", idx, total, game_name, appid)

            record: dict[str, Any] = dict(summary)
            record["ranking_sources"] = ranking_sources

            # Enriquece com genre e tags completas via SteamSpy appdetails
            try:
                details = fetch_steamspy_appdetails(client, appid=appid)
                if details:
                    record.update(details)
            except requests.RequestException as exc:
                logger.warning(
                    "Falha ao buscar appdetails no SteamSpy para appid=%s (%s): %s",
                    appid,
                    game_name,
                    exc,
                )

            # Enriquece com contagem de jogadores online em tempo real na Steam
            if include_live_ccu:
                record["live_player_count"] = fetch_steam_live_players(client, appid=appid)

            records.append(record)

    return records


def parse_args() -> argparse.Namespace:
    """Configura e processa argumentos de linha de comando (CLI)."""
    parser = argparse.ArgumentParser(
        description="Coletor ético de dados de jogos da Steam / SteamSpy (IMD1152 - UFRN)."
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help=f"Modo de teste rápido: coleta apenas {SAMPLE_LIMIT} jogos.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=f"Quantidade máxima de jogos a coletar (padrão: {DEFAULT_LIMIT}, ou {SAMPLE_LIMIT} com --sample).",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        default=list(DEFAULT_MODES),
        choices=["top100in2weeks", "top100forever", "top100owned", "all"],
        help="Listas do SteamSpy a consultar para descobrir jogos.",
    )
    parser.add_argument(
        "--skip-live-ccu",
        action="store_true",
        help="Não consulta o endpoint em tempo real GetNumberOfCurrentPlayers da Steam.",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=RATE_LIMIT_SECONDS,
        help=f"Intervalo mínimo em segundos entre requisições (padrão: {RATE_LIMIT_SECONDS}s).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILENAME,
        help=f"Nome do arquivo JSON salvo em data/raw/ (padrão: {OUTPUT_FILENAME}).",
    )
    return parser.parse_args()


def main() -> None:
    """Ponto de entrada do coletor da Steam."""
    args = parse_args()
    effective_limit = args.limit if args.limit is not None else (
        SAMPLE_LIMIT if args.sample else DEFAULT_LIMIT
    )

    logger.info(
        "Iniciando coleta Steam | limit=%d | modes=%s | live_ccu=%s | rate_limit=%.2fs",
        effective_limit,
        args.modes,
        not args.skip_live_ccu,
        args.rate_limit,
    )

    records = collect_steam_games(
        limit=effective_limit,
        modes=args.modes,
        include_live_ccu=not args.skip_live_ccu,
        rate_limit_seconds=args.rate_limit,
    )

    if not records:
        logger.warning("Nenhum registro foi coletado. Verifique a conexão ou disponibilidade da API.")
        return

    output_path = save_raw_json(
        records=records,
        filename=args.output,
        platform="steam",
    )
    logger.info(
        "Coleta finalizada com sucesso! %d jogos salvos em: %s",
        len(records),
        output_path,
    )


if __name__ == "__main__":
    main()
