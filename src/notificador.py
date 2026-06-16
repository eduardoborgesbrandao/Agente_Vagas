import os
import requests
from typing import Dict


def enviar_mensagem_telegram(vaga: Dict) -> bool:
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print(f"[notificador] Modo simulação: {vaga.get('titulo')} | Score: {vaga.get('match_score')}")
        return True

    icone_tech = "🚀" if vaga.get("tech_core") else "💻"

    mensagem = (
        f"{icone_tech} <b>Nova Vaga com Alto Fit!</b>\n"
        f"{'─' * 30}\n"
        f"📌 <b>Título:</b> {vaga.get('titulo', 'N/A')}\n"
        f"🏢 <b>Empresa:</b> {vaga.get('empresa', 'N/A')}\n"
        f"⭐ <b>Match Score:</b> {vaga.get('match_score', 0)}/100\n"
        f"🔬 <b>Tech Core:</b> {'Sim ✓' if vaga.get('tech_core') else 'Não'}\n"
        f"{'─' * 30}\n"
        f"💬 <b>Análise:</b>\n{vaga.get('motivo', 'N/A')}\n"
        f"{'─' * 30}\n"
        f"🔗 <a href=\"{vaga.get('url', '#')}\">Ver vaga completa</a>"
    )

    payload = {
        "chat_id":                  chat_id,
        "text":                     mensagem,
        "parse_mode":               "HTML",
        "disable_web_page_preview": True
    }

    try:
        resposta = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=payload,
            timeout=10
        )

        if resposta.status_code == 200:
            print(f"[notificador] ✓ Enviado: {vaga.get('titulo')} | Score: {vaga.get('match_score')}")
            return True

        print(f"[notificador] ERRO HTTP {resposta.status_code}: {resposta.text[:200]}")
        return False

    except requests.Timeout:
        print("[notificador] ERRO: Timeout")
        return False
    except requests.ConnectionError:
        print("[notificador] ERRO: Sem conexão")
        return False
    except Exception as e:
        print(f"[notificador] ERRO: {e}")
        return False