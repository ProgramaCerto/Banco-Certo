import sqlite3
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

API_KEY_SECRETA = "bp_chave_api_123"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def conectar():
    return sqlite3.connect('meu_banco_geral.db')

def preparar_tabela_e_colunas(tabela: str, dados: dict):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {tabela} (id INTEGER PRIMARY KEY AUTOINCREMENT)")
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
    
    for chave in dados.keys():
        if chave != 'id' and chave not in colunas_existentes:
            cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {chave} TEXT")
            
    conn.commit()
    conn.close()

def autenticar(x_api_key: str):
    if x_api_key != API_KEY_SECRETA:
        raise HTTPException(status_code=401, detail="Chave de API Inválida!")

@app.post("/api/salvar/{tabela}")
async def salvar_dados(tabela: str, request: Request, x_api_key: str = Header(None)):
    autenticar(x_api_key)
    dados = await request.json()
    preparar_tabela_e_colunas(tabela, dados)
    
    conn = conectar()
    cursor = conn.cursor()
    colunas = ", ".join(dados.keys())
    placeholders = ", ".join(["?"] * len(dados))
    
    query = f"INSERT INTO {tabela} ({colunas}) VALUES ({placeholders})"
    cursor.execute(query, list(dados.values()))
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"status": "sucesso", "id": item_id, "dados": dados}

@app.get("/api/buscar/{tabela}")
def buscar_dados(tabela: str, x_api_key: str = Header(None)):
    autenticar(x_api_key)
    conn = conectar()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {tabela}")
        linhas = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return {"tabela": tabela, "dados": linhas}
    except:
        conn.close()
        return {"tabela": tabela, "dados": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
