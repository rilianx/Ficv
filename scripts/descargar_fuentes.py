#!/usr/bin/env python3
"""Descarga los PDF de programa/catálogo enlazados desde ficvaldivia.cl a fuentes/."""
import re, sys, urllib.request
from pathlib import Path
from urllib.parse import urljoin

PAGINAS = ["https://ficvaldivia.cl/", "https://ficvaldivia.cl/en/", "https://ficvaldivia.cl/2026/",
           "https://33.ficvaldivia.cl/", "https://33.ficvaldivia.cl/programacion"]
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"}
out = Path("fuentes"); out.mkdir(exist_ok=True)

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()

enlaces = {}
for p in PAGINAS:
    try:
        html = get(p).decode("utf-8", "replace")
    except Exception as e:
        print("no pude abrir", p, e); continue
    for href, texto in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S | re.I):
        t = re.sub(r"<[^>]+>", " ", texto).strip()
        u = urljoin(p, href)
        if u.lower().split("?")[0].endswith(".pdf") or re.search(r"programa|cat[aá]logo|grilla", t + u, re.I):
            enlaces[u] = t
(out / "enlaces.txt").write_text("\n".join(f"{u}\t{t}" for u, t in enlaces.items()), encoding="utf-8")
print(len(enlaces), "enlaces"); print("\n".join(enlaces))
for u in enlaces:
    if not u.lower().split("?")[0].endswith(".pdf") and "drive.google" not in u:
        continue
    if "drive.google.com/file/d/" in u:
        fid = re.search(r"/d/([^/]+)", u).group(1); u = f"https://drive.google.com/uc?export=download&id={fid}"
    try:
        data = get(u)
    except Exception as e:
        print("falló", u, e); continue
    if data[:4] != b"%PDF":
        print("no es PDF", u); continue
    nombre = re.sub(r"[^\w.-]+", "_", u.split("/")[-1].split("?")[0]) or "programa.pdf"
    if not nombre.lower().endswith(".pdf"): nombre += ".pdf"
    (out / nombre).write_bytes(data); print("guardado", nombre, len(data))
