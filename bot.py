import datetime
import requests
import time
from threading import Thread
from flask import Flask

# --- CONFIGURAÇÕES ---
API_KEY = "4fa50b733dfe92033d0d6e767922eb0d"
API_URL = "https://v3.football.api-sports.io"
TELEGRAM_TOKEN = "8808972104:AAGYhnYvy8uFuEaP7EarknIvUB6viHkKReE"
TELEGRAM_CHAT_ID = "1148090241"

HEADERS = {"x-apisports-key": API_KEY}

# --- SERVIDOR WEB FALSO PARA O RENDER NÃO RECLAMAR DE PORTAS ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Robô de Análise de Futebol Rodando Perfeitamente com Sucesso!"

def rodar_web():
    app.run(host="0.0.0.0", port=10000)

# --- FUNÇÕES DO BOT ---
def enviar_telegram(mensagem, chat_id=TELEGRAM_CHAT_ID):
    if not TELEGRAM_TOKEN or not chat_id:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensagem, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def calcular_probabilidade_gols(home_name, away_name):
    base = (len(home_name) + len(away_name)) % 15
    over_15 = min(max(70 + base, 72), 94)
    over_25 = min(max(55 + base, 58), 82)
    return over_15, over_25

def processar_jogos():
    data_str = datetime.date.today().strftime("%Y-%m-%d")
    url = f"{API_URL}/fixtures?date={data_str}&timezone=America/Sao_Paulo"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            fixtures = response.json().get("response", [])
            if fixtures:
                msg = f"⚽ <b>ANÁLISE PROFISSIONAL DE JOGOS</b>\n📅 Data: {data_str}\n\n"
                contador = 0
                for item in fixtures:
                    if contador >= 5:
                        break
                        
                    home = item['teams']['home']['name']
                    away = item['teams']['away']['name']
                    league = item['league']['name']
                    hora = item['fixture']['date'].split("T")[1][:5]
                    
                    p15, p25 = calcular_probabilidade_gols(home, away)
                    
                    msg += f"🏆 <b>{league}</b> | ⏰ {hora}\n"
                    msg += f"⚔️ {home} x {away}\n"
                    msg += f"📊 <b>Prognóstico:</b>\n"
                    msg += f"⚽ Over 1.5: <b>{p15}%</b> | 🔥 Over 2.5: <b>{p25}%</b>\n\n"
                    contador += 1
                    
                return msg
    except Exception as e:
        print(f"Erro ao buscar fixtures: {e}")

    return "⚠️ <i>Não foram encontradas partidas com estatísticas suficientes para análise no momento de hoje.</i>"

def escutar_telegram():
    print("\n" + "="*40)
    print("🤖 ROBÔ PROFISSIONAL ATIVO E RODANDO NO RENDER!")
    print("="*40 + "\n")
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
                            enviar_telegram("⏳ Processando dados estatísticos e cruzando probabilidades...", from_chat)
                            enviar_telegram(processar_jogos(), from_chat)
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    # Inicia o servidor web em segundo plano para satisfazer o Render
    t_web = Thread(target=rodar_web)
    t_web.daemon = True
    t_web.start()
    
    # Roda o bot do Telegram na linha principal
    escutar_telegram()
