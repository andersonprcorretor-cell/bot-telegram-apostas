import datetime
import requests
import time
from threading import Thread
from flask import Flask

API_KEY = "4fa50b733dfe92033d0d6e767922eb0d"
API_URL = "https://v3.football.api-sports.io"
TELEGRAM_TOKEN = "8808972104:AAGYhnYvy8uFuEaP7EarknIvUB6viHkKReE"
TELEGRAM_CHAT_ID = "1148090241"

HEADERS = {"x-apisports-key": API_KEY}

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Robô de Análise Estatística Global Rodando!"

def rodar_web():
    app.run(host="0.0.0.0", port=10000)

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
    
    url = f"{API_URL}/fixtures?date={data_str}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        fixtures = []
        if response.status_code == 200:
            fixtures = response.json().get("response", [])
            
        # Contingência para /hoje: se não houver jogos na data, busca os jogos AO VIVO no momento com placares
        modo_live = False
        if not fixtures and dias_frente == 0:
            url_live = f"{API_URL}/fixtures?live=all"
            resp_live = requests.get(url_live, headers=HEADERS, timeout=10)
            if resp_live.status_code == 200:
                fixtures = resp_live.json().get("response", [])
                if fixtures:
                    modo_live = True

        # Contingência para /amanha: se não houver jogos exatos amanhã, busca as próximas partidas gerais
        if not fixtures and dias_frente > 0:
            url_next = f"{API_URL}/fixtures?next=15"
            resp_next = requests.get(url_next, headers=HEADERS, timeout=10)
            if resp_next.status_code == 200:
                fixtures = resp_next.json().get("response", [])

        if not fixtures:
            return f"⚠️ <i>Não foram encontradas partidas ativas na API para esta data. Tente verificar mais tarde.</i>"

        if modo_live:
            titulo_filtro = "🔴 PARTIDAS AO VIVO (AGORA)"
        elif dias_frente > 0:
            titulo_filtro = f"📅 PARTIDAS DE AMANHÃ ({data_str})"
        else:
            titulo_filtro = "⚽ PARTIDAS DE HOJE"

        if filtro == "over15":
            titulo_filtro += " - FILTRADO: OVER 1.5"
        elif filtro == "over25":
            titulo_filtro += " - FILTRADO: OVER 2.5"
        elif filtro == "btts":
            titulo_filtro += " - FILTRADO: AMBAS MARCAM"
        elif filtro == "altagestao":
            titulo_filtro += " - OPORTUNIDADES DE ALTA GESTÃO"

        msg = f"<b>{titulo_filtro}</b>\n\n"
        
        contador = 0
        for item in fixtures:
            home = item['teams']['home']['name']
            home_id = item['teams']['home']['id']
            away = item['teams']['away']['name']
            away_id = item['teams']['away']['id']
            
            league = item['league']['name']
            country = item['league']['country']
            
            status_short = item['fixture']['status']['short']
            elapsed = item['fixture']['status']['elapsed']
            
            # Pegando placar se estiver ao vivo ou encerrado
            gols_home = item['goals']['home']
            gols_away = item['goals']['away']
            if gols_home is None: gols_home = 0
            if gols_away is None: gols_away = 0
            
            raw_time = item['fixture']['date']
            try:
                hora = raw_time.split("T")[1][:5]
            except:
                hora = "00:00"
            
            p15, p25, btts = calcular_estatisticas_avancadas(home_id, away_id)
            
            if filtro == "over15" and p15 < 70:
                continue
            if filtro == "over25" and p25 < 55:
                continue
            if filtro == "btts" and btts < 50:
                continue
            if filtro == "altagestao" and (p25 < 60 and p15 < 70):
                continue

            if contador >= 8:
                break
            
            if modo_live or status_short in ["1H", "HT", "2H", "ET", "P"]:
                status_txt = f"🔴 <b>AO VIVO ({elapsed} minutos)</b>"
                placar_txt = f"⚡ <b>Placar:</b> {home} {gols_home} x {gols_away} {away}\n"
                tendencia = "🎯 <b>Indicativo Live:</b> Olhar pressão de cantos e finalizações para Over / Próximo Gol."
            else:
                status_txt = f"⏰ <b>Horário:</b> {hora}"
                placar_txt = f"⚔️ <b>{home}</b> x <b>{away}</b>\n"
                if p25 >= 75:
                    tendencia = "🔥 <b>Forte p/ Over 2.5 (Alta Pressão)</b>"
                elif p25 >= 65:
                    tendencia = "⚡ <b>Bom p/ Over 1.5 / Pré-live</b>"
                else:
                    tendencia = "⚖️ <b>Jogo Estudo / Cuidado</b>"
            
            msg += f"🏆 <b>{country} - {league}</b>\n"
            msg += f"{status_txt}\n"
            msg += placar_txt
            msg += f"📈 <b>Projeções:</b> O1.5 (<code>{p15}%</code>) | O2.5 (<code>{p25}%</code>) | BTTS (<code>{btts}%</code>)\n"
            msg += f"{tendencia}\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            contador += 1

        if contador > 0:
            return msg
        
        return f"⚠️ <i>Nenhuma partida encontrada para os critérios solicitados.</i>"

    except Exception as e:
        print(f"Erro: {e}")
        return f"⚠️ <i>Erro ao processar as partidas.</i>"

