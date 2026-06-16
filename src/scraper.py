import requests
from datetime import datetime, timezone, timedelta

JANELA_HORAS = 30

def _publicada_recentemente(job: dict) -> bool:
    campos_data = ["publishedDate", "published_date", "createdAt", "created_at", "publishedAt"]
    data_str = ""
    for campo in campos_data:
        if job.get(campo):
            data_str = str(job[campo])
            break

    if not data_str:
        return True

    try:
        data_str = data_str.replace("Z", "+00:00")
        data_publicacao = datetime.fromisoformat(data_str)
        if data_publicacao.tzinfo is None:
            data_publicacao = data_publicacao.replace(tzinfo=timezone.utc)
        return data_publicacao >= datetime.now(timezone.utc) - timedelta(hours=JANELA_HORAS)
    except Exception:
        return True

def buscar_vagas() -> list:
    url = "https://employability-portal.gupy.io/api/v1/jobs?jobName=est%C3%A1gio%20tecnologia"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://portal.gupy.io/"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        dados_api = response.json()

        lista_bruta = dados_api.get("data", dados_api) if isinstance(dados_api, dict) else dados_api

        if not lista_bruta or not isinstance(lista_bruta, list):
            return []

        vagas_formatadas = []

        for job in lista_bruta:
            if not _publicada_recentemente(job):
                continue

            vaga_id  = str(job.get("id", job.get("jobId", "")))
            titulo   = job.get("name", job.get("title", "Sem Título"))
            empresa  = job.get("careerPageName", job.get("companyName", "Empresa Confidencial"))
            url_vaga = job.get("jobUrl", job.get("url", ""))
            descricao = job.get("description", f"Vaga para {titulo} na empresa {empresa}.")

            if not vaga_id or not titulo:
                continue

            vagas_formatadas.append({
                "id":        f"GUPY_{vaga_id}",
                "titulo":    titulo,
                "empresa":   empresa,
                "url":       url_vaga,
                "descricao": descricao
            })

        return vagas_formatadas

    except Exception as e:
        print(f"[scraper] Falha de conexão: {e}")
        return []