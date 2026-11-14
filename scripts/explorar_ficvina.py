#!/usr/bin/env python3
"""Descarga páginas de ficvina.cl para ver cómo publica su programación (fuentes/ficvina/)."""
import re, json, urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/141 Safari/537.36"}
out = Path("fuentes/ficvina"); out.mkdir(parents=True, exist_ok=True)
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
        return r.read(), r.headers.get("content-type", "")
def guardar(u, data, ct):
    p = urlparse(u); n = re.sub(r"[^\w.-]+", "_", p.netloc + p.path + ("_" + p.query if p.query else ""))[:150]
    ext = ".json" if "json" in ct else ".pdf" if "pdf" in ct else ".xml" if "xml" in ct else ".html"
    (out / (n + ext)).write_bytes(data)
cola = ["https://ficvina.cl/", "https://www.ficvina.cl/", "https://ficvina.cl/programacion/", "https://ficvina.cl/programa/",
        "https://ficvina.cl/wp-json/", "https://ficvina.cl/wp-json/wp/v2/types", "https://ficvina.cl/sitemap.xml",
        "https://ficvina.cl/sitemap_index.xml", "https://ficvina.cl/robots.txt"]
vistos, enlaces = set(), {}
while cola and len(vistos) < 80:
    u = cola.pop(0)
    if u in vistos: continue
    vistos.add(u)
    try: data, ct = get(u)
    except Exception as e: print("ERR", u, e); continue
    print("OK", len(data), ct[:30], u); guardar(u, data, ct)
    if "html" in ct or "xml" in ct or "json" in ct:
        t = data.decode("utf-8", "replace")
        for h in re.findall(r'(?:href|src|data-url)="([^"]+)"|<loc>([^<]+)</loc>|"(https?:\\?/\\?/[^"]+)"', t):
            v = urljoin(u, (h[0] or h[1] or h[2]).replace("\\/", "/"))
            low = v.lower()
            if "ficvina" not in urlparse(v).netloc and not re.search(r"\.pdf|ticket|entrada|eventbrite|passline|cinemark", low): continue
            if re.search(r"program|cartelera|pelicula|film|grilla|horario|funcion|seccion|competencia|catalogo|sitemap|\.pdf|wp-json|api|ticket|entrada|eventbrite|passline|2026|calendario|agenda", low):
                enlaces[v] = 1
                if "ficvina" in urlparse(v).netloc and not re.search(r"\.(jpg|jpeg|png|webp|css|js|svg|woff2?)(\?|$)", low) and len(vistos) + len(cola) < 80: cola.append(v)
(out / "_enlaces.txt").write_text("\n".join(enlaces), encoding="utf-8")
try:
    t = get("https://ficvina.cl/")[0].decode("utf-8", "replace")
    (out / "_portada_enlaces.txt").write_text("\n".join(sorted({urljoin("https://ficvina.cl/", h) for h in re.findall(r'href="([^"#]+)"', t)})), encoding="utf-8")
except Exception as e: print("portada", e)
print(len(enlaces), "enlaces relevantes")

# PDFs 2026 (programación) y REST de posts/páginas de cinevina.cl
for u in ["https://cinevina.cl/wp-content/uploads/2026/11/Programacion-FicVina-2026.pdf"] + \
        [l for l in (out / "_enlaces.txt").read_text().splitlines() if re.search(r"uploads/2026/1[01]/.*\.pdf$", l, re.I)]:
    try: (out / Path(urlparse(u).path).name).write_bytes(get(u)[0]); print("PDF", u)
    except Exception as e: print("PDF", u, e)
api = out / "api"; api.mkdir(exist_ok=True)
for nombre, url in [("posts", "https://cinevina.cl/wp-json/wp/v2/posts?per_page=100&after=2026-06-01T00:00:00&_embed=1"),
                    ("pages", "https://cinevina.cl/wp-json/wp/v2/pages?per_page=100"),
                    ("media_pdf", "https://cinevina.cl/wp-json/wp/v2/media?per_page=100&mime_type=application/pdf")]:
    try: (api / f"{nombre}.json").write_bytes(get(url)[0]); print("REST", nombre)
    except Exception as e: print("REST", nombre, e)
