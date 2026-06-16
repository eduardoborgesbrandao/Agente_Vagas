import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY não encontrada. Verifique o .env")

MATCH_SCORE_MINIMO = 75
LIMITE_ENVIOS_DIA   = 7
MODELO_GEMINI       = "gemini-2.5-flash"