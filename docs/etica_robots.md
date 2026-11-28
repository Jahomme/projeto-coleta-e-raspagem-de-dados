# Auditoria Ética, `robots.txt` e Termos de Serviço (ToS)

> **Responsável:** Victor Emanuel Oliveira Silva  
> **Status:** Tamo caminhando

---

## 1. Visão Geral Ética e LGPD

- 

TODO: Descrever princípios éticos adotados (coleta exclusivamente acadêmica, ausência de dados pessoais conforme LGPD, identificação via `User-Agent` da UFRN, controle de taxa de requisições).

---

## 2. Auditoria de `robots.txt` e ToS por Plataforma

### 2.1. Steam / SteamSpy
- **URL verificada:** 'https://store.steampowered.com/robots.txt'
(robots.txt do SteamSpy indisponível)
- **Diretivas `robots.txt` relevantes:**
User-Agent: *
Disallow: /share/
Disallow: /news/externalpost/
Disallow: /account/emailoptout/?*token=
Disallow: /account/notificationsettings/?*token=
Disallow: /login/?*guestpasskey=
Disallow: /join/?*redir=
Disallow: /account/ackgift/
Disallow: /email/
Disallow: /widget/

- **Método adotado (API / Endpoints permitidos):** TODO

### 2.2. Roblox
- **URL verificada:** 'https://www.roblox.com/robots.txt'
- **Diretivas `robots.txt` relevantes:** 
User-agent: *
Disallow: /catalog/contents
Disallow: /catalog/html
Disallow: /client-status
Disallow: /data/
Disallow: /game/report-event
Disallow: /game/report-stats
Disallow: /reports/
Disallow: /badges/
Sitemap: https://www.roblox.com/sitemap-games.xml

- **Método adotado (APIs públicas):** Consumo dos Endpoints JSON públicos da API oficial de jogos, capturar experiências populares, jogadores ativos no momento, a contagem de visitas e categorias, respeintando os acessos não permitidos (Disallow).

### 2.3. GOG
- **URL verificada:** 'https://www.gog.com/robots.txt'
- **Diretivas `robots.txt` relevantes:**
User-agent: * 
Disallow: /upload/
Disallow: /www/
Disallow: /downloader2/
Disallow: /galaxy_notifications/
Disallow: /unsubscribe/
Disallow: /profile

- **Método adotado (Catálogo JSON público):** TODO

### 2.4. Itch.io
- **URL verificada:** 'https://itch.io/robots.txt'
- **Diretivas `robots.txt` relevantes:**
User-agent: *
Disallow: /embed/
Disallow: /embed-upload/
Disallow: /search
Disallow: /checkout/
Disallow: /game/download/
Disallow: /bundle/download/
Disallow: /register-for-purchase/
Disallow: /email-feedback/
Sitemap: 'https://itch.io/sitemap.xml'

- **Método adotado (Web Scraping HTML em rotas permitidas):** TODO

---

## 3. Justificativa Ética de Exclusão da Epic Games Store

- TODO: Documentar as restrições encontradas nos Termos de Serviço da Epic Games e as proteções anti-bot identificadas, justificando o descarte proposital da plataforma como decisão ética de conformidade.

---

## 4. Política de Rate Limiting e `User-Agent`

- TODO: Registrar os valores definidos em `config/settings.py` e `collectors/utils.py` (atraso entre requisições, tratamento de HTTP 429 e `User-Agent` identificável).
