from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import cloudscraper
from bs4 import BeautifulSoup
import time
import asyncio

app = FastAPI(title="RubinOT Scraper - Grátis")

# Scraper com configuração mais forte contra Cloudflare 2026
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    },
    delay=8,           # delay entre requests
    debug=False
)

# Cache simples (5 minutos)
cache = {}
CACHE_TTL = 300

@app.get("/")
def root():
    return {
        "message": "✅ RubinOT Scraper está ONLINE (bypass Cloudflare reforçado)",
        "status": "ok",
        "uso": "https://rubinot-scraper.onrender.com/search?nome=SeuNome",
        "endpoints": ["/search", "/health"]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/search")
async def search(nome: str = Query(..., description="Nome do personagem")):
    key = nome.strip().lower()

    # Cache
    if key in cache and time.time() - cache[key]["timestamp"] < CACHE_TTL:
        return cache[key]["data"]

    for attempt in range(3):  # 3 tentativas
        try:
            url = f"https://rubinot.com.br/?subtopic=characters&name={nome.replace(' ', '+')}"

            resp = scraper.get(url, timeout=25)

            if resp.status_code == 200:
                break
            else:
                await asyncio.sleep(3)  # espera antes da próxima tentativa
                continue

        except Exception as e:
            if attempt == 2:  # última tentativa
                return JSONResponse({
                    "error": f"Falha ao acessar RubinOT (Cloudflare): {str(e)}",
                    "attempts": attempt + 1
                }, status_code=502)
            await asyncio.sleep(3)

    if resp.status_code != 200:
        return JSONResponse({"error": f"RubinOT retornou {resp.status_code}"}, status_code=502)

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

    # Parser mais robusto (atualizado para o layout atual do RubinOT)
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

    # Verifica se personagem existe
    if data["level"] is None and ("não encontrado" in resp.text.lower() or "character not found" in resp.text.lower()):
        return JSONResponse({"error": "Personagem não encontrado"}, status_code=404)

    # Salva no cache
    cache[key] = {"data": data, "timestamp": time.time()}

    return data
