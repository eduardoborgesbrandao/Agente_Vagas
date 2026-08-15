import re
import requests
from datetime import datetime, timezone, timedelta

JANELA_HORAS = 30

# Empresas no Greenhouse — adiciona ou remove slugs aqui
GREENHOUSE_EMPRESAS = [
    "nubank", "stone", "picpay", "creditas", "loft",
    "loggi", "ebanx", "hotmart", "neon", "pagarme",
    "doordash", "salesforce", "ifood"
]

# Palavras-chave que identificam vaga de entrada (estágio/júnior)
KEYWORDS_ENTRADA = [
    "intern", "internship", "estágio", "estagio",
    "junior", "júnior", "trainee", "entry"
]

# ─────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────

def _publicada_recentemente(data_str: str) -> bool:
    if not data_str:
        return True
    try:
        data_str = str(data_str).replace("Z", "+00:00")
        data_publicacao = datetime.fromisoformat(data_str)
        if data_publicacao.tzinfo is None:
            data_publicacao = data_publicacao.replace(tzinfo=timezone.utc)
        return data_publicacao >= datetime.now(timezone.utc) - timedelta(hours=JANELA_HORAS)
    except Exception:
        return True

def _remover_html(texto: str) -> str:
    return re.sub(r'<[^>]+>', ' ', str(texto)).strip()

def _e_vaga_entrada(titulo: str) -> bool:
    titulo_lower = titulo.lower()
    return any(k in titulo_lower for k in KEYWORDS_ENTRADA)

# ─────────────────────────────────────────
# GUPY
# ─────────────────────────────────────────

def buscar_gupy() -> list:
    url = "https://employability-portal.gupy.io/api/v1/jobs?jobName=est%C3%A1gio%20tecnologia"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Referer": "https://portal.gupy.io/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        dados = response.json()
        lista = dados.get("data", dados) if isinstance(dados, dict) else dados
        if not isinstance(lista, list):
            return []

        vagas = []
        campos_data = ["publishedDate", "published_date", "createdAt", "created_at", "publishedAt"]
        for job in lista:
            data_str = next((str(job[c]) for c in campos_data if job.get(c)), "")
            if not _publicada_recentemente(data_str):
                continue
            vaga_id = str(job.get("id", job.get("jobId", "")))
            titulo = job.get("name", job.get("title", ""))
            if not vaga_id or not titulo:
                continue
            vagas.append({
                "id": f"GUPY_{vaga_id}",
                "titulo": titulo,
                "empresa": job.get("careerPageName", job.get("companyName", "Empresa Confidencial")),
                "url": job.get("jobUrl", job.get("url", "")),
                "descricao": job.get("description", f"Vaga para {titulo}.")[:2000]
            })
        return vagas
    except Exception as e:
        print(f"[scraper:gupy] Erro: {e}")
        return []

# ─────────────────────────────────────────
# GREENHOUSE (API pública — múltiplas empresas)
# ─────────────────────────────────────────

def buscar_greenhouse() -> list:
    vagas = []
    for slug in GREENHOUSE_EMPRESAS:
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                continue
            jobs = response.json().get("jobs", [])
            for job in jobs:
                titulo = job.get("title", "")
                vaga_id = str(job.get("id", ""))
                if not vaga_id or not titulo:
                    continue
                if not _e_vaga_entrada(titulo):
                    continue
                descricao = _remover_html(job.get("content", f"Vaga {titulo}."))
                vagas.append({
                    "id": f"GH_{slug.upper()}_{vaga_id}",
                    "titulo": titulo,
                    "empresa": slug.title(),
                    "url": job.get("absolute_url", ""),
                    "descricao": descricao[:2000]
                })
        except Exception as e:
            print(f"[scraper:greenhouse:{slug}] Erro: {e}")
    return vagas

# ─────────────────────────────────────────
# AMAZON
# ─────────────────────────────────────────

