from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import asyncio
import time

app = FastAPI(title="RubinOT Scraper - Playwright (Grátis 2026)")

cache = {}
CACHE_TTL = 300

@app.get("/")
def root():
    return {
        "message": "✅ RubinOT Scraper ONLINE com Playwright + Stealth",
        "status": "ok",
        "teste": "https://rubinot-scraper.onrender.com/search?nome=Mekbek"
    }

@app.get("/search")
async def search(nome: str = Query(..., description="Nome do personagem")):
    key = nome.strip().lower()

    if key in cache and time.time() - cache[key]["timestamp"] < CACHE_TTL:
        return cache[key]["data"]

    async with async_playwright() as p:
        # Browser com stealth forte
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            url = f"https://rubinot.com.br/?subtopic=characters&name={nome.replace(' ', '+')}"
            await page.goto(url, wait_until="networkidle", timeout=45000)

            # Espera extra para Cloudflare resolver o desafio
            await asyncio.sleep(8)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            data = {
                "nome": nome,
                "level": None,
                "vocacao": None,
                "guild": None,
                "comment": None,
                "status": "offline",
                "last_login": None
            }

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
                        data["guild"] = value if value.lower() != "none" else None
                    elif any(x in label for x in ["comment", "comentário", "comentario"]):
                        data["comment"] = value
                    elif any(x in label for x in ["status", "online"]):
                        data["status"] = "online" if "online" in value.lower() else "offline"
                    elif any(x in label for x in ["last login", "último login", "lastlogin"]):
                        data["last_login"] = value

            # Cache
            cache[key] = {"data": data, "timestamp": time.time()}

            await browser.close()
            return data

        except Exception as e:
            await browser.close()
            return JSONResponse({"error": f"Erro Playwright: {str(e)}"}, status_code=500)
