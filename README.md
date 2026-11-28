# Mapeamento Multiplataforma de Gêneros e Subgêneros de Jogos Digitais

Projeto da disciplina **IMD1152 – Coleta e Raspagem de Dados** (Instituto Metrópole Digital – IMD / UFRN), ministrada pela **Profa. Dra. Francimaria Nascimento**.

## Objetivo

Analisar o ecossistema de jogos digitais nas plataformas **Steam**, **Roblox**, **GOG** e **Itch.io** combinando coleta via **APIs REST** e **Web Scraping HTML**, identificando quais gêneros e subgêneros concentram maior volume de jogadores e quais apresentam tendência de ascensão.

> **Nota Ética e LGPD:** Todas as coletas respeitam `robots.txt`, Termos de Serviço (ToS), *rate limiting*, `User-Agent` acadêmico identificável e não coletam dados pessoais. A **Epic Games Store** foi descartada propositalmente devido a restrições severas de ToS e mecanismos anti-bot, decisão documentada em [`docs/etica_robots.md`](docs/etica_robots.md).

---

## Estrutura do Repositório

```text
projeto-coleta-e-raspagem-de-dados/
├── .gitignore
├── README.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   └── settings.py                  # Configurações globais e User-Agent acadêmico
├── collectors/
│   ├── __init__.py
│   ├── utils.py                     # Cliente HTTP ético compartilhado e persistência raw
│   ├── steam_collector.py           # Coleta Steam / SteamSpy
│   ├── roblox_gog_collector.py      # Coleta Roblox e GOG
│   └── itchio_collector.py          # Web Scraping HTML no Itch.io
├── processing/
│   ├── __init__.py
│   ├── clean_and_merge.py           # Limpeza, tratamento e unificação dos dados
│   └── genre_mapping.json           # Dicionário de mapeamento para macro-gêneros
├── analysis/
│   ├── __init__.py
│   └── generate_charts.py           # Geração dos gráficos em docs/figures/
├── data/
│   ├── raw/                         # Dados brutos fiéis à fonte (ignorados no Git)
│   └── processed/                   # Dataset unificado final (ignorado no Git)
└── docs/
    ├── figures/                     # Gráficos exportados
    ├── etica_robots.md              # Auditoria de robots.txt, ToS e decisões éticas
    ├── ata_reuniao.md               # Registro das reuniões da equipe
    └── relatorio_tecnico.md         # Relatório técnico do projeto
```

---

## Divisão de Tarefas e Branches (Trabalho Paralelo)

| Integrante | Branch sugerida | Arquivos sob responsabilidade | Escopo principal |
| :--- | :--- | :--- | :--- |
| **Integrante 1** | `feat/steam-collector` | `collectors/utils.py`, `collectors/steam_collector.py` | Base HTTP ética compartilhada e coleta Steam / SteamSpy (`data/raw/steam_raw.json`) |
| **Integrante 2** | `feat/roblox-gog-collector` | `collectors/roblox_gog_collector.py` | Coleta via APIs públicas da Roblox e catálogo JSON da GOG (`roblox_raw.json` e `gog_raw.json`) |
| **Integrante 3** | `feat/itchio-scraping-etica` | `collectors/itchio_collector.py`, `docs/etica_robots.md` | Web Scraping HTML do Itch.io (`itchio_raw.csv`) e auditoria ética de todas as plataformas |
| **Integrante 4** | `feat/processing-etl` | `processing/clean_and_merge.py`, `processing/genre_mapping.json` | Limpeza, tratamento de nulos/duplicados/outliers e unificação em `data/processed/games_unificado.csv` |
| **Integrante 5** | `feat/analysis-docs` | `analysis/generate_charts.py`, `docs/ata_reuniao.md`, `docs/relatorio_tecnico.md`, `README.md` | Visualizações em `docs/figures/`, documentação técnica e apresentação final |

---

## Configuração do Ambiente Local

### 1. Criar e ativar o ambiente virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## Execução dos Módulos

Execute sempre a partir da **raiz do repositório** usando `-m` para que as importações de `config` e `collectors` funcionem corretamente:

```bash
# Coletores (podem rodar em paralelo em terminais separados)
python -m collectors.steam_collector
python -m collectors.roblox_gog_collector
python -m collectors.itchio_collector

# Pré-processamento e unificação
python -m processing.clean_and_merge

# Geração de gráficos
python -m analysis.generate_charts
```

### Flags do Coletor da Steam (`collectors.steam_collector`)

| Flag | Valores / Tipo | Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `--sample` | booleana (sem valor) | `False` | Modo de teste rápido: coleta apenas `10` jogos. |
| `--limit` | `int` | `100` (ou `10` com `--sample`) | Quantidade máxima de jogos únicos a enriquecer e salvar. |
| `--modes` | `top100in2weeks`, `top100forever`, `top100owned`, `all` (aceita 1 ou mais) | `top100in2weeks top100forever` | Rankings/listas do SteamSpy consultados para descoberta de jogos. |
| `--skip-live-ccu` | booleana (sem valor) | `False` | Pula a consulta em tempo real ao endpoint `GetNumberOfCurrentPlayers` da Steam (coleta mais rápida usando apenas o `ccu` do SteamSpy). |
| `--rate-limit` | `float` (segundos) | `1.5` | Intervalo mínimo em segundos entre requisições HTTP consecutivas. |
| `--output` | `str` (nome do arquivo) | `steam_raw.json` | Nome do arquivo JSON gerado dentro de `data/raw/`. |
| `-h`, `--help` | — | — | Exibe a ajuda completa das opções no terminal. |

**Exemplos de uso:**

```bash
# Teste rápido com 10 jogos
python -m collectors.steam_collector --sample

# Coletar apenas o ranking das últimas 2 semanas em arquivo separado
python -m collectors.steam_collector --modes top100in2weeks --output steam_2weeks_raw.json

# Coletar apenas o ranking histórico (forever)
python -m collectors.steam_collector --modes top100forever --output steam_forever_raw.json

# Coletar todos os jogos únicos da união dos dois rankings sem a chamada extra de live_player_count
python -m collectors.steam_collector --limit 200 --skip-live-ccu
```
