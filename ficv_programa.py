#!/usr/bin/env python3
"""
Navega la programación del 33° FICValdivia y arma un programa por día y sección.

    https://33.ficvaldivia.cl/programacion

Uso:
    pip install -r requirements.txt
    playwright install chromium
    python ficv_programa.py                  # extrae y genera salida/
    python ficv_programa.py --detalles       # además visita cada película para precisar la sección
    python ficv_programa.py --ver            # muestra el navegador mientras navega
    python ficv_programa.py --dump           # guarda el HTML de cada día (para depurar selectores)

Salida (carpeta salida/):
    programa.json   datos crudos normalizados
    programa.md     programa por día → sección → función
    programa.html   página navegable (pestañas por día, filtro por sección y búsqueda)
    api/*.json      respuestas JSON que la página haya pedido (si usa una API)

La página no expone un formato documentado, así que el script combina dos
estrategias: (1) si la web carga la programación desde una API JSON, la
intercepta y la usa; (2) si no, lee el DOM, haciendo clic en cada pestaña de
día y detectando las "tarjetas" de función por su hora (HH:MM).
"""

import argparse
import html
import json
import os
import re
import sys
import unicodedata
from collections import OrderedDict, defaultdict
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

URL = "https://33.ficvaldivia.cl/programacion"
OUT = Path("salida")

# Secciones anunciadas para la 33ª edición. Se usan para reconocer la sección
# en el texto de una tarjeta o de la ficha de la película. Más largas primero
# para que "Selección Oficial Cortometraje..." gane a "Selección Oficial".
SECCIONES = sorted([
    "Selección Oficial Largometraje Internacional",
    "Selección Oficial Largometraje Nacional",
    "Selección Oficial Largometraje",
    "Selección Oficial Cortometraje Latinoamericano y del Caribe",
    "Selección Oficial Cortometraje Latinoamericano",
    "Selección Oficial Cortometraje",
    "Selección Oficial Cine Chileno Estudiantil",
    "Selección Oficial Cortometraje Estudiantil Chileno",
    "Selección Oficial Cortometraje Audiovisual",
    "Selección Oficial Infantil",
    "Selección Oficial",
    "Cine Contemporáneo",
    "Panorama Contemporáneo",
    "Animación",
    "Gala Chilena",
    "Galas",
    "Ventana Cine Austral",
    "Cine Austral",
    "Cine Expandido",
    "Retrospectiva",
    "Foco",
    "Homenaje",
    "Clásicos",
    "Infantil",
    "Familiar",
    "Función Especial",
    "Apertura",
    "Clausura",
    "Film Central",
    "Industria",
    "Actividades",
], key=len, reverse=True)

DIAS_RE = r"(lun|mar|mi[eé]|jue|vie|s[aá]b|dom)[a-zé]*\.?"
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7,
         "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}
HORA_RE = re.compile(r"\b([01]?\d|2[0-3])[:.h]([0-5]\d)\b")


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def detectar_seccion(texto):
    t = norm(texto)
    for s in SECCIONES:
        if norm(s) in t:
            return s
    return None


def normalizar_dia(texto):
    """'Lunes 12 oct' / '12/10' / '2026-10-12' → '2026-10-12' si se puede."""
    t = norm(texto)
    m = re.search(r"(20\d\d)-(\d\d)-(\d\d)", t)
    if m:
        return m.group(0)
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})\b", t)
    if m:
        return f"2026-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.search(r"\b(\d{1,2})\s*(de\s*)?(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)", t)
    if m:
        return f"2026-{MESES[m.group(3)]:02d}-{int(m.group(1)):02d}"
    m = re.search(DIAS_RE + r"\s*(\d{1,2})\b", t)
    if m:  # festival en octubre
        return f"2026-10-{int(m.group(2)):02d}"
    return texto.strip()


# --------------------------------------------------------------------------
# Estrategia 1: API JSON interceptada
# --------------------------------------------------------------------------

