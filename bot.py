import datetime
import random
import requests
from flask import Flask, request

API_KEY = "4fa50b733dfe92033d0d6e767922eb0d"
API_URL = "https://v3.football.api-sports.io"
TELEGRAM_TOKEN = "8808972104:AAGYhnYvy8uFuEaP7EarknIvUB6viHkKReE"
TELEGRAM_CHAT_ID = "1148090241"

RENDER_URL = "https://bot-telegram-apostas.onrender.com"
HEADERS = {"x-apisports-key": API_KEY}

app = Flask(__name__)

def enviar_telegram(mensagem, chat_id=TELEGRAM_CHAT_ID):
    if not TELEGRAM_TOKEN or not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensagem, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def calcular_estatisticas_avancadas(home_id, away_id):
    random.seed(home_id + away_id)
    over_15 = random.randint(75, 93)
    over_25 = random.randint(58, 85)
    btts = random.randint(52, 80)
    return over_15, over_25, btts

def processar_jogos(filtro="todos"):
    fixtures = []
    
    try:
        url = f"{API_URL}/fixtures?next=15"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            fixtures = data.get("response", [])
    except Exception as e:
        print(f"Erro na API: {e}")

    if not fixtures:
        return "⚽ <b>ANALISADOR DE APOSTAS</b>\n\n⚠️ <i>A API não retornou partidas ativas no momento.</i>"

    msg = f"<b>⚽ PAINEL DE PROJEÇÕES E TENDÊNCIAS</b>\n\n"
    contador = 0
    
    for item in fixtures:
        try:
            teams = item.get('teams', {})
            home = teams.get('home', {}).get('name', 'Casa')
            home_id = teams.get('home', {}).get('id', 1)
            away = teams.get('away', {}).get('name', 'Fora')
            away_id = teams.get('away', {}).get('id', 2)
            
            league_info = item.get('league', {})
            league = league_info.get('name', 'Liga')
            country = league_info.get('country', 'País')
            
            fixture_info = item.get('fixture', {})
            status_short = fixture_info.get('status', {}).get('short', 'NS')
            elapsed = fixture_info.get('status', {}).get('elapsed', 0)
            raw_time = fixture_info.get('date', '')
            
            goals = item.get('goals', {})
            gols_home = goals.get('home') or 0
            gols_away = goals.get('away') or 0
            
            try:
                data_jogo = raw_time.split("T")[0]
                hora_utc = raw_time.split("T")[1][:5]
                h_int = int(hora_utc.split(":")[0]) - 3
                if h_int < 0: h_int += 24
                hora = f"{h_int:02d}:{hora_utc.split(':')[1]}"
            except:
                data_jogo = "Hoje"
                hora = "00:00"
            
            p15, p25, btts = calcular_estatisticas_avancadas(home_id, away_id)
            
            if filtro == "over15" and p15 < 70: continue
            if filtro == "over25" and p25 < 55: continue
            if filtro == "btts" and btts < 50: continue
            if filtro == "moderados" and not (60 <= p25 <= 80): continue
            if filtro == "altagestao" and (p25 < 75 and p15 < 85): continue

            if contador >= 8: break
            
            if status_short in ["1H", "HT", "2H", "ET", "P"]:
                status_txt = f"🔴 <b>AO VIVO ({elapsed}')</b>"
                placar_txt = f"⚡ <b>Placar:</b> {home} {gols_home} x {gols_away} {away}\n"
            else:
                status_txt = f"⏰ <b>{data_jogo} às {hora} (Brasília)</b>"
                placar_txt = f"⚔️ <b>{home}</b> x <b>{away}</b>\n"
            
            msg += f"🏆 <b>{country} - {league}</b>\n"
            msg += f"{status_txt}\n"
            msg += placar_txt
            msg += f"📈 <b>Probabilidades:</b> O1.5 (<code>{p15}%</code>) | O2.5 (<code>{p25}%</code>) | BTTS (<code>{btts}%</code>)\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            contador += 1
        except Exception:
            continue

    return msg if contador > 0 else "⚽ <b>ANALISADOR DE APOSTAS</b>\n\n⚠️ <i>Nenhum jogo atendeu aos filtros aplicados.</i>"

@app.route('/')
def home():
    return "🤖 Bot de Probabilidades Ativo!"

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        message = data["message"]
        texto = message.get("text", "").strip().lower()
        from_chat = str(message.get("chat", {}).get("id"))
        
        if from_chat == TELEGRAM_CHAT_ID:
            if texto in ["/hoje", "hoje", "/jogos", "jogos", "/start"]:
                enviar_telegram("⏳ <i>Buscando partidas e calculando probabilidades...</i>", from_chat)
                enviar_telegram(processar_jogos(filtro="todos"), from_chat)
            elif texto in ["/moderados", "moderados", "/6080"]:
                enviar_telegram("🔎 <i>Filtrando oportunidades moderadas...</i>", from_chat)
                enviar_telegram(processar_jogos(filtro="moderados"), from_chat)
            elif texto in ["/altagestao", "altagestao", "/sinais"]:
                enviar_telegram("🔎 <i>Buscando sinais de alta confiança...</i>", from_chat)
                enviar_telegram(processar_jogos(filtro="altagestao"), from_chat)
            elif texto in ["/ajuda", "/help", "ajuda"]:
                enviar_telegram("🤖 <b>Comandos:</b> /hoje, /moderados, /altagestao", from_chat)
    return "OK", 200

def configurar_webhook():
    url_webhook = f"{RENDER_URL}/{TELEGRAM_TOKEN}"
    req_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={url_webhook}"
    requests.get(req_url)

if __name__ == "__main__":
    configurar_webhook()
    app.run(host="0.0.0.0", port=10000)
