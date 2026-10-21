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

# --- 2ª pasada: REST de WordPress (películas, edición, actividades, PDFs 2026) y fichas ---
api = Path("fuentes/sanfic/api"); api.mkdir(parents=True, exist_ok=True)
def rest(nombre, url, paginas=20):
    todo = []
    for p in range(1, paginas + 1):
        try: data, ct = get(f"{url}{'&' if '?' in url else '?'}per_page=100&page={p}")
        except Exception as e: print("REST", nombre, p, e); break
        try: lote = json.loads(data)
        except Exception: break
        if not isinstance(lote, list) or not lote: break
        todo += lote
        if len(lote) < 100: break
    (api / f"{nombre}.json").write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding="utf-8")
    print("REST", nombre, len(todo)); return todo
pelis = rest("movies", "https://sanfic.com/wp-json/wp/v2/movies?_embed=1")
for t in ["this_edition", "activities", "press_functions", "festival"]: rest(t, f"https://sanfic.com/wp-json/wp/v2/{t}?_embed=1", 5)
rest("media_pdf", "https://sanfic.com/wp-json/wp/v2/media?mime_type=application/pdf&after=2026-06-01T00:00:00", 3)
rest("pages", "https://sanfic.com/wp-json/wp/v2/pages?after=2026-01-01T00:00:00", 3)
rest("taxonomias", "https://sanfic.com/wp-json/wp/v2/taxonomies", 1)
fichas = Path("fuentes/sanfic/fichas"); fichas.mkdir(parents=True, exist_ok=True)
for m in pelis[:6]:
    try: fichas.joinpath(f"{m.get('slug','x')}.html").write_bytes(get(m["link"])[0])
    except Exception as e: print("ficha", e)
try: (out / "programacion_hoy.html").write_bytes(get("https://sanfic.com/esta-edicion/programacion/")[0])
except Exception as e: print(e)
# PDFs 2026 (grilla/catálogo cuando aparezcan)
for m in json.loads((api / "media_pdf.json").read_text()):
    u = m.get("source_url", "")
    if re.search(r"grilla|program|catal|horario", u, re.I):
        try: (out / Path(urlparse(u).path).name).write_bytes(get(u)[0]); print("PDF", u)
        except Exception as e: print("PDF", u, e)
