#!/usr/bin/env python3
"""Programa del 38° FICViña (23–28 nov 2026) → programa-ficvina/programa.json y programa-ficvina/programa.html.

La grilla oficial (fuentes/ficvina/Programacion-FicVina-2026.pdf) es una imagen, así que las funciones están
transcritas a mano aquí. La app es la misma plantilla de FICValdivia con los textos y salas de Viña.
"""
import json, re
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PDF = "https://cinevina.cl/wp-content/uploads/2026/11/Programacion-FicVina-2026.pdf"
LIBRE = "Entrada liberada (con inscripción previa)"
AIRE = "Entrada liberada · aire libre"

TM, CA, CM, PV = "Teatro Municipal", "Cine Arte", "Cinemark", "Palacio Vergara"
FIC, DOC = "Competencia Largometraje Iberoamericano de Ficción", "Competencia Largometraje Iberoamericano Documental"
PULSO, CREANDO = "Competencia Pulso Iberoamericano", "Competencia Creando Universos"
HABITAR, DESDE = "Competencia Habitar", "Competencia Desde Aquí"
JOYA, UAL, LPT = "Muestra Joya", "Muestra Una América Latina", "Muestra Latinoamérica para Todos"
RUCA = "Muestra RUCA (escuelas de cine)"

# (día, hora, sala, sección, título, dirección, año, país, minutos, calificación, género[, extra])
UNO = [
    # Teatro Municipal
    (23, "19:00", TM, "Ceremonias", "La frontera", "Ricardo Larraín", "1991", "Chile", 118, "+14", "Ficción",
     {"premiere": "Ceremonia y gala de inauguración · película inaugural (35° aniversario)", "bloque": 150}),
    (24, "16:00", TM, UAL, "La cordillera de los sueños", "Patricio Guzmán", "2019", "Chile", 84, "+7", "Documental"),
    (24, "18:30", TM, JOYA, "Siempre soy tu animal materno", "Valentina Maurel", "2026", "Costa Rica", 180, "+14", "Ficción"),
    (25, "15:00", TM, "Función especial", "Matapanki", 'Diego "Mapache" Fuentes', "2025", "Chile", 71, "+14", "Ficción/Drama"),
    (25, "17:00", TM, JOYA, "Sorda", "Eva Libertad", "2025", "España", 100, "TE", "Ficción"),
    (25, "19:30", TM, JOYA, "La muerte no tiene dueño", "Jorge Thielen Armand", "2025", "Venezuela", 106, "+14", "Ficción"),
    (26, "17:00", TM, UAL, "La teta asustada", "Claudia Llosa", "2009", "Perú", 95, "+14", "Ficción/Drama"),
    (26, "19:30", TM, JOYA, "La ilusión de un verano sin fin", "Alessandra Sanguinetti", "2026", "Argentina", 94, "TE", "Documental"),
    (27, "16:30", TM, UAL, "El laberinto del fauno", "Guillermo del Toro", "2006", "España", 120, "+14", "Ficción"),
    (27, "19:30", TM, JOYA, "Motel Paraíso", "José Eduardo Castilla Ponce", "2025", "México", 90, "+12", "Documental"),
    (28, "12:30", TM, LPT, "La fabulosa máquina del tiempo", "Eliza Capai", "2026", "Brasil", 70, "TE", "Documental"),
    (28, "14:30", TM, "Muestra especial País Vasco", "Karmele", "Asier Altuna", "2026", "España", 114, "+12", "Ficción"),
    (28, "19:30", TM, "Ceremonias", "La bola negra", "Javier Calvo y Javier Ambrossi", "2026", "España", 155, "+16", "Ficción",
     {"premiere": "Ceremonia de clausura y premiación · película de clausura · Estreno nacional", "bloque": 185}),
    # Cine Arte
    (24, "15:00", CA, FIC, "Uatana", "Claudio Marques", "2026", "Brasil", 100, "+16", "Ficción", {"premiere": "Premiere mundial"}),
    (24, "17:30", CA, DOC, "Plata o mierda", "Toia Bonino y Marcos Joubert", "2026", "Argentina", 98, "+14", "Documental"),
    (24, "20:00", CA, FIC, "Nunkui", "Verenice Benítez", "2026", "Ecuador", 91, "+16", "Ficción"),
    (25, "15:00", CA, DOC, "El coloquio de los pájaros", "Sofía Velázquez Núñez", "2026", "Perú", 60, "TE", "Documental",
     {"premiere": "Premiere nacional"}),
    (25, "17:30", CA, FIC, "Pin de Fartie", "Alejo Moguillansky", "2025", "Argentina", 106, "TE", "Ficción"),
    (25, "20:00", CA, DOC, "Los vencedores", "Pablo Aparo", "2025", "Argentina", 96, "TE", "Documental"),
    (26, "17:30", CA, DOC, "Mailin", "María Silvia Esteve", "2025", "Argentina", 87, "+14", "Documental"),
    (26, "20:00", CA, FIC, "Guerra de verano", "Alicia Scherson", "2026", "Argentina", 104, "+14", "Ficción",
     {"premiere": "Premiere nacional"}),
    (27, "17:30", CA, FIC, "La anatomía de los caballos", "Daniel Vilches Toche", "2025", "Perú", 107, "+12", "Documental"),
    (27, "20:00", CA, DOC, "Relicto", "Guillermo Quintero", "2026", "Colombia", 97, "TE", "Documental"),
    (28, "13:00", CA, LPT, "Ogú y Mampato en Rapa Nui", "Alejandro Rojas Téllez", "2002", "Chile", 76, "TE", "Animación"),
    # Cinemark (largos de Habitar y Desde Aquí)
    (26, "17:30", CM, HABITAR, "Tres tristes tías", "Carlos Villegas Leiva", "2026", "Chile", 72, "+12", "Documental"),
    (27, "15:00", CM, LPT, "Olivia y el terremoto invisible", "Irene Iborra Rizo", "2025", "España", 71, "TE", "Animación"),
    (27, "17:30", CM, HABITAR, "Réplicas", "Diego González-Durney", "2026", "Chile", 87, "+12", "Ficción"),
    (24, "20:00", CM, DESDE, "Cocaína negra", "Cristóbal Valenzuela", "2026", "Chile", 83, "+14", "Documental"),
    (25, "20:00", CM, DESDE, "Lyn Mía", "Camila Aboitiz", "2026", "Chile", 61, "TE", "Documental"),
    (26, "20:00", CM, DESDE, "Asteroide 2518", "Amanda Rutllant", "2026", "Chile", 63, "TE", "Documental",
     {"premiere": "Estreno mundial"}),
    (27, "20:00", CM, DESDE, "Población flotante", "Carlos Araya Díaz", "2026", "Chile", 66, "TE", "Documental"),
    # Viña a cielo abierto (funciones al aire libre antes y durante el festival)
    (20, "19:00", "Playa Los Marineros", JOYA, "Ciudad Jardín", "Javier Zoro", "2026", "Chile", 99, "TE", "Documental", {"acceso": AIRE}),
    (21, "19:30", "Muelle Vergara", UAL, "31 minutos, la película", "Álvaro Díaz y Pedro Peirano", "2008", "Chile", 87, "TE", "Ficción",
     {"acceso": AIRE}),
    (27, "19:30", "Calle Von Schroeder", JOYA, "El partido", "Juan Cabral y Santiago Franco", "2026", "Argentina", 91, "TE", "Documental",
     {"acceso": AIRE}),
]

