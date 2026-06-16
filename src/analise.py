import json
from google import genai
from google.genai import types
from config.configuracoes import GEMINI_API_KEY, MODELO_GEMINI

SYSTEM_PROMPT = """
Você é um recrutador técnico sênior e um sistema automatizado de triagem.
Sua única função é comparar uma vaga com o currículo do candidato e retornar uma avaliação.
A vaga se for presencial ou híbrida deve ser em São Paulo - SP, se for 100% remoto apenas cheque se pedem que seja residente de algum país em específico, se não pedirem então pode mandar por que a localização não vai importar.

REGRAS ABSOLUTAS DE ELIMINAÇÃO (SCORE ABAIXO DE 50):
- Se a vaga for estritamente administrativa (RH, Financeiro, Auxiliar de Escritório) e não envolver tecnologia.
- Se a vaga exigir graduação exclusiva em cursos fora de Sistemas de Informação, Ciência da Computação ou outros cursos relacionados a tecnologia.
- Se for vaga de suporte Nível 1 puramente focado em atendimento telefônico.
- Se a vaga for exclusiva para mulheres ou pretos e pardos ou pcd ou LGBT+

REGRAS DE FORMATAÇÃO:
- Retorne SOMENTE o objeto JSON, sem nenhum texto antes ou depois
- Não use blocos de código markdown (sem ```json)
- O JSON deve conter exatamente três chaves: match_score, tech_core, motivo
- match_score: inteiro entre 0 e 100
- tech_core: booleano (true se a empresa tem tecnologia como produto principal)
- motivo: string com no máximo 2 linhas justificando a nota

Exemplo do formato esperado:
{"match_score": 30, "tech_core": false, "motivo": "Vaga com foco administrativo em RH, sem alinhamento com Sistemas de Informação ou stack de desenvolvimento."}
""".strip()

def _limpar_resposta(texto: str) -> str:
    texto = texto.strip()
    inicio = texto.find('{')
    fim = texto.rfind('}')

    if inicio == -1 or fim == -1:
        raise ValueError("Formato JSON não encontrado na resposta.")

    return texto[inicio:fim + 1]

def _validar_resultado(dados: dict) -> dict:
    return {
        'match_score': int(dados.get('match_score', 0)),
        'tech_core': bool(dados.get('tech_core', False)),
        'motivo': str(dados.get('motivo', '')).strip()
    }

def analisar_vaga(titulo: str, descricao_vaga: str, curriculo_usuario: str) -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt_usuario = (
        f"VAGA: {titulo}\n\n"
        f"DESCRIÇÃO:\n{descricao_vaga}\n\n"
        f"CURRÍCULO DO CANDIDATO:\n{curriculo_usuario}"
    )

    for tentativa in range(1, 3):
        try:
            resposta = client.models.generate_content(
                model=MODELO_GEMINI,
                contents=prompt_usuario,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                    response_mime_type="application/json",
                )
            )

            texto_limpo = _limpar_resposta(resposta.text)
            dados = json.loads(texto_limpo)
            return _validar_resultado(dados)

        except (json.JSONDecodeError, ValueError) as e:
            if tentativa == 2:
                raise ValueError(f"Falha ao decodificar JSON: {e}")
        except Exception as e:
            if tentativa == 2:
                raise Exception(f"Erro na API do Gemini: {e}")