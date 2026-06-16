import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'jobs.db')

def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def criar_tabelas():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vagas (
            id          TEXT PRIMARY KEY,
            empresa     TEXT NOT NULL,
            titulo      TEXT NOT NULL,
            url         TEXT,
            match_score INTEGER NOT NULL,
            tech_core   INTEGER NOT NULL,
            motivo      TEXT,
            status      TEXT NOT NULL DEFAULT 'queue',
            data_encontrada TEXT NOT NULL,
            data_enviada    TEXT
        )
    """)
    conn.commit()
    conn.close()

def vaga_existe(vaga_id: str) -> bool:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM vagas WHERE id = ?", (vaga_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

def inserir_vaga(vaga_id: str, empresa: str, titulo: str, url: str, match_score: int, tech_core: bool, motivo: str, status: str = 'queue'):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vagas
            (id, empresa, titulo, url, match_score, tech_core, motivo, status, data_encontrada)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (vaga_id, empresa, titulo, url, match_score, 1 if tech_core else 0, motivo, status, str(date.today())))
    conn.commit()
    conn.close()

def buscar_fila(limite: int = 5) -> list:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, empresa, titulo, url, match_score, tech_core, motivo
        FROM vagas
        WHERE status = 'queue'
        ORDER BY tech_core DESC, match_score DESC
        LIMIT ?
    """, (limite,))
    colunas = ['id', 'empresa', 'titulo', 'url', 'match_score', 'tech_core', 'motivo']
    resultados = [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    conn.close()
    return resultados

def marcar_enviada(vaga_id: str):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE vagas SET status = 'sent', data_enviada = ? WHERE id = ?", (str(date.today()), vaga_id))
    conn.commit()
    conn.close()

def contar_enviadas_hoje() -> int:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vagas WHERE status = 'sent' AND data_enviada = ?", (str(date.today()),))
    quantidade = cursor.fetchone()[0]
    conn.close()
    return quantidade

def resumo_banco() -> dict:
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM vagas GROUP BY status")
    contagens = dict(cursor.fetchall())
    conn.close()
    return contagens