# Programas de cortos: (día, hora, sala, sección, minutos del programa, calificación, [(título, dirección, país/región, género)])
PROGRAMAS = [
    (24, "15:00", CM, PULSO, 119, "+16", [
        ("Allá en el cielo", "Roddy Dextre", "Perú", ""), ("Las visitas de Camilo", "Itatí Olmedo", "Argentina", ""),
        ("Paulina", "Marcela Bruna", "Chile", ""), ("Tauromaquia", "Christopher Sánchez", "México", ""),
        ("Sol menor", "André Silva Santos", "Portugal", ""),
        ("La procesión de los ausentes", "Jaime Díaz y Mauricio Matusalenes", "Chile", "")]),
    (24, "17:30", CM, CREANDO, 96, "TE", [
        ("Lodo", "Joseph Specker Nys", "Uruguay", "Animación"), ("Tinku", "Román Nina Nina", "Bolivia", "Animación"),
        ("Paqarina", "Sussan Yerathel Ccorimanya Tinta", "Perú", "Animación"),
        ("O Jardim Mágico", "Naira Carneiro", "Brasil", "Animación"),
        ("Azul: la última semilla", "Aline Romero", "España", "Animación"),
        ("Garantía de por vida", "Daniel Lobos", "Chile", "Animación"), ("Pan", "Miguel León", "Colombia", "Animación"),
        ("Trabajo hecho", "Jaime Freire Valenzuela", "Chile", "Animación")]),
    (25, "15:00", CM, CREANDO, 86, "+14", [
        ("El cuerpo de Cristo", "Bea Lema", "España", "Animación"), ("Pinchu es así", "Carmen Córdoba", "España", "Animación"),
        ("Mensajeras sin mensaje", "Daniela Maldonado", "Chile", "Animación"),
        ("No prendas la luz", "Carina Vanessa Rodríguez", "México", "Animación"),
        ("Decaer", "Juan Camilo González", "Colombia", "Animación"), ("TV Entreaberta", "Mateus Compart", "Brasil", "Animación"),
        ("A menina que queria ser pedra", "Jackson Teixeira", "Brasil", "Animación"),
        ("El tamagochi escarlata", "Francisco Visceral Rivera", "Chile", "Animación"),
        ("Mnema", "Inês Costa y Carolina Bonzinho", "Brasil", "Animación"),
        ("Emechiche, el renacer de los cabeciblancos", "Juan Camilo González", "Colombia", "Animación")]),
    (25, "17:30", CM, HABITAR, 86, "+14", [
        ("Norte claro, sur oscuro", "Francisca Amigo Moraga", "Chile (Maule)", "Documental"),
        ("La ofrenda", "Samuel González", "Chile (Los Ríos)", "Ficción"),
        ("Caudal", "Develo Colectivo", "Chile (Valparaíso)", "Documental"),
        ("Caerá el Morro y marcharán sus hijos", "Oscar Marín Sepúlveda", "Chile (Arica)", "Documental"),
        ("Criaturas que gritan", "Martín Durán", "Chile (Valparaíso)", "Documental")]),
    (26, "15:00", CM, PULSO, 103, "+16", [
        ("Ixquic", "Elvis Caj", "Guatemala", "Ficción"), ("Miriam", "Karla Condado", "México", "Documental"),
        ("En otra Palestina", "Yaela Gottlieb", "Perú", "Documental"), ("Presépio", "Felipe Bibian", "Brasil", "Ficción"),
        ("Videoclub 2001", "Guillermo Polo", "España", "Ficción"),
        ("Baisanos", "Andrés y Francisca Khamis Giacoman", "Chile", "Documental")]),
    (26, "15:00", CA, RUCA, 44, "+14", [
        ("Me vas a estar esperando", "Conam Calderón (Pontificia Universidad Católica de Chile)", "Chile", ""),
        ("Capturar la caída", "Erik Alexander (Universidad de los Andes)", "Chile", ""),
        ("Ross", "Florencia Vega (Universidad de Chile)", "Chile", ""),
        ("Zozobra", "Agus Amparo Muñoz (Universidad de Valparaíso)", "Chile", ""),
        ("Mi gran noche", "Florencia Lucero (Universidad Mayor)", "Chile", ""),
        ("H4BLAM#", "Benjamín Cuevas (Universidad Diego Portales)", "Chile", ""),
        ("Ven", "Facundo Daniel Alexander (Universidad Academia de Humanismo Cristiano)", "Chile", "")]),
    (27, "15:00", CA, RUCA, 57, "+14", [
        ("¿Quién mató a Gaete?", "Pablo E. Alvarado S. (Universidad del Desarrollo)", "Chile", ""),
        ("Herederas del mar", "Trinidad Toledo (Universidad de Viña del Mar)", "Chile", ""),
        ("Te quiero lejos", "Romina Espinoza (Universidad de las Américas)", "Chile", ""),
        ("Enajenado", "Soledad Jaramillo (Universidad Católica de la Santísima Concepción)", "Chile", ""),
        ("Como chispitas", "Amparo Chaparro (UNIACC)", "Chile", ""),
        ("El pan nuestro de cada día", "Tatiana Farías (Universidad de O'Higgins)", "Chile", ""),
        ("Captura", "Ignacia Manzano Daguerre (Universidad Austral de Chile)", "Chile", "")]),
    (28, "15:00", CA, "Muestra Conmemoración Día del Cine Chileno", 105, "+14", [
        ("El jardín de los pañuelos blancos", "Álvaro Covacevich", "Chile", "Documental · 7 min · TE"),
        ("Detrás de la lluvia", "Valeria Sarmiento", "Chile", "Ficción · 98 min · +14")]),
]

