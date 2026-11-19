"""Configurações globais, diretórios e parâmetros éticos HTTP do projeto."""

from pathlib import Path

# Diretórios principais do projeto
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
DOCS_DIR: Path = BASE_DIR / "docs"
FIGURES_DIR: Path = DOCS_DIR / "figures"
GENRE_MAPPING_PATH: Path = BASE_DIR / "processing" / "genre_mapping.json"

# Identificação acadêmica padrão (IMD / UFRN - IMD1152)
PROJECT_NAME: str = "IMD1152-GameGenres-UFRN"
PROJECT_VERSION: str = "1.0"
CONTACT_INFO: str = (
    "https://github.com/SEU-USUARIO/projeto-coleta-e-raspagem-de-dados; "
    "contato-equipe@ufrn.edu.br"
)
USER_AGENT: str = (
    f"{PROJECT_NAME}/{PROJECT_VERSION} "
    f"(Academic Research - IMD/UFRN; {CONTACT_INFO})"
)

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Parâmetros éticos de requisição HTTP
REQUEST_TIMEOUT: int = 15
RATE_LIMIT_SECONDS: float = 1.5
MAX_RETRIES: int = 3
BACKOFF_FACTOR: float = 1.0
RETRY_STATUS_CODES: tuple[int, ...] = (429, 500, 502, 503, 504)
