#!/usr/bin/env python3
"""Descarga páginas de sanfic.com para ver cómo publica su programación (fuentes/sanfic/)."""
import re, json, urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/141 Safari/537.36"}
out = Path("fuentes/sanfic"); out.mkdir(parents=True, exist_ok=True)
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
        return r.read(), r.headers.get("content-type", "")
inicio = ["https://sanfic.com/", "https://www.sanfic.com/", "https://sanfic.com/programacion/", "https://sanfic.com/programa/",
          "https://sanfic.com/wp-json/", "https://sanfic.com/wp-json/wp/v2/types", "https://sanfic.com/sitemap.xml",
          "https://sanfic.com/sitemap_index.xml", "https://sanfic.com/robots.txt"]
vistos, enlaces = set(), {}
def guardar(u, data, ct):
    n = re.sub(r"[^\w.-]+", "_", urlparse(u).netloc + urlparse(u).path + ("_" + urlparse(u).query if urlparse(u).query else ""))[:150]
    ext = ".json" if "json" in ct else ".pdf" if "pdf" in ct else ".xml" if "xml" in ct else ".html"
    (out / (n + ext)).write_bytes(data)
cola = list(inicio)
while cola and len(vistos) < 60:
    u = cola.pop(0)
    if u in vistos: continue
    vistos.add(u)
    try: data, ct = get(u)
    except Exception as e: print("ERR", u, e); continue
    print("OK", len(data), ct[:30], u); guardar(u, data, ct)
    if "html" in ct or "xml" in ct:
        t = data.decode("utf-8", "replace")
        for h in re.findall(r'(?:href|src|data-url)="([^"]+)"|<loc>([^<]+)</loc>', t):
            h = h[0] or h[1]; v = urljoin(u, h)
            if "sanfic" not in urlparse(v).netloc and not v.lower().endswith(".pdf"): continue
            low = v.lower()
            if re.search(r"program|cartelera|pelicula|film|grilla|horario|funcion|seccion|competencia|catalogo|sitemap|\.pdf|wp-json|api", low):
                enlaces[v] = 1
                if re.search(r"2026|sanfic22|sanfic-22|programaci|cartelera|grilla|pelicula|wp-json/wp/v2/types", low) and len(vistos) + len(cola) < 60 and not re.search(r"\.(jpg|png|webp|css|js)(\?|$)", low): cola.append(v)
(out / "_enlaces.txt").write_text("\n".join(enlaces), encoding="utf-8")
# todos los enlaces de la portada (para ver dónde está la programación 2026)
try:
    t = get("https://sanfic.com/")[0].decode("utf-8", "replace")
    todos = sorted({urljoin("https://sanfic.com/", h) for h in re.findall(r'href="([^"#]+)"', t)})
    (out / "_portada_enlaces.txt").write_text("\n".join(todos), encoding="utf-8"); print(len(todos), "enlaces en portada")
except Exception as e: print("portada", e)
print(len(enlaces), "enlaces relevantes")