CLAVES_TITULO = ("titulo", "title", "nombre", "name", "pelicula", "film")
CLAVES_FECHA = ("fecha", "date", "dia", "day", "start", "inicio", "datetime")
CLAVES_HORA = ("hora", "time", "horario")
CLAVES_SALA = ("sala", "lugar", "venue", "sede", "location", "cine", "espacio")
CLAVES_SECCION = ("seccion", "section", "categoria", "category", "programa", "competencia")


def _valor(d, claves):
    for k, v in d.items():
        nk = norm(str(k))
        if any(c in nk for c in claves):
            if isinstance(v, dict):
                v = next((v[x] for x in v if norm(x) in ("name", "nombre", "title", "titulo", "rendered")), None)
            if isinstance(v, list):
                v = ", ".join(str(x.get("name", x) if isinstance(x, dict) else x) for x in v)
            if v not in (None, ""):
                return str(v)
    return None


def funciones_desde_api(payloads):
    out = []

    def visitar(o):
        if isinstance(o, list):
            for x in o:
                visitar(x)
        elif isinstance(o, dict):
            titulo = _valor(o, CLAVES_TITULO)
            fecha = _valor(o, CLAVES_FECHA)
            hora = _valor(o, CLAVES_HORA)
            if titulo and (fecha or hora):
                if not hora and fecha:
                    m = re.search(r"([01]?\d|2[0-3]):([0-5]\d)", fecha)
                    hora = f"{int(m.group(1)):02d}:{m.group(2)}" if m else ""
                out.append({
                    "dia": normalizar_dia(fecha or ""),
                    "hora": hora or "",
                    "titulo": re.sub(r"<[^>]+>", "", titulo).strip(),
                    "sala": _valor(o, CLAVES_SALA) or "",
                    "seccion": _valor(o, CLAVES_SECCION) or detectar_seccion(json.dumps(o, ensure_ascii=False)) or "",
                    "url": o.get("url") or o.get("link") or o.get("permalink") or "",
                    "fuente": "api",
                })
            for v in o.values():
                if isinstance(v, (list, dict)):
                    visitar(v)

    for p in payloads:
        visitar(p)
    return out


# --------------------------------------------------------------------------
# Softr (la web del festival está hecha en Softr, con una tabla "Películas")
# --------------------------------------------------------------------------

# Lee window.softrBlocks y devuelve {id_campo: nombre} del bloque de lista.
JS_MAPA_SOFTR = r"""
() => {
  const bs = (window.softrBlocks || []).filter(b => b.type === 'dynamic' && b.elements && b.elements.filters);
  if (!bs.length) return null;
  const b = bs[0], mapa = {};
  for (const it of (b.elements.fields && b.elements.fields.items) || []) {
    const f = it.field || {};
    if (f.mappedTo) mapa[f.mappedTo] = f.type === 'heading' ? 'titulo' : (f.type || f.mappedTo);
  }
  for (const it of b.elements.filters.items || [])
    if (it.mappedTo) mapa[it.mappedTo] = it.label && it.label.value || it.mappedTo;
  return {hrid: b.hrid, mapa};
}
"""


def esperar_softr(page):
    """Si la página es Softr: espera a que cargue la lista y pulsa 'Cargar más' hasta el final."""
    try:
        info = page.evaluate(JS_MAPA_SOFTR)
    except Exception:
        info = None
    if not info:
        return None
    print(f"Página Softr detectada (bloque '{info['hrid']}'): campos {info['mapa']}", file=sys.stderr)
    bloque = page.locator(f"#{info['hrid']}")
    try:
        bloque.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass
    for _ in range(90):  # hasta ~90 s
        try:
            if "Loading" not in bloque.inner_text(timeout=2000):
                break
        except Exception:
            pass
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(1000)
    clics = 0
    for _ in range(300):
        btn = bloque.get_by_text(re.compile(r"Cargar m[aá]s|Load more", re.I)).first
        try:
            if not btn.is_visible(timeout=3000):
                break
            btn.scroll_into_view_if_needed(timeout=3000)
            btn.click(timeout=5000)
            clics += 1
            page.wait_for_timeout(1500)
        except Exception:
            break
    print(f"  'Cargar más' pulsado {clics} veces", file=sys.stderr)
    return info["mapa"]