# Palacio Vergara: Diálogos de cine y Real Chile (charlas). La duración no está en la grilla.
CHARLAS = [
    (24, "11:00", "Diálogos de cine", "La imagen imperfecta: Manuel Claro y la dirección de fotografía",
     "Modera: Miguel Araya y José Miño. Expone: Manuel Claro."),
    (24, "13:00", "Diálogos de cine", "Retrospectiva: el cine de Patricio Guzmán",
     "Modera: Marcelo Morales. Expone: Alexandra Galvis y Marisol Águila."),
    (24, "16:00", "Diálogos de cine", "Simbiosis cinematográfica: cinetecas y cineclubes",
     "Modera: Lucas Beckett Baeza. Exponen: Marcelo Morales, Verónica Muñoz, Carlos Ovando."),
    (25, "11:00", "Diálogos de cine", "El reencuentro: festivales en diálogo",
     "Modera: Francisca Droppelmann. Exponen: Edward Venero, Mariana Rubio y Sol San Julián."),
    (25, "13:00", "Diálogos de cine", "El reencuentro: cineastas iberoamericanos en diálogo",
     "Modera: Lola Contreras Bustamante. Exponen: Simón González, Javier Andrade, Pilar Colomé, Elena Vilardel, "
     "Alejandro Irías, Simón Franco, Lena Fernández, Pablo Dotta."),
    (26, "11:00", "Diálogos de cine", "Animación: más allá del público infantil",
     "Modera: Bambú Orellana. Exponen: Kike Ortega, Isidora Fajardo y Alejandra Moffat."),
    (26, "13:00", "Diálogos de cine", "La memoria del color: colorimetría en el cine análogo y digital",
     "Modera: Verónica Muñoz. Expone: Chema Alba."),
    (26, "15:00", "Real Chile", "Inauguración y ponencia: Cine, IA y realidades extendidas",
     "En torno a Cine, Inteligencia Artificial y Realidades extendidas: representación, mitos y desafíos."),
    (26, "17:00", "Diálogos de cine", "Master class: usos, retos y posibilidades de la IA en el relato de no ficción",
     "Modera: María Angélica Pacheco."),
    (27, "11:00", "Diálogos de cine", "El guionista hoy: de la página en blanco a la pantalla",
     "Modera: Felipe Salinas. Exponen: Gabriela Maire, Alejandra Moffat, Josefina Fernández y Susana Quiroz."),
    (27, "13:00", "Diálogos de cine", "Retrospectiva: Astro LX",
     "Modera: David Guzmán. Expone: Michelle Couttolenc y Jaime Baksht, Astro LX."),
    (27, "15:00", "Real Chile", "Ponencias: Cine, IA y realidades extendidas",
     "En torno a Cine, Inteligencia Artificial y Realidades extendidas: representación, mitos y desafíos."),
    (27, "17:00", "Diálogos de cine", "Master class Jorge Baradit: riesgos de la IA en la creación artística",
     "Modera: Pepe Rovano."),
]