def buscar_amazon() -> list:
    url = (
        "https://www.amazon.jobs/pt/search.json"
        "?radius=24km"
        "&facets%5B%5D=normalized_country_code"
        "&facets%5B%5D=normalized_state_name"
        "&facets%5B%5D=normalized_city_name"
        "&facets%5B%5D=location"
        "&facets%5B%5D=business_category"
        "&facets%5B%5D=category"
        "&facets%5B%5D=schedule_type_id"
        "&facets%5B%5D=employee_class"
        "&facets%5B%5D=normalized_location"
        "&facets%5B%5D=job_function_id"
        "&facets%5B%5D=is_manager"
        "&facets%5B%5D=is_intern"
        "&offset=0&result_limit=50&sort=recent"
        "&latitude=-23.56283&longitude=-46.65474"
        "&base_query=Intern"
        "&city=S%C3%A3o+Paulo&country=BRA&region=S%C3%A3o+Paulo"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.amazon.jobs/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        jobs = response.json().get("jobs", [])
        vagas = []
        for job in jobs:
            vaga_id = str(job.get("id_icims", job.get("id", "")))
            titulo = job.get("title", "")
            if not vaga_id or not titulo:
                continue
            if not _publicada_recentemente(job.get("posted_date", "")):
                continue
            job_path = job.get("job_path", "")
            url_vaga = f"https://www.amazon.jobs{job_path}" if job_path else ""
            descricao = job.get("description", job.get("description_short", f"Vaga {titulo} na Amazon."))
            vagas.append({
                "id": f"AMAZON_{vaga_id}",
                "titulo": titulo,
                "empresa": "Amazon",
                "url": url_vaga,
                "descricao": _remover_html(descricao)[:2000]
            })
        return vagas
    except Exception as e:
        print(f"[scraper:amazon] Erro: {e}")
        return []

# ─────────────────────────────────────────
# MICROSOFT
# ─────────────────────────────────────────

def buscar_microsoft() -> list:
    url = (
        "https://apply.careers.microsoft.com/api/pcsx/search"
        "?domain=microsoft.com"
        "&query="
        "&location=S%C3%A3o+Paulo%2C+State+of+S%C3%A3o+Paulo%2C+Brazil"
        "&start=0&sort_by=distance"
        "&filter_include_remote=1"
        "&filter_seniority=Intern"
        "&filter_seniority=Entry"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        dados = response.json()
        # Microsoft pode retornar em estruturas diferentes
        jobs = (
            dados.get("operationResult", {}).get("result", {}).get("jobs", [])
            or dados.get("jobs", [])
            or dados.get("value", [])
        )
        vagas = []
        for job in jobs:
            vaga_id = str(job.get("jobId", job.get("id", "")))
            titulo = job.get("title", job.get("Title", ""))
            if not vaga_id or not titulo:
                continue
            url_vaga = job.get("url", job.get("applyUrl", ""))
            descricao = job.get("description", job.get("Description", f"Vaga {titulo} na Microsoft."))
            vagas.append({
                "id": f"MSFT_{vaga_id}",
                "titulo": titulo,
                "empresa": "Microsoft",
                "url": url_vaga,
                "descricao": _remover_html(descricao)[:2000]
            })
        return vagas
    except Exception as e:
        print(f"[scraper:microsoft] Erro: {e}")
        return []

# ─────────────────────────────────────────
# MERCADO LIVRE
# ─────────────────────────────────────────

def buscar_mercadolivre() -> list:
    url = (
        "https://careers-meli.mercadolibre.com/api/positions"
        "?start=0&num=50"
        "&query=Est%C3%A1gio"
        "&location=SP%2C+Brazil"
        "&sort_by=timestamp"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        dados = response.json()
        jobs = dados.get("positions", dados.get("jobs", []))
        if not isinstance(jobs, list):
            return []
        vagas = []
        for job in jobs:
            vaga_id = str(job.get("id", job.get("Id", "")))
            titulo = job.get("name", job.get("title", ""))
            if not vaga_id or not titulo:
                continue
            url_vaga = job.get("url", job.get("applyUrl", f"https://careers-meli.mercadolibre.com/jobs/{vaga_id}"))
            descricao = job.get("description", f"Vaga {titulo} no Mercado Livre.")
            vagas.append({
                "id": f"MELI_{vaga_id}",
                "titulo": titulo,
                "empresa": "Mercado Livre",
                "url": url_vaga,
                "descricao": _remover_html(descricao)[:2000]
            })
        return vagas
    except Exception as e:
        print(f"[scraper:mercadolivre] Erro: {e}")
        return []

# ─────────────────────────────────────────
# ENTRADA PRINCIPAL
# ─────────────────────────────────────────

def buscar_vagas() -> list:
    fontes = [
        ("Gupy",          buscar_gupy),
        ("Greenhouse",    buscar_greenhouse),
        ("Amazon",        buscar_amazon),
        ("Microsoft",     buscar_microsoft),
        ("Mercado Livre", buscar_mercadolivre),
    ]
    todas = []
    for nome, func in fontes:
        try:
            resultado = func()
            print(f"[scraper] {nome}: {len(resultado)} vagas encontradas")
            todas += resultado
        except Exception as e:
            print(f"[scraper] {nome}: erro inesperado: {e}")
    print(f"[scraper] Total: {len(todas)} vagas de {len(fontes)} fontes")
    return todas