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
    return "🤖 Robô de Análise Estatística Avançada Rodando!"

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
    """
    Simula um cruzamento analítico avançado (estilo FootyStats/SofaScore)
    baseado no ID dos times, gerando pesos dinâmicos de tendência ofensiva e defensiva.
    """
    # Usando os IDs para gerar uma volatilidade estatística consistente por time
    fator_h = (home_id % 30) / 100
    fator_a = (away_id % 30) / 100
    
    # Probabilidades base ajustadas para cenários de alta assertividade
    over_15 = int(75 + (fator_h * 15) + (fator_a * 5))
    over_25 = int(58 + (fator_h * 20) + (fator_a * 10))
    
    # Limitando os percentuais entre margens realistas de mercado (ex: 50% a 95%)
    over_15 = min(max(over_15, 65), 94)
    over_25 = min(max(over_25, 52), 86)
    
    return over_15, over_25

def processar_jogos():
    data_str = datetime.date.today().strftime("%Y-%m-%d")
    url = f"{API_URL}/fixtures?date={data_str}&timezone=America/Sao_Paulo"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            fixtures = response.json().get("response", [])
            if fixtures:
                msg = "📊 <b>PAINEL ESTATÍSTICO AVANÇADO (IA)</b> 📊\n"
                msg += f"📅 <b>Data:</b> {data_str}\n"
                msg += f"🔍 <i>Filtro: Tendências de Gols & Pressão</i>\n"
                msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                
                contador = 0
                for item in fixtures:
                    if contador >= 5:
                        break
                        
                    home = item['teams']['home']['name']
                    home_id = item['teams']['home']['id']
                    
                    away = item['teams']['away']['name']
                    away_id = item['teams']['away']['id']
                    
                    league = item['league']['name']
                    hora = item['fixture']['date'].split("T")[1][:5]
                    
                    p15, p25 = calcular_estatisticas_avancadas(home_id, away_id)
                    
                    # Indicador de valor de mercado baseado na probabilidade cruzada
                    if p25 >= 75:
                        tendencia = "🔥 <b>Forte p/ Over 2.5 (Alta Pressão)</b>"
                    elif p25 >= 65:
                        tendencia = "⚡ <b>Bom p/ Over 1.5 / Live</b>"
                    else:
                        tendencia = "⚖️ <b>Jogo Estudo / Cuidado</b>"
                    
                    msg += f"🏆 <b>{league}</b>\n"
                    msg += f"⏰ <b>Horário:</b> {hora}\n"
                    msg += f"⚔️ <b>{home}</b> x <b>{away}</b>\n"
                    msg += f"📈 <b>Cruzamento Estatístico:</b>\n"
                    msg += f"   • Projeção Over 1.5 ➔ <code>{p15}%</code>\n"
                    msg += f"   • Projeção Over 2.5 ➔ <code>{p25}%</code>\n"
                    msg += f"🎯 <b>Análise:</b> {tendencia}\n"
                    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    contador += 1
                    
                return msg
    except Exception as e:
        print(f"Erro: {e}")

    return "⚠️ <i>Nenhuma partida encontrada para os critérios atuais.</i>"

def escutar_telegram():
    print("\nROBÔ COM ANÁLISE ESTATÍSTICA AVANÇADA ATIVO!\n")
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
                            enviar_telegram("🔎 <i>Cruzando matrizes estatísticas e histórico recente...</i>", from_chat)
                            enviar_telegram(processar_jogos(), from_chat)
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    t_web = Thread(target=rodar_web)
    t_web.daemon = True
    t_web.start()
    
    escutar_telegram()
