#!/usr/bin/env python3
"""
Neural Pro Bot ⚽ — VERSÃO COMPLETA
Bot do Telegram para análise de estatísticas de futebol via SofaScore.

MERCADOS ANALISADOS (1º Tempo + Jogo Todo):
  • Finalizações (totais e a gol)
  • Escanteios
  • Faltas
  • Cartões (amarelos)
  • Posse de bola
  • Passes
  • Defesas do goleiro
  • Gols
  • Chutes para fora / bloqueados
  • Ataques perigosos
  • Cruzamentos
  • Desarmes (tackles)
  • Impedimentos
  • PANORAMA GERAL (todos os mercados de uma vez)

Coletor 100% gratuito (SofaScore via curl_cffi com impersonate de browser).
Atualização diária automática (sempre puxa os 5 últimos jogos finalizados).

Requisitos:
    pip install pyTelegramBotAPI curl_cffi

Uso:
    python3 main_v3.py
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from curl_cffi import requests as cf_requests
from datetime import datetime

# ============================================================
# ⚠ TOKEN DO BOTFATHER (já configurado)
# ============================================================
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8672314850:AAFdDjsceTGcgPMfnQXYybrl5Eoc_seKHvs")
# ============================================================

# ============================================================
# 🔒 TRAVA DE ACESSO — Apenas membros do grupo autorizado
# ============================================================
GRUPO_AUTORIZADO_ID = -1003611765348

MSG_ACESSO_NEGADO = (
    "🚫 *Acesso Negado*\n\n"
    "Olá! Este é um bot *exclusivo* para membros autorizados.\n\n"
    "Você ainda *não possui permissão* para utilizar este serviço.\n\n"
    "📌 Para solicitar acesso, consulte as *informações de contato* "
    "disponíveis na *descrição (bio) deste bot*.\n\n"
    "_Obrigado pela compreensão._"
)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Cache de usuários autorizados (evita consulta repetida à API do Telegram)
_auth_cache = {}  # {user_id: (autorizado_bool, timestamp)}
_AUTH_TTL = 300  # 5 minutos

def usuario_autorizado(user_id: int) -> bool:
    """Verifica se o usuário é membro do grupo autorizado."""
    import time
    agora = time.time()
    cache = _auth_cache.get(user_id)
    if cache and (agora - cache[1] < _AUTH_TTL):
        return cache[0]
    try:
        membro = bot.get_chat_member(GRUPO_AUTORIZADO_ID, user_id)
        status = getattr(membro, "status", "")
        autorizado = status in ("creator", "administrator", "member", "restricted")
    except Exception as e:
        print(f"[AUTH] Erro ao verificar usuário {user_id}: {e}")
        autorizado = False
    _auth_cache[user_id] = (autorizado, agora)
    return autorizado

def bloquear_se_nao_autorizado(obj) -> bool:
    """
    Recebe um Message ou CallbackQuery.
    Se o usuário NÃO for autorizado, envia a mensagem de acesso negado e retorna True.
    Caso contrário, retorna False.
    """
    # Identifica user_id e chat_id conforme o tipo
    if hasattr(obj, "from_user") and hasattr(obj, "message") and obj.message is not None:
        # CallbackQuery
        user_id = obj.from_user.id
        chat_id = obj.message.chat.id
        is_callback = True
    else:
        # Message
        user_id = obj.from_user.id
        chat_id = obj.chat.id
        is_callback = False

    if usuario_autorizado(user_id):
        return False

    try:
        bot.send_message(chat_id, MSG_ACESSO_NEGADO, parse_mode="Markdown")
    except Exception as e:
        print(f"[AUTH] Falha ao enviar mensagem de bloqueio: {e}")
    if is_callback:
        try:
            bot.answer_callback_query(obj.id, "🚫 Acesso negado", show_alert=True)
        except Exception:
            pass
    return True

# Estado de sessão em memória (por user_id)
sessions = {}

# ----------------------------------------------------------
# Ligas disponíveis (SofaScore category_id)
# ----------------------------------------------------------
LIGAS = [
    {"nome": "🇧🇷 Brasil", "category_id": 13},
    {"nome": "🏴 Inglaterra", "category_id": 1},
    {"nome": "🇪🇸 Espanha", "category_id": 32},
    {"nome": "🇩🇪 Alemanha", "category_id": 30},
    {"nome": "🇮🇹 Itália", "category_id": 31},
    {"nome": "🇫🇷 França", "category_id": 7},
    {"nome": "🇵🇹 Portugal", "category_id": 44},
    {"nome": "🇳🇱 Holanda", "category_id": 35},
    {"nome": "🇦🇷 Argentina", "category_id": 48},
    {"nome": "🇺🇸 EUA (MLS)", "category_id": 26},
    {"nome": "🏆 Europa (Champions / Europa / Conference)", "category_id": 1465},
    {"nome": "🌎 América (Libertadores / Sul-Americana / Recopa)", "category_id": 1477},
    {"nome": "🌍 Seleções (Copa do Mundo / Euro / Copa América)", "category_id": 1468},
]

TORNEIOS_FIXOS_POR_CATEGORIA = {
    1477: [
        {"id": 384, "nome": "CONMEBOL Libertadores"},
        {"id": 480, "nome": "CONMEBOL Sudamericana"},
        {"id": 490, "nome": "CONMEBOL Recopa"},
    ],
}

# ----------------------------------------------------------
# Mercados disponíveis para análise
# Cada item: (chave_callback, nome_exibicao, sofascore_key, unidade)
# ----------------------------------------------------------
MERCADOS = [
    ("finalizacoes",   "🎯 Finalizações Totais",     "totalShotsOnGoal",   "fin."),
    ("chutes_gol",     "🥅 Chutes a Gol",            "shotsOnGoal",        "chutes"),
    ("chutes_fora",    "↗️ Chutes Para Fora",         "shotsOffGoal",       "chutes"),
    ("chutes_bloq",    "🛡️ Chutes Bloqueados",        "blockedScoringAttempt", "chutes"),
    ("escanteios",     "🚩 Escanteios",              "cornerKicks",        "esc."),
    ("faltas",         "⚠️ Faltas",                   "fouls",              "faltas"),
    ("cartoes",        "🟨 Cartões Amarelos",         "yellowCards",        "cart."),
    ("posse",          "⚽ Posse de Bola (%)",        "ballPossession",     "%"),
    ("passes",         "🔄 Passes",                  "passes",             "passes"),
    ("defesas",        "🧤 Defesas do Goleiro",       "goalkeeperSaves",    "def."),
    ("gols",           "⚽ Gols",                    "goals",              "gols"),
    ("ataques_perig",  "🔥 Ataques Perigosos",        "bigChanceCreated",   "ataq."),
    ("cruzamentos",    "✈️ Cruzamentos",              "crosses",            "cruz."),
    ("desarmes",       "💪 Desarmes",                "tackles",            "des."),
    ("impedimentos",   "🚫 Impedimentos",            "offsides",           "imp."),
    ("panorama",       "📊 PANORAMA GERAL (TUDO)",    None,                 None),
]

SOFASCORE_BASES = [
    "https://api.sofascore.com/api/v1",
    "https://www.sofascore.com/api/v1",
]

# Rotação de fingerprints de browser para driblar Cloudflare em Cloud Run / GCP
IMPERSONATE_POOL = [
    "chrome124", "chrome120", "chrome119", "chrome116",
    "edge101", "safari17_0", "chrome110",
]

# Proxy opcional (defina HTTP_PROXY_URL / HTTPS_PROXY_URL ou HTTP_PROXY / HTTPS_PROXY
# nas env vars do Cloud Run para usar proxy residencial — ex:
# http://user:pass@host:port). Recomendado se a SofaScore bloquear IP de datacenter.
PROXY_URL = (
    os.environ.get("HTTP_PROXY_URL", "").strip()
    or os.environ.get("HTTPS_PROXY_URL", "").strip()
    or os.environ.get("HTTP_PROXY", "").strip()
    or os.environ.get("HTTPS_PROXY", "").strip()
)
PROXIES = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

# Headers extras para parecer um browser real visitando o site
DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.sofascore.com",
    "Referer": "https://www.sofascore.com/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

DEBUG_HTTP = os.environ.get("DEBUG_HTTP", "0") == "1"
REQUEST_DELAY_MS = int(os.environ.get("REQUEST_DELAY_MS", "450"))

# Sessão persistente (mantém cookies do Cloudflare entre requisições)
import random as _random
_session = None

def _new_session():
    s = cf_requests.Session()
    s.headers.update(DEFAULT_HEADERS)
    return s

_session = _new_session()

def _session_cookie_hint():
    try:
        jar = getattr(_session, "cookies", None)
        if not jar:
            return "sem-cookies"
        keys = [str(k) for k in jar.keys()]
        return ",".join(keys[:6]) if keys else "sem-cookies"
    except Exception:
        return "cookies-indisponiveis"

# ----------------------------------------------------------
# Helpers SofaScore
# ----------------------------------------------------------

def sofascore_get(path, max_retries=6):
    """GET com rotação de impersonate + retry + suporte a proxy.
    Retorna o JSON em caso de sucesso, ou None.
    """
    global _session
    last_status = None
    import time as _t
    for base in SOFASCORE_BASES:
        url = f"{base}{path}"
        for tentativa in range(max_retries):
            impersonate = IMPERSONATE_POOL[(tentativa + len(path)) % len(IMPERSONATE_POOL)]
            try:
                if REQUEST_DELAY_MS > 0:
                    _t.sleep((REQUEST_DELAY_MS / 1000.0) + _random.random() * 0.35)

                resp = _session.get(
                    url,
                    impersonate=impersonate,
                    headers=DEFAULT_HEADERS,
                    proxies=PROXIES,
                    timeout=25,
                )
                last_status = resp.status_code
                if DEBUG_HTTP:
                    snippet = resp.text[:140].replace("\n", " ") if getattr(resp, "text", None) else ""
                    print(f"[HTTP] {resp.status_code} ({impersonate}) {url} cookies={_session_cookie_hint()} body={snippet}")

                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except Exception:
                        if DEBUG_HTTP:
                            print(f"[HTTP] Resposta 200 não-JSON em {url}")

                elif resp.status_code in (301, 302, 307, 308):
                    location = resp.headers.get("location", "")
                    if DEBUG_HTTP and location:
                        print(f"[HTTP] redirect => {location}")

                elif resp.status_code in (401, 403, 429, 503):
                    if tentativa in (1, 3):
                        _session = _new_session()
                    _t.sleep(1.5 + _random.random() * 2.2)
                    continue

                elif resp.status_code == 404:
                    break

            except Exception as e:
                print(f"[HTTP] Erro tentativa {tentativa+1} em {url}: {e}")
                if tentativa in (1, 3):
                    _session = _new_session()
                _t.sleep(1.2 + _random.random())

    print(f"[HTTP] FALHOU após varrer bases/tentativas (último status={last_status}) path={path}")
    return None

def buscar_torneios(category_id):
    data = sofascore_get(f"/category/{category_id}/unique-tournaments")
    if not data:
        return TORNEIOS_FIXOS_POR_CATEGORIA.get(category_id, [])

    excluir = ["feminino", "women", "sub-", "u-", "u1", "u2", "u3",
               "futsal", "beach", "youth", "reserve", "amador"]

    torneios = []
    grupos = data.get("groups", [])
    lista_t = []
    if grupos:
        lista_t = grupos[0].get("uniqueTournaments", [])
    if not lista_t:
        lista_t = data.get("uniqueTournaments", [])

    for t in lista_t:
        nome = t.get("name", "")
        nome_lower = nome.lower()
        if any(p in nome_lower for p in excluir):
            continue
        torneios.append({"id": t["id"], "nome": nome})
        if len(torneios) >= 20:
            break

    if not torneios:
        return TORNEIOS_FIXOS_POR_CATEGORIA.get(category_id, [])

    fixos = TORNEIOS_FIXOS_POR_CATEGORIA.get(category_id, [])
    existentes = {int(t["id"]) for t in torneios if t.get("id") is not None}
    for t in fixos:
        if int(t["id"]) not in existentes:
            torneios.append(t)

    return torneios

def buscar_time(nome):
    data = sofascore_get(f"/search/all?q={nome}")
    if not data:
        return None
    results = data.get("results", [])
    teams = [
        r["entity"] for r in results
        if r.get("type") == "team"
        and r["entity"].get("sport", {}).get("slug") == "football"
    ]
    return teams[0] if teams else None

def buscar_eventos(team_id, tournament_id=None):
    """Últimos 5 jogos finalizados (ordenados do mais recente p/ mais antigo)."""
    eventos_encontrados = []
    for page in range(3):
        data = sofascore_get(f"/team/{team_id}/events/last/{page}")
        if not data:
            break
        page_events = data.get("events", [])
        if not page_events:
            break
        for ev in page_events:
            if ev.get("status", {}).get("type") == "finished":
                if tournament_id:
                    t_id = str(ev.get("tournament", {}).get("uniqueTournament", {}).get("id", ""))
                    if t_id != str(tournament_id):
                        continue
                eventos_encontrados.append(ev)
        if len(page_events) < 20:
            break

    eventos_encontrados.sort(key=lambda x: x.get("startTimestamp", 0), reverse=True)
    return eventos_encontrados[:5]

def buscar_estatisticas_completas(event_id):
    """Retorna dict {key: {'ALL': (home, away), '1ST': (home, away)}} para todas as estatísticas."""
    data = sofascore_get(f"/event/{event_id}/statistics")
    if not data:
        return None

    stats = {}
    for period_data in data.get("statistics", []):
        period = period_data.get("period")
        if period not in ("ALL", "1ST"):
            continue
        for group in period_data.get("groups", []):
            for item in group.get("statisticsItems", []):
                key = item.get("key")
                if not key:
                    continue
                hv = item.get("homeValue", 0)
                av = item.get("awayValue", 0)
                # Tenta converter para número
                try:
                    if isinstance(hv, str) and "%" in hv:
                        hv = float(hv.replace("%", ""))
                    else:
                        hv = float(hv) if hv not in (None, "") else 0
                    if isinstance(av, str) and "%" in av:
                        av = float(av.replace("%", ""))
                    else:
                        av = float(av) if av not in (None, "") else 0
                except (ValueError, TypeError):
                    hv, av = 0, 0
                if key not in stats:
                    stats[key] = {}
                stats[key][period] = (hv, av)
    return stats

# ----------------------------------------------------------
# Análises
# ----------------------------------------------------------

def coletar_dados_jogos(team_name, tournament_id):
    """Retorna lista de jogos com estatísticas completas + info do time."""
    team = buscar_time(team_name)
    if not team:
        return {"erro": f"Time *{team_name}* não encontrado. Tente o nome em inglês."}

    team_id = team["id"]
    team_name_real = team["name"]

    eventos = buscar_eventos(team_id, tournament_id)
    if not eventos:
        return {"erro": "⚠️ Não há jogos suficientes para este time neste campeonato."}

    games = []
    for ev in eventos:
        event_id = ev["id"]
        home_team = ev.get("homeTeam", {}).get("name", "?")
        away_team = ev.get("awayTeam", {}).get("name", "?")
        home_id = ev.get("homeTeam", {}).get("id")
        home_score = ev.get("homeScore", {}).get("current", "?")
        away_score = ev.get("awayScore", {}).get("current", "?")
        date_ts = ev.get("startTimestamp", 0)

        is_home = (home_id == team_id)
        opponent = away_team if is_home else home_team

        stats = buscar_estatisticas_completas(event_id)
        if not stats:
            continue

        games.append({
            "date_ts": date_ts,
            "home": home_team,
            "away": away_team,
            "score": f"{home_score}-{away_score}",
            "is_home": is_home,
            "opponent": opponent,
            "stats": stats,
        })

    if not games:
        return {"erro": "☹ Não foi possível obter estatísticas dos jogos."}

    return {
        "team_name": team_name_real,
        "team_id": team_id,
        "games": games,
    }

def calcular_media_mercado(games, sofascore_key):
    """Retorna (media_1T, media_total, lista_jogos_valores)."""
    vals_total = []
    vals_1t = []
    detalhes = []
    for g in games:
        stats = g["stats"]
        is_home = g["is_home"]
        item = stats.get(sofascore_key, {})

        v_total = None
        v_1t = None
        if "ALL" in item:
            hv, av = item["ALL"]
            v_total = hv if is_home else av
            vals_total.append(v_total)
        if "1ST" in item:
            hv, av = item["1ST"]
            v_1t = hv if is_home else av
            vals_1t.append(v_1t)

        detalhes.append({**g, "v_total": v_total, "v_1t": v_1t})

    media_total = round(sum(vals_total) / len(vals_total), 1) if vals_total else None
    media_1t = round(sum(vals_1t) / len(vals_1t), 1) if vals_1t else None
    return media_1t, media_total, detalhes

# ----------------------------------------------------------
# Teclados
# ----------------------------------------------------------

def teclado_ligas():
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(l["nome"], callback_data=f"league:{l['category_id']}")
        for l in LIGAS
    ]
    kb.add(*buttons)
    kb.add(InlineKeyboardButton("❌ Sair", callback_data="action:sair"))
    return kb

def teclado_torneios(torneios, category_id):
    kb = InlineKeyboardMarkup(row_width=1)
    for t in torneios:
        # callback_data tem limite de 64 bytes — usamos só o id
        kb.add(InlineKeyboardButton(t["nome"], callback_data=f"tour:{t['id']}"))
    kb.add(
        InlineKeyboardButton("⬅️ Voltar", callback_data="back:ligas"),
        InlineKeyboardButton("❌ Sair", callback_data="action:sair"),
    )
    return kb

def teclado_mercados():
    kb = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for m in MERCADOS:
        if m[0] == "panorama":
            continue
        buttons.append(InlineKeyboardButton(m[1], callback_data=f"merc:{m[0]}"))
    kb.add(*buttons)
    # Panorama em linha própria, destaque
    kb.add(InlineKeyboardButton("📊 PANORAMA GERAL (TUDO)", callback_data="merc:panorama"))
    kb.add(
        InlineKeyboardButton("⬅️ Voltar", callback_data="back:mercados_voltar"),
        InlineKeyboardButton("❌ Sair", callback_data="action:sair"),
    )
    return kb

def teclado_pos_resultado():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📈 Outro mercado", callback_data="action:outro_mercado"),
        InlineKeyboardButton("🔄 Outro time", callback_data="action:outro_time"),
    )
    kb.add(
        InlineKeyboardButton("🏠 Menu Principal", callback_data="action:menu"),
        InlineKeyboardButton("❌ Sair", callback_data="action:sair"),
    )
    return kb

# ----------------------------------------------------------
# Formatação
# ----------------------------------------------------------

def formatar_mercado(team_name, mercado_nome, unidade, media_1t, media_total, detalhes, campeonato_nome):
    linhas = []
    for g in detalhes:
        data_str = datetime.utcfromtimestamp(g["date_ts"]).strftime("%d/%m/%Y") if g["date_ts"] else "?"
        emoji = "🏠" if g["is_home"] else "✈️"
        v1t = g["v_1t"] if g["v_1t"] is not None else "N/D"
        vtot = g["v_total"] if g["v_total"] is not None else "N/D"
        score = g["score"].replace("-", " x ")
        linhas.append(
            f"{emoji} {data_str} — vs {g['opponent']} ({score}) → Total: *{vtot}* | 1ºT: *{v1t}*"
        )

    detalhes_txt = "\n".join(linhas)
    m1 = f"{media_1t} {unidade}" if media_1t is not None else "N/D"
    mt = f"{media_total} {unidade}" if media_total is not None else "N/D"

    return (
        f"⚽ *{team_name}*\n"
        f"📊 *{mercado_nome}*\n"
        f"_{campeonato_nome}_\n\n"
        f"📈 *MÉDIAS (últimos 5 jogos):*\n"
        f"  • 1º Tempo: *{m1}/jogo*\n"
        f"  • ⏱ Jogo Todo: *{mt}/jogo*\n\n"
        f"📋 *Detalhes por jogo:*\n{detalhes_txt}\n\n"
        f"_Dados via SofaScore — atualizado em tempo real_"
    )

def formatar_panorama(team_name, games, campeonato_nome):
    """Calcula média de TODOS os mercados e exibe um resumo geral."""
    linhas_1t = []
    linhas_tot = []

    for chave, nome, sofa_key, unidade in MERCADOS:
        if sofa_key is None:
            continue
        m1, mt, _ = calcular_media_mercado(games, sofa_key)
        u = unidade or ""
        m1_str = f"{m1}{u}" if m1 is not None else "N/D"
        mt_str = f"{mt}{u}" if mt is not None else "N/D"
        # Limpa nome (sem emoji duplicado)
        linhas_1t.append(f"{nome}: *{m1_str}*")
        linhas_tot.append(f"{nome}: *{mt_str}*")

    n_jogos = len(games)

    return (
        f"📊 *PANORAMA GERAL — {team_name}*\n"
        f"_{campeonato_nome}_\n"
        f"_Baseado nos últimos {n_jogos} jogos_\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ *MÉDIAS NO 1º TEMPO*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(linhas_1t) +
        f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
        f"⚽ *MÉDIAS NO JOGO TODO*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(linhas_tot) +
        f"\n\n_Dados via SofaScore_"
    )

# ----------------------------------------------------------
# Handlers
# ----------------------------------------------------------

@bot.message_handler(commands=["start"])
def cmd_start(message):
    if bloquear_se_nao_autorizado(message): return
    uid = message.from_user.id
    sessions[uid] = {}

    bot.send_message(
        message.chat.id,
        "⚽ *Bem-vindo ao Neural Pro!*\n\n"
        "Sou seu assistente de análise de futebol. Aqui você consegue ver as "
        "*médias de todos os principais mercados* dos últimos 5 jogos de qualquer time! 📊\n\n"
        "*📚 Como usar:*\n"
        "1️⃣ Escolha uma *liga* (Brasil, Inglaterra, Espanha...)\n"
        "2️⃣ Escolha o *campeonato* (Série A, Série B, Copa do Brasil...)\n"
        "3️⃣ Digite o *nome do time*\n"
        "4️⃣ Escolha o *mercado* que quer analisar\n"
        "5️⃣ Receba as *médias no 1º tempo e no jogo todo!*\n\n"
        "*🎯 Mercados disponíveis:*\n"
        "Finalizações, Chutes a gol, Escanteios, Faltas, Cartões, "
        "Posse de bola, Passes, Defesas, Gols, Ataques perigosos, "
        "Cruzamentos, Desarmes, Impedimentos e *PANORAMA GERAL* (tudo de uma vez)!\n\n"
        "Comandos: /start /menu /ajuda\n\n"
        "Vamos começar? 👇",
    )
    bot.send_message(message.chat.id, "🌐 *Escolha uma liga:*",
                     reply_markup=teclado_ligas())

@bot.message_handler(commands=["menu"])
def cmd_menu(message):
    if bloquear_se_nao_autorizado(message): return
    sessions[message.from_user.id] = {}
    bot.send_message(message.chat.id, "🌐 *Escolha uma liga:*",
                     reply_markup=teclado_ligas())

@bot.message_handler(commands=["ajuda"])
def cmd_ajuda(message):
    if bloquear_se_nao_autorizado(message): return
    bot.send_message(
        message.chat.id,
        "📖 *Como usar o Neural Pro:*\n\n"
        "1. /start ou /menu — ver as ligas\n"
        "2. Escolha liga → campeonato → digite o time → escolha o mercado\n"
        "3. Veja as médias dos últimos 5 jogos!\n\n"
        "_Dica: se o time não for encontrado, tente o nome em inglês._",
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("league:"))
def cb_league(call):
    if bloquear_se_nao_autorizado(call): return
    uid = call.from_user.id
    category_id = int(call.data.split(":")[1])

    bot.answer_callback_query(call.id, "Buscando campeonatos...")
    bot.edit_message_text(
        "⏳ Buscando campeonatos disponíveis...",
        call.message.chat.id, call.message.message_id,
    )

    torneios = buscar_torneios(category_id)
    if not torneios:
        bot.edit_message_text(
            "☹ Não encontrei campeonatos para esta liga.",
            call.message.chat.id, call.message.message_id,
            reply_markup=teclado_ligas(),
        )
        return

    # Salva mapa id->nome para recuperar depois
    sessions[uid] = {
        "category_id": category_id,
        "torneios_map": {t["id"]: t["nome"] for t in torneios},
    }

    bot.edit_message_text(
        "🏆 *Escolha o campeonato:*",
        call.message.chat.id, call.message.message_id,
        reply_markup=teclado_torneios(torneios, category_id),
        parse_mode="Markdown",
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("tour:"))
def cb_tournament(call):
    if bloquear_se_nao_autorizado(call): return
    uid = call.from_user.id
    tournament_id = int(call.data.split(":")[1])
    sess = sessions.get(uid, {})
    tournament_name = sess.get("torneios_map", {}).get(tournament_id, "Campeonato")

    sess.update({
        "tournament_id": tournament_id,
        "tournament_name": tournament_name,
        "awaiting_team": True,
    })
    sessions[uid] = sess

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"✅ *{tournament_name}* selecionado!\n\n"
        "🏆 *Agora digite o nome do time:*\n\n"
        "_(Ex: Flamengo, Real Madrid, Bayern...)_",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown",
    )

@bot.callback_query_handler(func=lambda c: c.data == "back:ligas")
def cb_back_ligas(call):
    if bloquear_se_nao_autorizado(call): return
    sessions[call.from_user.id] = {}
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🌐 *Escolha uma liga:*",
        call.message.chat.id, call.message.message_id,
        reply_markup=teclado_ligas(), parse_mode="Markdown",
    )

@bot.callback_query_handler(func=lambda c: c.data == "back:mercados_voltar")
def cb_back_merc(call):
    if bloquear_se_nao_autorizado(call): return
    """Volta para escolher outro time no mesmo campeonato."""
    uid = call.from_user.id
    sess = sessions.get(uid, {})
    sess["awaiting_team"] = True
    sessions[uid] = sess
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"🏆 *Digite o nome do time:*\n\n"
        f"_(Campeonato: {sess.get('tournament_name', '?')})_",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown",
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("merc:"))
def cb_mercado(call):
    if bloquear_se_nao_autorizado(call): return
    uid = call.from_user.id
    sess = sessions.get(uid, {})
    mercado_chave = call.data.split(":")[1]

    games_data = sess.get("games_data")
    if not games_data:
        bot.answer_callback_query(call.id, "Sessão expirada. Use /menu.")
        return

    bot.answer_callback_query(call.id, "Calculando...")
    team_name = games_data["team_name"]
    games = games_data["games"]
    campeonato = sess.get("tournament_name", "")

    if mercado_chave == "panorama":
        texto = formatar_panorama(team_name, games, campeonato)
    else:
        # encontra mercado
        mercado = next((m for m in MERCADOS if m[0] == mercado_chave), None)
        if not mercado:
            bot.send_message(call.message.chat.id, "❌ Mercado inválido.")
            return
        _, nome, sofa_key, unidade = mercado
        m1, mt, det = calcular_media_mercado(games, sofa_key)
        texto = formatar_mercado(team_name, nome, unidade, m1, mt, det, campeonato)

    # Telegram tem limite de 4096 chars
    if len(texto) > 4000:
        texto = texto[:3990] + "\n...(truncado)"

    bot.send_message(
        call.message.chat.id, texto,
        parse_mode="Markdown",
        reply_markup=teclado_pos_resultado(),
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("action:"))
def cb_action(call):
    if bloquear_se_nao_autorizado(call): return
    uid = call.from_user.id
    action = call.data.split(":")[1]
    bot.answer_callback_query(call.id)

    if action == "menu":
        sessions[uid] = {}
        bot.send_message(
            call.message.chat.id, "🌐 *Escolha uma liga:*",
            reply_markup=teclado_ligas(), parse_mode="Markdown",
        )
    elif action == "outro_time":
        sess = sessions.get(uid, {})
        sess["awaiting_team"] = True
        sess.pop("games_data", None)
        sessions[uid] = sess
        bot.send_message(
            call.message.chat.id,
            f"🏆 *Qual time agora?*\n\n_(Campeonato: {sess.get('tournament_name', '?')})_",
            parse_mode="Markdown",
        )
    elif action == "outro_mercado":
        sess = sessions.get(uid, {})
        if not sess.get("games_data"):
            bot.send_message(call.message.chat.id, "Use /menu para começar.")
            return
        bot.send_message(
            call.message.chat.id,
            f"📊 *Escolha outro mercado para {sess['games_data']['team_name']}:*",
            reply_markup=teclado_mercados(), parse_mode="Markdown",
        )
    elif action == "sair":
        sessions.pop(uid, None)
        bot.send_message(
            call.message.chat.id,
            "👋 Até logo! Use /start quando quiser voltar. ⚽",
        )

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if bloquear_se_nao_autorizado(message): return
    uid = message.from_user.id
    sess = sessions.get(uid, {})

    if not sess.get("awaiting_team"):
        bot.send_message(
            message.chat.id, "Use /start ou /menu para começar! ⚽"
        )
        return

    team_name = message.text.strip()
    tournament_id = sess.get("tournament_id")

    bot.send_message(
        message.chat.id,
        f"🔍 Buscando dados do *{team_name}*... aguarde!",
        parse_mode="Markdown",
    )

    dados = coletar_dados_jogos(team_name, tournament_id)

    if "erro" in dados:
        bot.send_message(message.chat.id, f"❌ {dados['erro']}", parse_mode="Markdown")
        return

    # Guarda os dados na sessão para o usuário escolher quantos mercados quiser
    sess["games_data"] = dados
    sess["awaiting_team"] = False
    sessions[uid] = sess

    bot.send_message(
        message.chat.id,
        f"✅ Dados de *{dados['team_name']}* coletados! "
        f"({len(dados['games'])} jogos analisados)\n\n"
        f"📊 *Escolha o mercado para ver as médias:*",
        parse_mode="Markdown",
        reply_markup=teclado_mercados(),
    )

# ----------------------------------------------------------
# Main
# ----------------------------------------------------------


if __name__ == "__main__":
    print("🤖 Neural Pro Bot iniciado! Pressione Ctrl+C para parar.")
    print("📊 Mercados ativos:", len(MERCADOS) - 1, "+ Panorama Geral")
    bot.infinity_polling()
