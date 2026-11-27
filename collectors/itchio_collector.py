"""
Coletor de dados via Web Scraping HTML do catálogo Itch.io.

Responsável: Victor Emanuel Oliveira Silva
Saída esperada: data/raw/itchio_raw.csv
Executar: python -m collectors.itchio_collector
"""

from __future__ import annotations
import requests
import time
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

from collectors.utils import EthicalHTTPClient, save_raw_csv

BASE_URL = "https://itch.io"
OUTPUT_PATH = "data/raw/itchio_raw.csv"

GENRES = ["action", "adventure", "puzzle", "rpg", "simulation", "strategy"]
TAGS = ["pixel-art", "horror", "platformer", "visual-novel", "roguelike"]

def scrape_listing(base_path: str, source_type: str, source_value: str, max_pages: int = 5) -> list:
    """
    Raspa uma listagem do itch.io (gênero ou tag) com paginação.
    
    :param base_path: Caminho base da URL (ex: "/games/genre-action").
    :param source_type: "genre" ou "tag" (para registrar a origem do dado).
    :param source_value: Valor do gênero ou tag (ex: "action").
    :param max_pages: Número máximo de páginas a serem coletadas (evita sobrecarga).
    :return: Lista de dicionários com os dados brutos dos jogos.
    """
    client = EthicalHTTPClient()  # Cliente HTTP ético do projeto (respeita robots.txt e rate limit)
    games_data = []
    page = 1
    
    while page <= max_pages:
        # Constrói a URL da página atual (itch.io usa ?page=N para paginação)
        url = f"{BASE_URL}{base_path}?page={page}"
        print(f"Coletando: {url}")
        
        try:
            response = client.get(url)
            if response.status_code != 200:
                print(f"Status {response.status_code}. Encerrando paginação.")
                break
        except Exception as e:
            print(f"Erro na requisição: {e}")
            break
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Cada jogo na listagem está dentro de uma div com a classe "game_cell"
        game_cells = soup.find_all("div", class_="game_cell")
        if not game_cells:
            print("  -> Nenhum jogo encontrado nesta página. Fim da paginação.")
            break
        
        for cell in game_cells:
            # Extração dos campos de cada jogo
            # Título (dentro de div.game_title)
            title_tag = cell.find("div", class_="game_title")
            title = title_tag.get_text(strip=True) if title_tag else None
            
            # Autor (div.game_author)
            author_tag = cell.find("div", class_="game_author")
            author = author_tag.get_text(strip=True) if author_tag else None
            
            # Link do jogo (a.game_link)
            link_tag = cell.find("a", class_="game_link")
            game_url = link_tag["href"] if link_tag and link_tag.has_attr("href") else None
            if game_url and game_url.startswith("/"):
                game_url = urljoin(BASE_URL, game_url)
            
            # Gênero exibido na listagem (div.game_genre)
            genre_tag = cell.find("div", class_="game_genre")
            genre = genre_tag.get_text(strip=True) if genre_tag else "Unknown"
            
            # ID do jogo (atributo data-game_id da div)
            game_id = cell.get("data-game_id")
            
            # Montagem do registro bruto
            record = {
                "game_id": game_id,
                "title": title,
                "author": author,
                "game_url": game_url,
                "genre_in_listing": genre,
                "source_type": source_type,   # "genre" ou "tag"
                "source_value": source_value, # ex: "action" ou "pixel-art"
                "listing_page": page,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            games_data.append(record)
        
        print(f"{len(game_cells)} jogos extraídos da página {page}.")
        
        # Verifica se existe um link para a próxima página
        # O itch.io geralmente usa um link com a classe "next_page" no final da listagem
        next_link = soup.find("a", class_="next_page")
        if not next_link:
            # Alternativa: verificar se há um link com texto "Next" ou "Próximo"
            next_link = soup.find("a", string=lambda t: t and ("Next" in t or "Próximo" in t))
        
        if not next_link:
            print("Não há link para próxima página. Encerrando.")
            break
        
        # Extrai o número da página do href do link (ex: ?page=2)
        href = next_link.get("href", "")
        parsed = urlparse(href)
        query_params = parse_qs(parsed.query)
        next_page_num = query_params.get("page", [None])[0]
        
        if next_page_num:
            page = int(next_page_num)
        else:
            page += 1
        
        # Pausa de cortesia entre páginas (o EthicalHTTPClient pode já fazer isso)
        time.sleep(1)
    
    return games_data

def main() -> None:
    """
    Ponto de entrada: itera sobre gêneros e tags, coleta os dados e salva o CSV bruto.
    """
    all_games = []
    
    # 1. Coleta por gênero
    for genre in GENRES:
        path = f"/games/genre-{genre}"
        print(f"\n=== Iniciando coleta por GÊNERO: {genre} ===")
        data = scrape_listing(path, source_type="genre", source_value=genre, max_pages=3)  # Limite de páginas para teste
        all_games.extend(data)
    
    # 2. Coleta por tag
    for tag in TAGS:
        path = f"/games/tag-{tag}"
        print(f"\n=== Iniciando coleta por TAG: {tag} ===")
        data = scrape_listing(path, source_type="tag", source_value=tag, max_pages=3)
        all_games.extend(data)
    
    # 3. Salvamento via utilitário do projeto
    if all_games:
        # Assumindo que save_raw_csv(data, filename, source_name)
        save_raw_csv(all_games, "itchio_raw.csv", "itchio")
        print(f"\nTotal de {len(all_games)} registros salvos em data/raw/itchio_raw.csv")
    else:
        print("\nNenhum dado foi coletado. Verifique as URLs ou a conexão.")

if __name__ == "__main__":
    main()

"""
def main() -> None:
    # Implementar verificação de robots.txt e Web Scraping HTML com BeautifulSoup
    # usando collectors.utils.EthicalHTTPClient e salvar via save_raw_csv(..., "itchio_raw.csv", "itchio").
    pass


if __name__ == "__main__":
    main()
    """
