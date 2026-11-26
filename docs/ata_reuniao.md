# Ata de Reuniões — Projeto IMD1152

**Disciplina:** IMD1152 – Coleta e Raspagem de Dados (IMD / UFRN)  
**Docente:** Profa. Dra. Francimaria Nascimento  
**Projeto:** Mapeamento Multiplataforma de Gêneros e Subgêneros de Jogos Digitais  
**Responsável pela Documentação:** Kauê Rebouças 

---

## Registro 01 — Definição do Escopo, Fontes e Repositório

* **Data:** 19 de novembro de 2026  
* **Horário:** 17:00  
* **Local:** Google Meet e WhatsApp  
* **Participantes Presentes:**
  * FABIO FELIX RODRIGUES
  * VITOR GABRIEL QUEIROZ DA COSTA
  * KAUE REBOUCAS DE ARAUJO
  * JADILSON IGOR DE CAMPOS LOPES
  * VICTOR EMANUEL OLIVEIRA SILVA

### Pauta
1. Escolha do tema e definição das plataformas de jogos a serem analisadas.
2. Análise de viabilidade técnica e restrições éticas de coleta.
3. Definição da arquitetura inicial do repositório no GitHub.

### Decisões Tomadas
* **Exclusão Ética da Epic Games Store:** A plataforma foi descartada devido às proibições explícitas em seus Termos de Serviço (ToS) e bloqueios anti-bot ativos. Para manter a diversidade de fontes de forma ética, decidiu-se substituí-la pelo **Itch.io** (via Web Scraping HTML em rotas permitidas), operando em conjunto com **Steam**, **Roblox** e **GOG** (via APIs REST/JSON).
* **Criação do Repositório Oficial:** Repositório criado sob a organização `Jahomme/projeto-coleta-e-raspagem-de-dados`, com convites enviados a todos os colaboradores.
* **Cliente HTTP Ético Compartilhado:** Aprovada a criação do módulo `collectors/utils.py` contendo `User-Agent` acadêmico identificável da UFRN, tratamento de *rate limiting* e política de *retry* com *backoff* exponencial para padronizar as requisições de todos os integrantes.

---

## Registro 02 — Divisão Oficial de Tarefas e Workflow do Git

* **Data:** 21 de novembro de 2026  
* **Horário:** 19:00  
* **Local:** Google Meet e WhatsApp  
* **Participantes Presentes:**
  * FABIO FELIX RODRIGUES
  * VITOR GABRIEL QUEIROZ DA COSTA
  * KAUE REBOUCAS DE ARAUJO
  * JADILSON IGOR DE CAMPOS LOPES
  * VICTOR EMANUEL OLIVEIRA SILVA

### Pauta
1. Alinhamento sobre o fluxo de desenvolvimento em *branches* paralelas no Git.
2. Atribuição das *issues* abertas no repositório entre os integrantes.

### Decisões Tomadas
* **Atribuição Modular do Projeto:**
  * **Integrante 1:** Desenvolver `collectors/utils.py` e `collectors/steam_collector.py` (`data/raw/steam_raw.json`).
  * **Integrante 2:** Desenvolver `collectors/roblox_gog_collector.py` (`data/raw/roblox_raw.json` e `gog_raw.json`), prestando suporte posterior na etapa de análise e visualizações.
  * **Integrante 3:** Desenvolver `collectors/itchio_collector.py` (`data/raw/itchio_raw.csv`) e redigir a documentação de auditoria em `docs/etica_robots.md`.
  * **Integrante 4:** Desenvolver a pipeline de pré-processamento em `processing/clean_and_merge.py` e o dicionário de taxonomia em `processing/genre_mapping.json`.
  * **Integrante 5:** Desenvolver o módulo de visualizações (`analysis/generate_charts.py`), relatórios técnicos, atas e slides da apresentação oral.

---

## Registro 03 — Entrega Parcial (SIGAA) e Alinhamento do Pipeline ETL

* **Data:** 23 de novembro de 2026  
* **Horário:** 17:30  
* **Local:** Google Meet e WhatsApp  
* **Participantes Presentes:**
  * FABIO FELIX RODRIGUES
  * VITOR GABRIEL QUEIROZ DA COSTA
  * KAUE REBOUCAS DE ARAUJO
  * JADILSON IGOR DE CAMPOS LOPES
  * VICTOR EMANUEL OLIVEIRA SILVA

### Pauta
1. Validação e submissão da atividade de reposição de aula no SIGAA ("Descrição do Problema").
2. Acompanhamento do progresso da coleta de dados brutos e desbloqueio da etapa de tratamento (ETL).
3. Definição do cronograma até o prazo final de submissão (30/11/2026).

### Decisões Tomadas
* **Envio da Atividade Parcial:** O documento em PDF com a "Descrição do Problema" foi elaborado e submetido no SIGAA pelo Integrante 1.
* **Prazo Limite para Coleta de Dados:** Os responsáveis pelos coletores (Integrantes 1, 2 e 3) devem disponibilizar seus arquivos de dados brutos na pasta `data/raw/` até o final do dia 25/11/2026.
* **Sequenciamento dos Próximos Passos:** O Integrante 4 iniciará a limpeza, tratamento de nulos/outliers e fusão taxonômica assim que os arquivos brutos forem entregues. Em paralelo, o Integrante 5 avançará na documentação técnica, estruturação do script de gráficos e preparação dos slides da apresentação.