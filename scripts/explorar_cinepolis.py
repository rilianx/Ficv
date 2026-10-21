#!/usr/bin/env python3
"""Busca funciones SANFIC en cinepolischile.cl capturando las respuestas JSON (fuentes/sanfic/cinepolis/)."""
import json, re, asyncio
from pathlib import Path
from playwright.async_api import async_playwright
out = Path("fuentes/sanfic/cinepolis"); out.mkdir(parents=True, exist_ok=True)
URLS = ["https://cinepolischile.cl/", "https://cinepolischile.cl/cartelera/santiago-oriente/cinepolis-parque-arauco",
        "https://cinepolischile.cl/cartelera/santiago-oriente/cinepolis-la-reina", "https://cinepolischile.cl/festival-sanfic",
        "https://cinepolischile.cl/sanfic", "https://cinepolischile.cl/eventos", "https://cinepolischile.cl/proximos-estrenos"]
async def main():
    n = 0
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(locale="es-CL")
        async def resp(r):
            nonlocal n
            if "json" in (r.headers.get("content-type") or ""):
                try: t = await r.text()
                except Exception: return
                n += 1; nombre = re.sub(r"[^\w.-]+", "_", r.url.split("//", 1)[-1])[:120]
                (out / f"{n:03d}_{nombre}.json").write_text(t, encoding="utf-8")
        pg.on("response", lambda r: asyncio.ensure_future(resp(r)))
        for u in URLS:
            try:
                await pg.goto(u, wait_until="networkidle", timeout=60000); await pg.wait_for_timeout(3000)
                html = await pg.content(); (out / (re.sub(r"[^\w]+", "_", u)[-60:] + ".html")).write_text(html, encoding="utf-8")
                print("OK", u, "sanfic" in html.lower())
            except Exception as e: print("ERR", u, e)
        await b.close()
    hits = [f.name for f in out.glob("*.json") if "sanfic" in f.read_text(encoding="utf-8", errors="ignore").lower()]
    print("JSON con 'sanfic':", hits)
asyncio.run(main())
