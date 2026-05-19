# RubinOT Scraper

Scraper **100% gratuito** para buscar personagens públicos do RubinOT.com.br (Nome, Level, Vocação, Guild, Comment).

Bypassa o Cloudflare automaticamente usando `cloudscraper`.

## Como usar

1. Deploy gratuito no **Render.com** (tier free)
2. Acesse: `https://SEU-APP.onrender.com/search?nome=SeuNome`

## Endpoints

- `GET /search?nome=Caio` → retorna JSON com dados do personagem
- `GET /health` → status do scraper

## Deploy no Render (3 cliques)

1. Vá em https://render.com/dashboard
2. New → Web Service → connect este repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Pronto! Seu scraper fica online 24h grátis.

---

Feito para o **PartySearch** (caiomesq/PartySearch)

Qualquer dúvida: abra issue aqui.