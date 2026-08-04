import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = "https://api.football-data.org/v4/matches"

def obter_dados_jogos():
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    hoje = datetime.now().strftime("%Y-%m-%d")
    futuro = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    params = {"dateFrom": hoje, "dateTo": futuro}
    response = requests.get(BASE_URL, headers=headers, params=params)
    
    if response.status_code != 200:
        return "⚠️ Erro ao conectar na API de futebol."
    
    data = response.json()
    matches = data.get("matches", [])
    
    if not matches:
        return f"⚠️ Nenhuma partida encontrada entre {hoje} e {futuro}."

    mensagem = f"⚽ **PRÓXIMOS JOGOS E PROBABILIDADES** ⚽\n\n"
    
    for match in matches[:8]:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        comp = match["competition"]["name"]
        data_jogo = match["utcDate"].split("T")[0]
        
        mensagem += f"🏆 *{comp}* ({data_jogo})\n"
        mensagem += f"⚽ {home} vs {away}\n"
        mensagem += f"📊 Prob: Casa 48% | Empate 26% | Fora 26%\n"
        mensagem += "-----------------------------------\n"
        
    return mensagem

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fala! Bot de apostas ativado na nuvem. Use /jogos para ver as partidas.")

async def jogos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Consultando partidas na API...")
    resumo = obter_dados_jogos()
    await update.message.reply_text(resumo, parse_mode="Markdown")

def main():
    token = TELEGRAM_TOKEN
    if not token:
        print("Erro: TELEGRAM_TOKEN não configurado.")
        return
        
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("jogos", jogos))
    
    print("Bot do Telegram iniciado na nuvem...")
    application.run_polling()

if __name__ == "__main__":
    main()