def slug(t):
    t = t.lower()
    for a, b in zip("áéíóúüñ", "aeiouun"):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def base(d, hora, sala, sec):
    comp = sec.startswith("Competencia")
    return {"dia": f"2026-11-{d:02d}", "hora": hora, "sala": sala,
            "seccion": "En Competencia" if comp else sec, "subseccion": sec if comp else "",
            "acceso": LIBRE, "url": PDF, "fuente": "pdf", "estado": "", "idioma": "", "sinopsis": "", "premiere": ""}


def funciones():
    out = []
    for t in UNO:
        d, hora, sala, sec, tit, dire, anio, pais, mins, calif, gen = t[:11]
        x = t[11] if len(t) > 11 else {}
        f = base(d, hora, sala, sec)
        f.update(titulo=tit, direccion=dire, anio=anio, pais=pais, id=slug(tit), duracion=x.get("bloque", mins),
                 duracion_film=f"{mins}'", formato=f"{gen} · {calif}", sesion=tit, premiere=x.get("premiere", ""))
        if "acceso" in x:
            f["acceso"] = x["acceso"]
        out.append(f)
    for d, hora, sala, sec, mins, calif, films in PROGRAMAS:
        ses = ", ".join(t for t, *_ in films)
        for tit, dire, pais, gen in films:
            f = base(d, hora, sala, sec)
            f.update(titulo=tit, direccion=dire, anio="", pais=pais, id=slug(tit), duracion=mins,
                     duracion_film="", formato=" · ".join(x for x in (gen, calif) if x) if "min" not in gen else gen, sesion=ses)
            out.append(f)
    for d, hora, sec, tit, quien in CHARLAS:
        f = base(d, hora, PV, sec)
        f.update(titulo=tit, direccion="", anio="", pais="", id=slug(tit), duracion=0, duracion_film="",
                 formato="Charla", sesion=tit, sinopsis=quien)
        out.append(f)
    ids = [f["id"] for f in out]
    assert len(ids) == len(set(ids)), "ids repetidos"
    return sorted(out, key=lambda f: (f["dia"], f["hora"], f["sala"], f["titulo"]))


