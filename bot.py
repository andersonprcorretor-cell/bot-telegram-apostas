def processar_jogos():
    data_str = datetime.date.today().strftime("%Y-%m-%d")
    url = f"{API_URL}/fixtures?date={data_str}&timezone=America/Sao_Paulo"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            fixtures = response.json().get("response", [])
            if fixtures:
                msg = "⚽ <b>PARTIDAS EM DESTAQUE (ANÁLISE INTELIGENTE)</b> ⚽\n"
                msg += f"📅 <b>Data:</b> {data_str}\n\n"
                
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
                    
                    if p25 >= 75:
                        tendencia = "🔥 <b>Forte p/ Over 2.5 (Alta Pressão)</b>"
                    elif p25 >= 65:
                        tendencia = "⚡ <b>Bom p/ Over 1.5 / Live</b>"
                    else:
                        tendencia = "⚖️ <b>Jogo Estudo / Cuidado</b>"
                    
                    msg += f"🏆 <b>{league}</b> | ⏰ <b>{hora}</b>\n"
                    msg += f"⚔️ <b>{home}</b> x <b>{away}</b>\n"
                    msg += f"⚽ <b>Over 1.5:</b> <code>{p15}%</code> | {tendencia}\n"
                    msg += f"⚽ <b>Over 2.5:</b> <code>{p25}%</code>\n\n"
                    contador += 1
                
                if contador > 0:
                    return msg
            
            return "⚠️ <i>Nenhuma partida encontrada para os critérios atuais.</i>"

    except Exception as e:
        print(f"Erro: {e}")
        return f"⚠️ <i>Erro ao processar as partidas: {e}</i>"
