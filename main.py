from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import asyncio
from typing import Dict, Any

app = FastAPI(title="RubinOT Scraper - Grátis")

# Cache simples em memória (Render free reinicia de vez em quando, mas é OK)
cache: Dict[str, tuple[Dict[str, Any], datetime]] = {}
CACHE_TTL = 300  # 5 minutos

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

def parse_rubinot_character(html: str, searched_name: str) -> dict:
    soup = BeautifulSoup(html, 'lxml')
    character = {
        "nome": searched_name,
        "level": None,
        "vocacao": None,
        "guild": None,
        "comment": None,
        "status": "offline",
        "last_login": None,
        "erro": None
    }

    # Tabela de informações do personagem (padrão OT)
    tables = soup.find_all('table', class_=lambda x: x and 'TableContent' in x or 'table' in x.lower())
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                value = cells[1].get_text(strip=True)
                if 'level' in label:
                    character['level'] = value
                elif 'vocação' in label or 'vocation' in label:
                    character['vocacao'] = value
                elif 'guild' in label:
                    character['guild'] = value
                elif 'comment' in label or 'comentário' in label or 'comentario' in label:
                    character['comment'] = value
                elif 'status' in label or 'online' in label:
                    character['status'] = value.lower()
                elif 'last login' in label or 'último login' in label:
                    character['last_login'] = value

    # Fallback: busca por texto direto na página
    if not character['level']:
        level_tag = soup.find(string=lambda text: text and 'Level:' in text)
        if level_tag:
            character['level'] = level_tag.find_next().get_text(strip=True) if hasattr(level_tag, 'find_next') else None

    if character['level'] is None and character['vocacao'] is None:
        character['erro'] = 'Personagem não encontrado ou página bloqueada'

    return character


@app.get("/search")
async def search_character(nome: str = Query(..., description="Nome do personagem")):
    name_clean = nome.strip().lower()

    # Verifica cache
    now = datetime.now()
    if name_clean in cache:
        data, expiry = cache[name_clean]
        if now < expiry:
            return data

    try:
        url = f"https://rubinot.com.br/?subtopic=characters&name={nome.replace(' ', '+')}"
        response = scraper.get(url, timeout=15)

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail=f"RubinOT retornou {response.status_code}")

        character_data = parse_rubinot_character(response.text, nome)

        # Salva no cache
        cache[name_clean] = (character_data, now + timedelta(seconds=CACHE_TTL))

        return character_data

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"erro": f"Erro ao buscar: {str(e)}", "nome": nome}
        )


@app.get("/health")
async def health():
    return {"status": "online", "cache_size": len(cache), "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)