def reemplazar(s, viejo, nuevo, n=1):
    assert s.count(viejo) >= n, viejo
    return s.replace(viejo, nuevo)


def html(F, fecha):
    s = (RAIZ / "plantilla.html").read_text(encoding="utf-8")
    s = reemplazar(s, "<title>Programa 33° FICValdivia</title>", "<title>Programa 38° FICViña</title>")
    s = reemplazar(s, "<h1>33° <span>FICValdivia</span> · Programa</h1>", "<h1>38° <span>FICViña</span> · Programa</h1>")
    s = reemplazar(s, "12 al 18 de octubre de 2026", "23 al 28 de noviembre de 2026 · entrada liberada")
    s = re.sub(r"<footer>.*?</footer>", f'<footer>Datos de la <a href="{PDF}">grilla oficial del 38° FICViña</a> '
               f'(cinevina.cl), transcritos el {fecha}. Todas las funciones son gratuitas con inscripción previa en '
               '<a href="https://www.passline.com/sitio/ilustre-municipalidad-de-vina-del-mar">Passline</a>. '
               'La duración de cada bloque es la de la película o del programa de cortos (las ceremonias suman unos 30 min); '
               'las charlas de Palacio Vergara no traen duración y se cuentan como 90 min.</footer>', s, flags=re.S)
    s = reemplazar(s, "const F=__DATA__;", "const F=" + json.dumps(F, ensure_ascii=False) + ";")
    s = re.sub(r"const LB=\{.*?\};", "const LB={};", s, count=1, flags=re.S)
    s = re.sub(r"const PRESENTE=new Set\(\[.*?\]\);", "const PRESENTE=new Set([]);", s, count=1, flags=re.S)
    s = reemplazar(s, 'const ZONAS=[[/UACh/i,"UACh"],[/Teatro Cervantes/i,"Centro (Teatro Cervantes)"]];',
                   'const ZONAS=[[/Teatro Municipal|Cine Arte|Palacio Vergara/i,"Plaza Vergara"],[/Cinemark/i,"Cinemark (Av. Libertad)"]];')
    s = reemplazar(s, 'const LEJOS=new Set(["Centro (Teatro Cervantes)"]);', 'const LEJOS=new Set(["Cinemark (Av. Libertad)"]);')
    s = s.replace("// Zonas: todo lo de la UACh queda cerca entre sí; Teatro Cervantes está lejos del resto.",
                  "// Zonas: Teatro Municipal, Cine Arte y Palacio Vergara están a pasos; Cinemark (Av. Libertad 1348) queda lejos.")
    s = reemplazar(s, 'o.t.dia<"2026-10-12"', 'o.t.dia<"2026-11-20"')
    # todo es gratis y la grilla no indica cineastas presentes: fuera esas casillas
    s = reemplazar(s, '+chip("*libre","Entrada liberada","esp")+chip("*presente","Cineasta presente","esp")', "")
    s = reemplazar(s, '<label class="sololista"><input id="libre" type="checkbox"> Solo entrada liberada</label>',
                   '<input id="libre" type="checkbox" hidden>')
    s = s.replace("ficv33", "ficvina38").replace("de octubre", "de noviembre")
    s = reemplazar(s, '"33° FICValdivia · Calendario de "', '"38° FICViña · Calendario de "')
    assert "__" not in re.sub(r"__(proto|init)__", "", s.split("const F=")[0]), "quedó un marcador sin reemplazar"
    return s


def main():
    F = funciones()
    out = RAIZ / "programa-ficvina"
    out.mkdir(exist_ok=True)
    (out / "programa.json").write_text(json.dumps(F, ensure_ascii=False, indent=1), encoding="utf-8")
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    hoy = date.today()
    (out / "programa.html").write_text(html(F, f"{hoy.day} de {meses[hoy.month - 1]} de {hoy.year}"), encoding="utf-8")
    print(len(F), "funciones /", len({(f['dia'], f['hora'], f['sala']) for f in F}), "bloques →", out)


if __name__ == "__main__":
    main()