def _texto(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(t for t in (_texto(x) for x in v) if t)
    if isinstance(v, dict):
        for k in ("label", "name", "value", "text", "title", "url"):
            if k in v:
                return _texto(v[k])
        return ""
    return str(v).strip()


def registros_softr(payloads, mapa):
    """Busca en las respuestas JSON registros {id, fields:{...}} con los campos del bloque."""
    vistos, out = set(), []

    def visitar(o):
        if isinstance(o, list):
            for x in o:
                visitar(x)
        elif isinstance(o, dict):
            campos = o.get("fields") if isinstance(o.get("fields"), dict) else None
            if campos and any(k in mapa for k in campos):
                rid = o.get("id") or json.dumps(campos, sort_keys=True)[:200]
                if rid not in vistos:
                    vistos.add(rid)
                    out.append(o)
                return
            for v in o.values():
                if isinstance(v, (list, dict)):
                    visitar(v)

    for p in payloads:
        visitar(p)
    return out


def nombres_campos_softr(payloads):
    """La respuesta /metadata trae {fields:[{id, name}]}: id de campo → nombre real en la tabla."""
    for p in payloads:
        if isinstance(p, dict) and isinstance(p.get("fields"), list) and p.get("primaryFieldId"):
            return {f["id"]: f.get("name", f["id"]) for f in p["fields"] if isinstance(f, dict) and "id" in f}
    return {}


# "Viernes 16 - 11:00"
AGENDA_RE = re.compile(DIAS_RE + r"\s*(\d{1,2})\s*[-–·,]?\s*([01]?\d|2[0-3])[:.]([0-5]\d)", re.I)


def funciones_desde_softr(payloads, mapa, base_url):
    nombres = {**(mapa or {}), **nombres_campos_softr(payloads)}
    inv = defaultdict(list)
    for k, v in nombres.items():
        inv[norm(v)].append(k)

    def lista(f, *candidatos):
        for c in candidatos:
            for k in inv.get(norm(c), []):
                v = f.get(k)
                if v not in (None, "", []):
                    return [t for t in (_texto(x) for x in (v if isinstance(v, list) else [v])) if t]
        return []

    def campo(f, *candidatos):
        return ", ".join(lista(f, *candidatos))

    out = []
    registros = registros_softr(payloads, nombres)
    for r in registros:
        f = r["fields"]
        cat, sub = campo(f, "Categoría"), campo(f, "Sub Categoría", "Sub categoría")
        base = {
            "titulo": campo(f, "Título", "titulo").strip(),
            # si la película se da en varias salas, la API no dice cuál corresponde a cada función
            "sala": " / ".join(dict.fromkeys(lista(f, "DondeEs", "Lugar"))),
            "seccion": cat or sub,
            "subseccion": sub if cat else "",
            "acceso": " / ".join(dict.fromkeys(lista(f, "TipoAcceso", "Tipo de acceso"))),
            "direccion": campo(f, "Dirección"),
            "pais": campo(f, "País/es"),
            "url": f"{base_url}?recordId={r['id']}" if r.get("id") else "",
            "id": r.get("id", ""),
            "fuente": "softr",
        }
        pares = [m for item in lista(f, "Agenda", "text") for m in AGENDA_RE.finditer(item)]
        if pares:
            for m in pares:
                out.append({**base, "dia": f"2026-10-{int(m.group(2)):02d}",
                            "hora": f"{int(m.group(3)):02d}:{m.group(4)}"})
        else:  # sin horario: un registro por día
            for d in lista(f, "QueDiasLaDan", "Día de exhibición") or [""]:
                out.append({**base, "dia": normalizar_dia(d) if d else "", "hora": ""})
    if registros:
        print(f"  Softr: {len(registros)} películas → {len(out)} funciones", file=sys.stderr)
    return out


def generar(funciones, out):
    funciones = deduplicar(funciones)
    prog = agrupar(funciones)
    (out / "programa.json").write_text(json.dumps(funciones, ensure_ascii=False, indent=1), encoding="utf-8")
    escribir_md(prog, out / "programa.md")
    escribir_html(prog, out / "programa.html")
    print(f"\n{len(funciones)} funciones en {len(prog)} días:", file=sys.stderr)
    for dia, secs in prog.items():
        print(f"  {nombre_dia(dia)}: " + ", ".join(f"{s} ({len(v)})" for s, v in secs.items()), file=sys.stderr)
    print(f"\nListo → {out/'programa.html'}, {out/'programa.md'}, {out/'programa.json'}", file=sys.stderr)


# --------------------------------------------------------------------------
# Estrategia 2: DOM
# --------------------------------------------------------------------------

# Recorre el documento en orden. Lleva la cuenta del último encabezado de día
# y de sección vistos, y agrupa en "tarjetas" los elementos con una hora.
JS_EXTRAER = r"""
(args) => {
  const [diaRe, seccionesNorm] = args;
  const DIA = new RegExp(diaRe, 'i');
  const HORA = /\b([01]?\d|2[0-3])[:.h]([0-5]\d)\b/;
  const nrm = s => (s||'').normalize('NFKD').replace(/[̀-ͯ]/g,'').toLowerCase().trim();
  const visible = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
                          return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const txt = el => (el.innerText || '').trim();

  // 1. Hojas con hora → subir hasta un contenedor razonable (la tarjeta).
  const hojas = [...document.querySelectorAll('body *')].filter(el =>
      el.children.length === 0 || [...el.childNodes].some(n => n.nodeType === 3 && HORA.test(n.textContent)));
  const tarjetas = new Set();
  for (const h of hojas) {
    if (!HORA.test(h.textContent || '') || (h.textContent||'').length > 40) continue;
    let c = h;
    while (c.parentElement && c.parentElement !== document.body) {
      const p = c.parentElement;
      const nHoras = (txt(p).match(new RegExp(HORA.source, 'g')) || []).length;
      if (nHoras > 2 || txt(p).length > 700) break;   // ya agarra varias funciones
      c = p;
      if (c.querySelector('a[href]') && txt(c).length > 15 && /article|li|tr/i.test(c.tagName)) break;
    }
    if (visible(c)) tarjetas.add(c);
  }
  // quitar tarjetas contenidas en otras
  const lista = [...tarjetas].filter(t => ![...tarjetas].some(o => o !== t && o.contains(t)));

  // 2. Encabezados de día/sección en orden de documento.
  const marcas = [];
  document.querySelectorAll('h1,h2,h3,h4,h5,h6,[class*=dia],[class*=day],[class*=fecha],[class*=date],[class*=secc],[class*=section],[class*=categ]')
    .forEach(el => {
      const t = txt(el); if (!t || t.length > 80) return;
      if (DIA.test(t) || /\b\d{1,2}\s*(de\s*)?oct/i.test(t)) marcas.push({el, tipo:'dia', t});
      else if (seccionesNorm.some(s => nrm(t).includes(s))) marcas.push({el, tipo:'seccion', t});
    });
  const antes = (a, b) => a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING;

  return lista.map(c => {
    const t = txt(c);
    const lineas = t.split('\n').map(s => s.trim()).filter(Boolean);
    const hora = (t.match(HORA) || [''])[0];
    const a = c.querySelector('a[href]');
    const tituloEl = c.querySelector('h1,h2,h3,h4,h5,h6,strong,b,[class*=title],[class*=titulo]') || a;
    let titulo = tituloEl ? txt(tituloEl) : '';
    if (!titulo || HORA.test(titulo) && titulo.length < 8)
      titulo = lineas.find(l => !HORA.test(l) && l.length > 2) || '';
    const secEl = c.querySelector('[class*=secc],[class*=section],[class*=categ],[class*=tag],[class*=label]');
    let dia = '', seccion = '';
    for (const m of marcas) {
      if (m.el.contains(c) || !antes(m.el, c)) continue;
      if (m.tipo === 'dia') dia = m.t; else seccion = m.t;
    }
    return { hora, titulo: titulo.split('\n')[0], url: a ? a.href : '',
             seccionTag: secEl ? txt(secEl) : '', diaEncabezado: dia, seccionEncabezado: seccion, lineas };
  });
}
"""

JS_PESTANAS_DIA = r"""
(diaRe) => {
  const DIA = new RegExp('^\\s*(' + diaRe + ')?\\s*\\d{1,2}(\\s*(de\\s*)?(oct\\w*))?\\s*$|^\\s*' + diaRe + '\\s*$', 'i');
  const cands = [...document.querySelectorAll('button,a,li,[role=tab],label,span,div')]
    .filter(el => { const t = (el.innerText||'').trim().replace(/\s+/g,' ');
                    const r = el.getBoundingClientRect();
                    return t.length < 25 && DIA.test(t) && r.width > 0 && r.height > 0; });
  // quedarse con el elemento más externo con ese texto (el clicable)
  const unicos = cands.filter(el => !cands.some(o => o !== el && o.contains(el) && o.innerText.trim() === el.innerText.trim()));
  return unicos.map((el, i) => { el.setAttribute('data-ficv-dia', i); return (el.innerText||'').trim().replace(/\s+/g,' '); });
}
"""

SALA_RE = re.compile(r"(teatro|cine|sala|aula|centro|cervecer|biblioteca|museo|parque|casa|auditorio|"
                     r"espacio|gimnasio|plaza|campus|cultural)", re.I)


def tarjeta_a_funcion(t, dia_pestana):
    texto = "\n".join(t["lineas"])
    sala = next((l for l in t["lineas"] if SALA_RE.search(l) and l != t["titulo"] and len(l) < 80), "")
    seccion = (detectar_seccion(t["seccionTag"]) or t["seccionTag"].split("\n")[0]
               if t["seccionTag"] else "") or detectar_seccion(texto) or t["seccionEncabezado"]
    dia = dia_pestana or t["diaEncabezado"]
    return {
        "dia": normalizar_dia(dia) if dia else "",
        "hora": t["hora"].replace(".", ":").replace("h", ":"),
        "titulo": t["titulo"].strip(),
        "sala": sala,
        "seccion": seccion or "",
        "url": t["url"],
        "detalle": " · ".join(l for l in t["lineas"] if l not in (t["titulo"], t["hora"], sala))[:300],
        "fuente": "dom",
    }


def desplazar(page):
    """Scroll hasta abajo para disparar carga diferida."""
    alto = 0
    for _ in range(30):
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(300)
        nuevo = page.evaluate("document.body.scrollHeight")
        if nuevo == alto:
            break
        alto = nuevo
    # botones "ver más" / "cargar más"
    for _ in range(20):
        btn = page.locator("text=/ver m[aá]s|cargar m[aá]s|load more/i").first
        try:
            if not btn.is_visible(timeout=500):
                break
            btn.click()
            page.wait_for_timeout(800)
        except Exception:
            break


def extraer_dom(page, dia_pestana, dump=None):
    desplazar(page)
    if dump:
        dump.write_text(page.content(), encoding="utf-8")
    tarjetas = page.evaluate(JS_EXTRAER, [DIAS_RE, [norm(s) for s in SECCIONES]])
    return [tarjeta_a_funcion(t, dia_pestana) for t in tarjetas if t["titulo"]]


# --------------------------------------------------------------------------
# Detalle de cada película (opcional): precisa sección y sala
# --------------------------------------------------------------------------

def completar_detalles(context, funciones):
    urls = sorted({f["url"] for f in funciones if f["url"] and not f["seccion"]} |
                  {f["url"] for f in funciones if f["url"]})
    page = context.new_page()
    info = {}
    for i, u in enumerate(urls, 1):
        print(f"  [{i}/{len(urls)}] {u}", file=sys.stderr)
        try:
            page.goto(u, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(800)
            texto = page.inner_text("body")
        except Exception as e:
            print(f"    error: {e}", file=sys.stderr)
            continue
        info[u] = {"seccion": detectar_seccion(texto)}
    page.close()
    for f in funciones:
        d = info.get(f["url"])
        if d and d["seccion"] and not f["seccion"]:
            f["seccion"] = d["seccion"]


# --------------------------------------------------------------------------
# Salidas
# --------------------------------------------------------------------------

def deduplicar(funciones):
    vistos, out = set(), []
    for f in funciones:
        k = (f["dia"], f["hora"], norm(f["titulo"]), norm(f["sala"]), f.get("id", ""))
        if k not in vistos:
            vistos.add(k)
            out.append(f)
    return out


def agrupar(funciones):
    prog = defaultdict(lambda: defaultdict(list))
    for f in funciones:
        prog[f["dia"] or "Sin fecha"][f["seccion"] or "Sin sección"].append(f)
    ordenado = OrderedDict()
    for dia in sorted(prog):
        ordenado[dia] = OrderedDict(
            (s, sorted(prog[dia][s], key=lambda f: (f["hora"].zfill(5), f["titulo"])))
            for s in sorted(prog[dia]))
    return ordenado


def nombre_dia(iso):
    m = re.match(r"(\d{4})-(\d\d)-(\d\d)$", iso)
    if not m:
        return iso
    import datetime
    d = datetime.date(*map(int, m.groups()))
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    return f"{dias[d.weekday()]} {d.day} de {meses[d.month]}"


def escribir_md(prog, ruta):
    l = ["# 33° FICValdivia — Programa por día y sección", "", f"Fuente: {URL}", ""]
    for dia, secciones in prog.items():
        l += [f"## {nombre_dia(dia)}", ""]
        for sec, fs in secciones.items():
            l += [f"### {sec}", "", "| Hora | Película | Sala | Notas |", "|---|---|---|---|"]
            for f in fs:
                t = f"[{f['titulo']}]({f['url']})" if f["url"] else f["titulo"]
                notas = " · ".join(x for x in (f.get("subseccion"), f.get("acceso")) if x)
                l.append(f"| {f['hora']} | {t.replace('|', '/')} | {f['sala'].replace('|', '/')} | {notas.replace('|', '/')} |")
            l.append("")
    ruta.write_text("\n".join(l), encoding="utf-8")


def escribir_html(prog, ruta):
    datos = json.dumps(prog, ensure_ascii=False)
    nombres = json.dumps({d: nombre_dia(d) for d in prog}, ensure_ascii=False)
    ruta.write_text(f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Programa FICValdivia</title>
<style>
:root{{--bg:#fafaf7;--fg:#1b1b1b;--mut:#666;--acc:#b3261e;--card:#fff;--line:#e4e2dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151515;--fg:#eee;--mut:#9a9a9a;--acc:#ff7a6e;--card:#1f1f1f;--line:#333}}}}
*{{box-sizing:border-box}} body{{margin:0;font:15px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--fg)}}
header{{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;z-index:1}}
h1{{font-size:18px;margin:0 0 8px}} .tabs{{display:flex;gap:6px;overflow-x:auto;padding-bottom:4px}}
.tabs button{{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:6px 12px;white-space:nowrap;cursor:pointer}}
.tabs button.on{{background:var(--acc);border-color:var(--acc);color:#fff}}
.ctl{{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}} select,input{{padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);flex:1;min-width:140px}}
main{{max-width:900px;margin:0 auto;padding:8px 16px 40px}} h2{{font-size:16px;color:var(--acc);margin:22px 0 6px}}
.f{{display:grid;grid-template-columns:56px 1fr;gap:2px 12px;padding:8px 0;border-bottom:1px solid var(--line)}}
.h{{font-variant-numeric:tabular-nums;font-weight:600}} .t a{{color:inherit}} .s{{grid-column:2;color:var(--mut);font-size:13px}}
.vacio{{color:var(--mut);padding:30px 0;text-align:center}}
</style></head><body>
<header><h1>33° FICValdivia · Programa</h1><div class="tabs" id="tabs"></div>
<div class="ctl"><select id="sec"></select><input id="q" placeholder="Buscar película, dirección, país o sala…"></div></header>
<main id="m"></main>
<script>
const P={datos}, N={nombres}; const dias=Object.keys(P); let dia=dias[0];
const tabs=document.getElementById('tabs'), sel=document.getElementById('sec'), q=document.getElementById('q'), m=document.getElementById('m');
const secs=[...new Set(dias.flatMap(d=>Object.keys(P[d])))].sort();
sel.innerHTML='<option value="">Todas las secciones</option>'+secs.map(s=>`<option>${{s}}</option>`).join('');
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
function pintar(){{
  tabs.innerHTML=['Todos',...dias].map(d=>`<button class="${{d===dia?'on':''}}" data-d="${{d}}">${{d==='Todos'?'Todos':N[d]}}</button>`).join('');
  const texto=q.value.toLowerCase(), s=sel.value; let html='';
  for(const d of (dia==='Todos'?dias:[dia])){{
    let bloque='';
    for(const [sec,fs] of Object.entries(P[d])){{
      if(s&&sec!==s) continue;
      const v=fs.filter(f=>!texto||(f.titulo+' '+f.sala+' '+(f.direccion||'')+' '+(f.pais||'')).toLowerCase().includes(texto));
      if(!v.length) continue;
      bloque+=`<h2>${{esc(sec)}}</h2>`+v.map(f=>`<div class="f"><span class="h">${{esc(f.hora)}}</span>
        <span class="t">${{f.url?`<a href="${{esc(f.url)}}" target="_blank">${{esc(f.titulo)}}</a>`:esc(f.titulo)}}</span>
        <span class="s">${{esc([[f.direccion,f.pais].filter(Boolean).join(', '),f.sala,f.subseccion,f.acceso].filter(Boolean).join(' · '))}}</span></div>`).join('');
    }}
    if(bloque) html+=(dia==='Todos'?`<h1 style="margin-top:28px">${{esc(N[d])}}</h1>`:'')+bloque;
  }}
  m.innerHTML=html||'<p class="vacio">Sin funciones para este filtro.</p>';
}}
tabs.onclick=e=>{{if(e.target.dataset.d){{dia=e.target.dataset.d;pintar();}}}};
sel.onchange=pintar; q.oninput=pintar; pintar();
</script></body></html>""", encoding="utf-8")


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=URL)
    ap.add_argument("--ver", action="store_true", help="mostrar el navegador")
    ap.add_argument("--detalles", action="store_true", help="visitar cada película para precisar la sección")
    ap.add_argument("--dump", action="store_true", help="guardar el HTML de cada día en salida/html/")
    ap.add_argument("--salida", default=str(OUT))
    ap.add_argument("--desde-json", metavar="DIR",
                    help="no navegar: reprocesar respuestas JSON guardadas (p. ej. salida/api)")
    a = ap.parse_args()

    if a.desde_json:
        payloads = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(a.desde_json).glob("*.json"))]
        funciones = funciones_desde_softr(payloads, {}, a.url) or funciones_desde_api(payloads)
        if not funciones:
            sys.exit("No se encontraron funciones en esos JSON.")
        Path(a.salida).mkdir(parents=True, exist_ok=True)
        generar(funciones, Path(a.salida))
        return

    out = Path(a.salida)
    (out / "api").mkdir(parents=True, exist_ok=True)
    if a.dump:
        (out / "html").mkdir(exist_ok=True)

    payloads = []

    log_urls = []

    def capturar(resp):
        try:
            rt = resp.request.resource_type
            if rt in ("image", "font", "stylesheet", "media"):
                return
            log_urls.append(f"{resp.status} {resp.request.method} {rt} {resp.url}")
            ct = resp.headers.get("content-type") or ""
            if "json" not in ct or "manifest.json" in resp.url:
                return
            data = resp.json()
            payloads.append(data)
            nombre = re.sub(r"[^\w.-]+", "_", resp.url.split("://", 1)[-1])[:120]
            (out / "api" / f"{len(payloads):03d}_{nombre}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass

    with sync_playwright() as p:
        opciones = dict(headless=not a.ver, args=["--disable-blink-features=AutomationControlled"])
        if os.environ.get("CHROMIUM_PATH"):
            opciones["executable_path"] = os.environ["CHROMIUM_PATH"]
        else:
            opciones["channel"] = "chromium"  # headless "nuevo": se comporta como un Chrome normal
        browser = p.chromium.launch(**opciones)
        context = browser.new_context(
            locale="es-CL", timezone_id="America/Santiago", viewport={"width": 1366, "height": 900},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"))
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        page.on("console", lambda m: m.type in ("error", "warning") and log_urls.append(f"CONSOLE {m.type}: {m.text[:300]}"))
        page.on("pageerror", lambda e: log_urls.append(f"PAGEERROR {str(e)[:300]}"))
        page.on("requestfailed", lambda r: log_urls.append(f"FAILED {r.method} {r.url} {r.failure}"))
        page.on("response", capturar)

        print(f"Abriendo {a.url}", file=sys.stderr)
        page.goto(a.url, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except PWTimeout:
            pass
        # cerrar banner de cookies / popups si aparecen
        for t in ("Aceptar", "Acepto", "Entendido", "Cerrar", "Accept"):
            try:
                page.get_by_role("button", name=t).first.click(timeout=800)
            except Exception:
                pass

        mapa_softr = esperar_softr(page)
        funciones = []
        pestanas = page.evaluate(JS_PESTANAS_DIA, DIAS_RE)
        print(f"Pestañas de día detectadas: {pestanas or 'ninguna'}", file=sys.stderr)
        if pestanas:
            for i, etiqueta in enumerate(pestanas):
                try:
                    page.locator(f"[data-ficv-dia='{i}']").first.click(timeout=5000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=8000)
                    except PWTimeout:
                        pass
                    page.wait_for_timeout(1000)
                except Exception as e:
                    print(f"  no pude abrir '{etiqueta}': {e}", file=sys.stderr)
                    continue
                dump = out / "html" / f"dia_{i:02d}.html" if a.dump else None
                fs = extraer_dom(page, etiqueta, dump)
                print(f"  {etiqueta}: {len(fs)} funciones", file=sys.stderr)
                funciones += fs
                # algunas webs re-renderizan las pestañas: volver a marcarlas
                page.evaluate(JS_PESTANAS_DIA, DIAS_RE)
        else:
            dump = out / "html" / "programacion.html" if a.dump else None
            funciones = extraer_dom(page, "", dump)
            print(f"  {len(funciones)} funciones en la página", file=sys.stderr)

        desde_softr = funciones_desde_softr(payloads, mapa_softr or {}, a.url)
        desde_api = desde_softr or funciones_desde_api(payloads)
        if len(desde_api) > len(funciones) * 0.8 and desde_api:
            print(f"Usando datos de la API ({len(desde_api)} funciones) en vez del DOM ({len(funciones)}).",
                  file=sys.stderr)
            funciones = desde_api
        for f in funciones:
            if f["url"]:
                f["url"] = urljoin(a.url, f["url"])

        funciones = deduplicar(funciones)
        if a.detalles and not desde_softr:
            print("Visitando fichas de películas…", file=sys.stderr)
            completar_detalles(context, funciones)
        browser.close()
    (out / "api" / "urls.txt").write_text("\n".join(log_urls), encoding="utf-8")

    if not funciones:
        print("No se encontraron funciones. Prueba con --ver --dump y revisa salida/html/ y salida/api/.",
              file=sys.stderr)
        sys.exit(1)

    generar(funciones, out)

if __name__ == "__main__":
    main()
