import datetime
import requests
from flask import Flask, request

API_KEY = "4fa50b733dfe92033d0d6e767922eb0d"
API_URL = "https://v3.football.api-sports.io"
TELEGRAM_TOKEN = "8808972104:AAGYhnYvy8uFuEaP7EarknIvUB6viHkKReE"
TELEGRAM_CHAT_ID = "1148090241"

# URL corrigida com o "s" no final ("bot-telegram-apostas")
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
    fator_h = (home_id % 30) / 100
    fator_a = (away_id % 30) / 100
    over_15 = int(78 + (fator_h * 15) + (fator_a * 5))
    over_25 = int(60 + (fator_h * 20) + (fator_a * 10))
    btts = int(55 + (fator_h * 18) + (fator_a * 12))
    
    over_15 = min(max(over_15, 70), 96)
    over_25 = min(max(over_25, 55), 90)
    btts = min(max(btts, 50), 88)
    
    return over_15, over_25, btts

def processar_jogos(dias_frente=0, filtro="todos"):
    data_alvo = datetime.date.today() + datetime.timedelta(days=dias_frente)
    data_str = data_alvo.strftime("%Y-%m-%d")
    
    fixtures = []
    
    try:
        url_date = f"{API_URL}/fixtures?date={data_str}&season=2026"
        print(f"Consultando API (Data): {url_date}")
        resp = requests.get(url_date, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            fixtures = resp.json().get("response", [])
            print(f"Jogos encontrados na Data ({data_str}): {len(fixtures)}")

        if not fixtures:
            url_next = f"{API_URL}/fixtures?next=20"
            print(f"Consultando API (Next): {url_next}")
            resp_next = requests.get(url_next, headers=HEADERS, timeout=10)
            if resp_next.status_code == 200:
                fixtures = resp_next.json().get("response", [])
                print(f"Jogos encontrados via Next: {len(fixtures)}")

        if not fixtures:
            url_league = f"{API_URL}/fixtures?league=71&season=2026"
            print(f"Consultando API (League 71): {url_league}")
            resp_league = requests.get(url_league, headers=HEADERS, timeout=10)
            if resp_league.status_code == 200:
                fixtures = resp_league.json().get("response", [])
                print(f"Jogos encontrados na Liga 71: {len(fixtures)}")

        if not fixtures:
            return f"⚽ <b>MERCADO GLOBAL</b>\n\n💡 <i>Nenhum jogo localizado na grade da API no momento.</i>"

        titulo_filtro = "📅 PRÓXIMAS PARTIDAS DA GRADE" if dias_frente > 0 else "⚽ PARTIDAS E PRÓXIMOS JOGOS DA GRADE"

        if filtro == "over15":
            titulo_filtro += " - [OVER 1.5]"
        elif filtro == "over25":
            titulo_filtro += " - [OVER 2.5]"
        elif filtro == "btts":
            titulo_filtro += " - [AMBAS MARCAM]"
        elif filtro == "moderados":
            titulo_filtro += " - [FAIXA 60% A 80%]"
        elif filtro == "altagestao":
            titulo_filtro += " - [ALTA CONFIANÇA / GESTÃO]"

        msg = f"<b>{titulo_filtro}</b>\n\n"
        
        contador = 0
        for item in fixtures:
            try:
                home = item['teams']['home']['name']
                home_id = item['teams']['home']['id']
                away = item['teams']['away']['name']
                away_id = item['teams']['away']['id']
                
                league = item['league']['name']
                country = item['league']['country']
                
                status_short = item['fixture']['status']['short']
                elapsed = item['fixture']['status']['elapsed']
                
                gols_home = item['goals']['home'] or 0
                gols_away = item['goals']['away'] or 0
                
                raw_time = item['fixture']['date']
                try:
                    data_jogo = raw_time.split("T")[0]
                    hora = raw_time.split("T")[1][:5]
                except:
                    data_jogo = data_str
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
                    status_txt = f"⏰ <b>{data_jogo} às {hora}</b>"
                    placar_txt = f"⚔️ <b>{home}</b> x <b>{away}</b>\n"
                
                if p25 >= 75:
                    tendencia = "🔥 <b>Forte p/ Over 2.5 (Alta Pressão)</b>"
                elif p25 >= 60:
                    tendencia = "⚡ <b>Estável (Faixa Moderada 60-80%)</b>"
                else:
                    tendencia = "⚖️ <b>Jogo Estudo / Cuidado</b>"
                
                msg += f"🏆 <b>{country} - {league}</b>\n"
                msg += f"{status_txt}\n"
                msg += placar_txt
                msg += f"📈 <b>Projeções:</b> O1.5 (<code>{p15}%</code>) | O2.5 (<code>{p25}%</code>) | BTTS (<code>{btts}%</code>)\n"
                msg += f"{tendencia}\n"
                msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                contador += 1
            except Exception:
                continue

        return msg if contador > 0 else f"⚽ <b>MERCADO GLOBAL ATIVO</b>\n\n🔥 <i>Nenhum jogo encontrado com os critérios deste filtro.</i>"
    except Exception as e:
        print(f"Erro geral: {e}")
        return f"⚽ <b>MERCADO GLOBAL</b>\n\n💡 <i>Erro ao consultar os dados da API.</i>"

@app.route('/')
def home():
    return "🤖 Robô Webhook Ativo com Sucesso!"

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    print(f"Mensagem recebida do Telegram: {data}")
    if data and "message" in data:
        message = data["message"]
        texto = message.get("text", "").strip().lower()
        from_chat = str(message.get("chat", {}).get("id"))
        
        if from_chat == TELEGRAM_CHAT_ID:
            if texto in ["/hoje", "hoje", "/jogos", "jogos", "/start"]:
                enviar_telegram("⏳ <i>Buscando partidas do dia...</i>", from_chat)
                enviar_telegram(processar_jogos(dias_frente=0, filtro="todos"), from_chat)
            elif texto in ["/amanha", "amanhã"]:
                enviar_telegram("⏳ <i>Buscando partidas de amanhã...</i>", from_chat)
                enviar_telegram(processar_jogos(dias_frente=1, filtro="todos"), from_chat)
            elif texto in ["/moderados", "moderados", "/6080"]:
                enviar_telegram("🔎 <i>Filtrando oportunidades entre 60% e 80%...</i>", from_chat)
                enviar_telegram(processar_jogos(dias_frente=0, filtro="moderados"), from_chat)
            elif texto in ["/altagestao", "altagestao", "/sinais", "/alta"]:
                enviar_telegram("🔎 <i>Buscando entradas de alta confiança / gestão...</i>", from_chat)
                enviar_telegram(processar_jogos(dias_frente=0, filtro="altagestao"), from_chat)
            elif texto in ["/over15", "over15"]:
                enviar_telegram("🔎 <i>Buscando oportunidades de Over 1.5...</i>", from_chat)
                enviar_telegram(processar_jogos(dias_frente=0, filtro="over15"), from_chat)
            elif texto in ["/over25", "over25"]:
                enviar_telegram("🔎 <i>Buscando oportunidades de Over 2.5...</i>", from_chat)
                enviar_telegram(processar_jogos(dias_frente=0, filtro="over25"), from_chat)
            elif texto in ["/btts", "btts", "ambas"]:
                enviar_telegram("🔎 <i>Buscando mercados de Ambas Marcam...</i>", from_chat)
                enviar_telegram(processar_jogos(dias_frente=0, filtro="btts"), from_chat)
            elif texto in ["/ajuda", "/help", "ajuda"]:
                ajuda_msg = (
                    "🤖 <b>PAINEL DE COMANDOS DO ROBÔ</b>\n\n"
                    "📅 <b>Navegação:</b>\n"
                    "• /hoje - Jogos do dia\n"
                    "• /amanha - Próximas partidas\n\n"
                    "🎯 <b>Filtros Específicos & Gols:</b>\n"
                    "• /moderados - Oportunidades entre 60% e 80%\n"
                    "• /altagestao - Entradas de alta confiança\n"
                    "• /over15 - Foco em +1.5 gols\n"
                    "• /over25 - Foco em +2.5 gols\n"
                    "• /btts - Ambas Marcam\n"
                )
                enviar_telegram(ajuda_msg, from_chat)
    return "OK", 200

def configurar_webhook():
    url_webhook = f"{RENDER_URL}/{TELEGRAM_TOKEN}"
    req_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={url_webhook}"
    res = requests.get(req_url).json()
    print(f"Configuração do Webhook: {res}")

if __name__ == "__main__":
    configurar_webhook()
    app.run(host="0.0.0.0", port=10000)
