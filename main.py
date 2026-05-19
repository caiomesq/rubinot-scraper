from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import cloudscraper
from bs4 import BeautifulSoup
import time
import asyncio

app = FastAPI(title="RubinOT Scraper - Grátis")

# === CONFIGURAÇÃO MAIS FORTE CONTRA CLOUDFLARE 2026 ===
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    },
    delay=10,                    # delay maior
    debug=False
)

# Cache (5 minutos)
cache = {}
CACHE_TTL = 300

@app.get("/")
def root():
    return {
        "message": "✅ RubinOT Scraper ONLINE (bypass reforçado + debug)",
        "status": "ok",
        "teste": "https://rubinot-scraper.onrender.com/search?nome=Mekbek"
    }

@app.get("/search")
async def search(nome: str = Query(..., description="Nome do personagem")):
    key = nome.strip().lower()

    if key in cache and time.time() - cache[key]["timestamp"] < CACHE_TTL:
        return cache[key]["data"]

    print(f"[DEBUG] Buscando: {nome} | Tentativa iniciada")

    for attempt in range(4):   # 4 tentativas
        try:
            url = f"https://rubinot.com.br/?subtopic=characters&name={nome.replace(' ', '+')}"
            print(f"[DEBUG] Tentativa {attempt+1}/4 → {url}")

            resp = scraper.get(url, timeout=30)

            print(f"[DEBUG] Status recebido: {resp.status_code}")

            if resp.status_code == 200:
                print("[DEBUG] Sucesso! Status 200")
                break

            print(f"[DEBUG] Status diferente de 200: {resp.status_code} - Tentando novamente...")
            await asyncio.sleep(4)

        except Exception as e:
            print(f"[DEBUG] Erro na tentativa {attempt+1}: {str(e)}")
            if attempt == 3:
                return JSONResponse({"error": f"Falha total após 4 tentativas: {str(e)}"}, status_code=502)
            await asyncio.sleep(4)

    if resp.status_code != 200:
        return JSONResponse({"error": f"RubinOT bloqueou (Cloudflare) - Status {resp.status_code}"}, status_code=502)

    soup = BeautifulSoup(resp.text, "html.parser")

    data = {
        "nome": nome,
        "level": None,
        "vocacao": None,
        "guild": None,
        "comment": None,
        "status": "offline",
        "last_login": None
    }

    # Parser robusto
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)

            if any(x in label for x in ["name", "nome"]):
                data["nome"] = value
            elif any(x in label for x in ["level", "nível", "nivel"]):
                data["level"] = int(value) if value.isdigit() else value
            elif any(x in label for x in ["vocation", "vocação", "vocacao"]):
                data["vocacao"] = value
            elif any(x in label for x in ["guild", "guilda"]):
                data["guild"] = value if value and value.lower() != "none" else None
            elif any(x in label for x in ["comment", "comentário", "comentario"]):
                data["comment"] = value
            elif any(x in label for x in ["status", "online"]):
                data["status"] = "online" if "online" in value.lower() else "offline"
            elif any(x in label for x in ["last login", "último login", "lastlogin"]):
                data["last_login"] = value

    # Cache
    cache[key] = {"data": data, "timestamp": time.time()}

    print(f"[DEBUG] Personagem encontrado: {data['nome']} - Level {data['level']}")
    return data
