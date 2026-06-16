from config.configuracoes import MATCH_SCORE_MINIMO, LIMITE_ENVIOS_DIA
from src.database import (
    criar_tabelas, vaga_existe, inserir_vaga, buscar_fila,
    marcar_enviada, contar_enviadas_hoje, resumo_banco
)
from src.scraper import buscar_vagas
from src.analise import analisar_vaga
from src.notificador import enviar_mensagem_telegram

def processar_vagas(vagas: list) -> dict:
    novas = duplicatas = aprovadas = reprovadas = erros_analise = 0

    for vaga in vagas:
        vaga_id = vaga["id"]

        if vaga_existe(vaga_id):
            duplicatas += 1
            continue

        novas += 1
        
        try:
            analise = analisar_vaga(
                titulo=vaga["titulo"],
                descricao_vaga=vaga["descricao"],
                curriculo_usuario=_ler_curriculo()
            )

            match_score = analise["match_score"]
            tech_core = analise["tech_core"]
            motivo = analise["motivo"]

            if match_score >= MATCH_SCORE_MINIMO:
                status = "queue"
                aprovadas += 1
            else:
                status = "rejected"
                reprovadas += 1

            inserir_vaga(
                vaga_id=vaga_id, empresa=vaga["empresa"], titulo=vaga["titulo"],
                url=vaga["url"], match_score=match_score, tech_core=tech_core,
                motivo=motivo, status=status
            )

        except Exception as e:
            erros_analise += 1
            print(f"[main] Erro de análise ({vaga['titulo']}): {e}")

    return {
        "novas": novas, "duplicatas": duplicatas, "aprovadas": aprovadas,
        "reprovadas": reprovadas, "erros_analise": erros_analise
    }

def enviar_fila() -> dict:
    enviadas_hoje = contar_enviadas_hoje()
    slots_disponiveis = LIMITE_ENVIOS_DIA - enviadas_hoje

    if slots_disponiveis <= 0:
        return {"enviadas": 0, "erros_envio": 0}

    fila = buscar_fila(limite=slots_disponiveis)

    if not fila:
        return {"enviadas": 0, "erros_envio": 0}

    enviadas = erros_envio = 0

    for vaga in fila:
        sucesso = enviar_mensagem_telegram(vaga)
        if sucesso:
            marcar_enviada(vaga["id"])
            enviadas += 1
        else:
            erros_envio += 1

    return {"enviadas": enviadas, "erros_envio": erros_envio}

def _ler_curriculo() -> str:
    try:
        with open("perfil.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Perfil não configurado."

def main():
    print("Iniciando Job Hunter Agent...")
    criar_tabelas()

    vagas = buscar_vagas()
    resumo_processamento = processar_vagas(vagas)
    resumo_envio = enviar_fila()
    estado = resumo_banco()

    print("\n--- RESUMO DA EXECUÇÃO ---")
    print(f"Vagas Encontradas: {len(vagas)}")
    print(f"Novas: {resumo_processamento['novas']} | Duplicatas: {resumo_processamento['duplicatas']}")
    print(f"Aprovadas: {resumo_processamento['aprovadas']} | Reprovadas: {resumo_processamento['reprovadas']}")
    print(f"Mensagens Enviadas: {resumo_envio['enviadas']}")
    print(f"Estado DB -> Fila: {estado.get('queue', 0)} | Enviadas: {estado.get('sent', 0)} | Reprovadas: {estado.get('rejected', 0)}")
    print("--------------------------\n")

if __name__ == "__main__":
    main()