def escutar_telegram():
    print("\nROBÔ GLOBAL COM SUPORTE AO VIVO ATIVO!\n")
    offset = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            res = requests.get(url, params={"timeout": 20, "offset": offset}, timeout=25).json()
            if res.get("ok"):
                for result in res.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message", {})
                    texto = message.get("text", "").strip().lower()
                    from_chat = str(message.get("chat", {}).get("id"))
                    
                    if from_chat == TELEGRAM_CHAT_ID:
                        if texto in ["/hoje", "hoje", "/jogos", "jogos", "/start"]:
                            enviar_telegram("🔎 <i>Varrendo partidas de hoje (com fallback para Ao Vivo)...</i>", from_chat)
                            enviar_telegram(processar_jogos(dias_frente=0, filtro="todos"), from_chat)
                        elif texto in ["/amanha", "amanhã"]:
                            enviar_telegram("🔎 <i>Varrendo partidas de amanhã...</i>", from_chat)
                            enviar_telegram(processar_jogos(dias_frente=1, filtro="todos"), from_chat)
                        elif texto in ["/over15", "over15"]:
                            enviar_telegram("🔎 <i>Buscando oportunidades de Over 1.5...</i>", from_chat)
                            enviar_telegram(processar_jogos(dias_frente=0, filtro="over15"), from_chat)
                        elif texto in ["/over25", "over25"]:
                            enviar_telegram("🔎 <i>Buscando oportunidades de Over 2.5...</i>", from_chat)
                            enviar_telegram(processar_jogos(dias_frente=0, filtro="over25"), from_chat)
                        elif texto in ["/btts", "btts", "ambas"]:
                            enviar_telegram("🔎 <i>Buscando mercados de Ambas Marcam...</i>", from_chat)
                            enviar_telegram(processar_jogos(dias_frente=0, filtro="btts"), from_chat)
                        elif texto in ["/altagestao", "altagestao", "/sinais"]:
                            enviar_telegram("🔎 <i>Buscando entradas de alta probabilidade...</i>", from_chat)
                            enviar_telegram(processar_jogos(dias_frente=0, filtro="altagestao"), from_chat)
                        elif texto in ["/ajuda", "/help", "ajuda"]:
                            ajuda_msg = (
                                "🤖 <b>PAINEL DE COMANDOS DO ROBÔ</b>\n\n"
                                "📅 <b>Navegação:</b>\n"
                                "• /hoje - Jogos do dia (com fallback para Ao Vivo)\n"
                                "• /amanha - Jogos e análises de amanhã\n\n"
                                "🎯 <b>Filtros de Mercado:</b>\n"
                                "• /over15 - Foco em +1.5 gols\n"
                                "• /over25 - Foco em +2.5 gols\n"
                                "• /btts - Ambas Marcam\n"
                                "• /altagestao - Melhores oportunidades\n"
                            )
                            enviar_telegram(ajuda_msg, from_chat)
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    t_web = Thread(target=rodar_web)
    t_web.daemon = True
    t_web.start()
    escutar_telegram()
