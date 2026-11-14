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


# Letterboxd: slug verificado por dirección (curl a letterboxd.com/film/<slug>/ y comparar twitter:data1)
LB = {"31-minutos-la-pelicula": "31-minutos-the-movie", "a-menina-que-queria-ser-pedra": "a-menina-que-queria-ser-pedra", "baisanos": "baisanos", "ciudad-jardin": "ciudad-jardin", "decaer": "decaer", "detras-de-la-lluvia": "detras-de-la-lluvia", "el-coloquio-de-los-pajaros": "el-coloquio-de-los-pajaros", "el-cuerpo-de-cristo": "el-cuerpo-de-cristo", "el-laberinto-del-fauno": "pans-labyrinth", "el-partido": "el-partido-2026", "el-tamagochi-escarlata": "el-tamagochi-escarlata", "emechiche-el-renacer-de-los-cabeciblancos": "emechiche-el-renacer-de-los-cabeciblancos", "en-otra-palestina": "en-otra-palestina", "guerra-de-verano": "summer-war", "ixquic": "ixquic", "karmele": "karmele", "la-anatomia-de-los-caballos": "la-anatomia-de-los-caballos", "la-bola-negra": "la-bola-negra", "la-cordillera-de-los-suenos": "the-cordillera-of-dreams", "la-fabulosa-maquina-del-tiempo": "the-fabulous-time-machine", "la-frontera": "the-frontier-1991", "la-ilusion-de-un-verano-sin-fin": "la-ilusion-de-un-verano-sin-fin", "la-muerte-no-tiene-dueno": "death-has-no-master", "la-ofrenda": "la-ofrenda-2026", "la-teta-asustada": "the-milk-of-sorrow", "las-visitas-de-camilo": "las-visitas-de-camilo", "los-vencedores": "los-vencedores", "mailin": "mailin", "matapanki": "matapanki", "me-vas-a-estar-esperando": "me-vas-a-estar-esperando", "miriam": "miriam-2026", "mnema": "mnema", "motel-paraiso": "motel-paraiso-2026", "no-prendas-la-luz": "no-prendas-la-luz", "nunkui": "nunkui-2026", "o-jardim-magico": "o-jardim-magico", "ogu-y-mampato-en-rapa-nui": "ogu-y-mampato-en-rapa-nui", "olivia-y-el-terremoto-invisible": "olivia-y-el-terremoto-invisible", "pin-de-fartie": "pin-de-fartie", "pinchu-es-asi": "pinchu-es-asi", "plata-o-mierda": "plata-o-mierda", "poblacion-flotante": "floating-population", "presepio": "presepio", "quien-mato-a-gaete": "quien-mato-a-gaete", "relicto": "relicto", "siempre-soy-tu-animal-materno": "forever-your-maternal-animal", "sol-menor": "sol-menor-2025", "sorda": "deaf-2025", "tinku": "tinku-2025", "tres-tristes-tias": "tres-tristes-tias", "tv-entreaberta": "tv-entreaberta", "videoclub-2001": "videoclub-2001"}


# Ficha: cinevina.cl no tiene página por película (salvo Karmele); se enlaza la noticia de su sección que la presenta.
# Sin noticia → sin enlace.
FICHA = {
"31-minutos-la-pelicula": "https://cinevina.cl/el-cine-sale-a-la-calle-ficvina-se-toma-playas-muelle-y-centro-de-vina-del-mar/",
"a-menina-que-queria-ser-pedra": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"alla-en-el-cielo": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"asteroide-2518": "https://cinevina.cl/ficvina-reune-cinco-miradas-sobre-el-chile-de-hoy-en-la-competencia-desde-aqui/",
"azul-la-ultima-semilla": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"baisanos": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"caera-el-morro-y-marcharan-sus-hijos": "https://cinevina.cl/ficvina-explora-los-territorios-y-las-identidades-locales-en-la-competencia-habitar/",
"caudal": "https://cinevina.cl/ficvina-explora-los-territorios-y-las-identidades-locales-en-la-competencia-habitar/",
"ciudad-jardin": "https://cinevina.cl/el-cine-sale-a-la-calle-ficvina-se-toma-playas-muelle-y-centro-de-vina-del-mar/",
"cocaina-negra": "https://cinevina.cl/ficvina-reune-cinco-miradas-sobre-el-chile-de-hoy-en-la-competencia-desde-aqui/",
"criaturas-que-gritan": "https://cinevina.cl/ficvina-explora-los-territorios-y-las-identidades-locales-en-la-competencia-habitar/",
"decaer": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"el-coloquio-de-los-pajaros": "https://cinevina.cl/ficvina-reune-historias-de-resistencia-memoria-y-culturas-en-su-competencia-documental-iberoamericana/",
"el-cuerpo-de-cristo": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"el-laberinto-del-fauno": "https://cinevina.cl/38-ficvina-anuncia-una-america-latina-franja-especial-que-reunira-peliculas-emblematicas-en-el-teatro-municipal/",
"el-partido": "https://cinevina.cl/el-cine-sale-a-la-calle-ficvina-se-toma-playas-muelle-y-centro-de-vina-del-mar/",
"el-tamagochi-escarlata": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"emechiche-el-renacer-de-los-cabeciblancos": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"en-otra-palestina": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"garantia-de-por-vida": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"guerra-de-verano": "https://cinevina.cl/competencia-largometraje-iberamericano-de-ficcion/",
"ixquic": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"karmele": "https://cinevina.cl/karmele/",
"la-anatomia-de-los-caballos": "https://cinevina.cl/competencia-largometraje-iberamericano-de-ficcion/",
"la-bola-negra": "https://cinevina.cl/la-bola-negra-premiada-en-cannes-y-carta-de-espana-al-oscar-cerrara-el-38-ficvina/",
"la-cordillera-de-los-suenos": "https://cinevina.cl/38-ficvina-anuncia-una-america-latina-franja-especial-que-reunira-peliculas-emblematicas-en-el-teatro-municipal/",
"la-frontera": "https://cinevina.cl/ficvina-anuncia-su-38a-edicion-con-la-exhibicion-de-la-frontera-comopelicula-inaugural/",
"la-ilusion-de-un-verano-sin-fin": "https://cinevina.cl/38-ficvina-presenta-joya-con-cinco-aclamados-estrenos-del-cine-iberoamericano/",
"la-muerte-no-tiene-dueno": "https://cinevina.cl/38-ficvina-presenta-joya-con-cinco-aclamados-estrenos-del-cine-iberoamericano/",
"la-ofrenda": "https://cinevina.cl/ficvina-explora-los-territorios-y-las-identidades-locales-en-la-competencia-habitar/",
"la-procesion-de-los-ausentes": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"la-teta-asustada": "https://cinevina.cl/38-ficvina-anuncia-una-america-latina-franja-especial-que-reunira-peliculas-emblematicas-en-el-teatro-municipal/",
"las-visitas-de-camilo": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"lodo": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"los-vencedores": "https://cinevina.cl/ficvina-reune-historias-de-resistencia-memoria-y-culturas-en-su-competencia-documental-iberoamericana/",
"lyn-mia": "https://cinevina.cl/ficvina-reune-cinco-miradas-sobre-el-chile-de-hoy-en-la-competencia-desde-aqui/",
"mailin": "https://cinevina.cl/ficvina-reune-historias-de-resistencia-memoria-y-culturas-en-su-competencia-documental-iberoamericana/",
"matapanki": "https://cinevina.cl/el-cine-sale-a-la-calle-ficvina-se-toma-playas-muelle-y-centro-de-vina-del-mar/",
"mensajeras-sin-mensaje": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"miriam": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"mnema": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"motel-paraiso": "https://cinevina.cl/38-ficvina-presenta-joya-con-cinco-aclamados-estrenos-del-cine-iberoamericano/",
"no-prendas-la-luz": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"norte-claro-sur-oscuro": "https://cinevina.cl/ficvina-explora-los-territorios-y-las-identidades-locales-en-la-competencia-habitar/",
"nunkui": "https://cinevina.cl/competencia-largometraje-iberamericano-de-ficcion/",
"o-jardim-magico": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"pan": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"paqarina": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"paulina": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"pin-de-fartie": "https://cinevina.cl/competencia-largometraje-iberamericano-de-ficcion/",
"pinchu-es-asi": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"plata-o-mierda": "https://cinevina.cl/ficvina-reune-historias-de-resistencia-memoria-y-culturas-en-su-competencia-documental-iberoamericana/",
"poblacion-flotante": "https://cinevina.cl/ficvina-reune-cinco-miradas-sobre-el-chile-de-hoy-en-la-competencia-desde-aqui/",
"presepio": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"relicto": "https://cinevina.cl/ficvina-reune-historias-de-resistencia-memoria-y-culturas-en-su-competencia-documental-iberoamericana/",
"replicas": "https://cinevina.cl/ficvina-reune-cinco-miradas-sobre-el-chile-de-hoy-en-la-competencia-desde-aqui/",
"siempre-soy-tu-animal-materno": "https://cinevina.cl/38-ficvina-presenta-joya-con-cinco-aclamados-estrenos-del-cine-iberoamericano/",
"sol-menor": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"sorda": "https://cinevina.cl/38-ficvina-presenta-joya-con-cinco-aclamados-estrenos-del-cine-iberoamericano/",
"tauromaquia": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/",
"tinku": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"trabajo-hecho": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"tres-tristes-tias": "https://cinevina.cl/ficvina-explora-los-territorios-y-las-identidades-locales-en-la-competencia-habitar/",
"tv-entreaberta": "https://cinevina.cl/ficvina-celebra-la-imaginacion-y-la-diversidad-de-la-animacion-en-la-competencia-creando-universos/",
"uatana": "https://cinevina.cl/competencia-largometraje-iberamericano-de-ficcion/",
"videoclub-2001": "https://cinevina.cl/ficvina-presenta-doce-cortometrajes-en-la-competencia-pulso-iberoamericano/"
}


# Sinopsis: de las noticias de cada sección en cinevina.cl (sin la frase de día y hora)
SINOPSIS = {
"31-minutos-la-pelicula": "Tulio Triviño, Bodoque y el resto del equipo emprenden una aventura para rescatar a Juanín Juan Harry, secuestrado por la malvada Cachirula, en una de las historias que llevó al popular universo de la serie chilena a la pantalla grande.",
"a-menina-que-queria-ser-pedra": "Un niño curioso y una niña serena se encuentran a orillas de un lago. Allí surgen reflexiones sobre la vida de manera sutil e inesperada. Después de todo, ¿qué significa ser una piedra?",
"alla-en-el-cielo": "En las afueras de Lima, Chito, de 11 años, cuida las palomas mensajeras que su hermano utiliza para el tráfico de drogas. Cuando la violencia destroza su infancia, el duelo y un frágil gesto de humanidad abren la posibilidad de otro destino.",
"asteroide-2518": "El descubrimiento de documentos inéditos sobre su bisabuelo astrofísico lleva a la propia directora a iniciar una investigación cinematográfica que pronto se ve amenazada por una enfermedad autoinmune. La búsqueda de una figura del pasado se convierte así también en un relato sobre el cuerpo, la memoria y la propia experiencia de hacer una película.",
"azul-la-ultima-semilla": "Han pasado años desde las últimas lluvias. Las semillas mueren y con ellas, la vida. Los pocos supervivientes emigraron al norte buscando agua. Pero Azul, joven guardiana, imagina un futuro diferente.",
"baisanos": "Siguiendo a hinchas del Club Deportivo Palestino, surge un diálogo sobre identidad y retorno que une dos territorios lejanos en celebración y sueños.",
"caera-el-morro-y-marcharan-sus-hijos": "Durante años, las imágenes no han existido en la ciudad de Arica. Cuando un joven lugareño recibe una fotografía por encomienda, inicia una búsqueda que lo conduce entre postales y derivas hacia el Morro de Arica.",
"caudal": "En un relato personal, la protagonista contrasta los recuerdos de una infancia próspera en el pueblo de Hierro Viejo con las huellas de un presente deteriorado a causa de la sequía.",
"ciudad-jardin": "Ante la inminente venta de la casa de su madre, el director emprende una investigación sobre el jardín familiar que termina convirtiéndose en un recorrido por la historia y el presente de Viña del Mar. Entre plantas, recuerdos y relaciones con la naturaleza, la película también observa las tensiones de clase, pertenencia e identidad que atraviesan la ciudad.",
"cocaina-negra": "A partir del hallazgo de cintas de audio grabadas por Eugenio Berríos, conocido como el “Químico de Pinochet”, el documental reconstruye el ascenso y caída de una figura vinculada a algunos de los episodios más oscuros de la historia reciente de Chile. Entre dictadura, sustancias letales y narcotráfico, la película se aproxima a una vida marcada por la violencia política y su propia autodestrucción.",
"criaturas-que-gritan": "Un viaje por la escena punk de la Quinta Región, tejido a través de las voces de quienes habitan los espacios más subterráneos de una comunidad que se rehúsa a desaparecer.",
"decaer": "“Gracias a los Chinos por la pólvora, parece que la hubieran hecho para mí”.",
"el-coloquio-de-los-pajaros": "En un mundo sumido en la oscuridad, un grupo de viejos anarco-poetas debe vivir en la clandestinidad. A través de reuniones secretas, poesía y danza, sus integrantes buscan adoptar identidades no humanas y convertir la amistad en una forma de insubordinación. Inspirada en el mito sufí del mismo nombre, esta fábula documental propone una exploración poética de la resistencia frente al orden establecido.",
"el-cuerpo-de-cristo": "Adela padece un trastorno mental que no reconoce como tal, lo que la lleva a buscar respuestas en la religión y los rituales populares. Se siente incomprendida tanto por su familia como por el sistema médico y psiquiátrico, donde la medicación se presenta como la solución absoluta a todos sus problemas. Sin embargo, lo que realmente necesita es alguien que escuche lo que le está sucediendo. Adela cree que está siendo vigilada y percibe una presencia que, en ocasiones, la toca y le hace daño. El único espacio donde su realidad parece encontrar sentido es en la religión, lo que la impulsa a visitar a un curandero, a quien le confiesa cómo y cuándo comenzó todo.",
"el-laberinto-del-fauno": "A 20 años de su estreno (3 premios Oscar), la película de Guillermo del Toro combina fantasía y realidad en la España de la posguerra, usando el universo fantástico como vía para abordar la violencia, el autoritarismo y la resistencia frente a la represión.",
"el-partido": "La película reconstruye el histórico encuentro entre Argentina e Inglaterra en el Mundial de México 1986, a partir de imágenes de archivo y de un partido convertido en memoria colectiva, pero también como expresión de una relación marcada por más de dos siglos de encuentros y conflictos.",
"el-tamagochi-escarlata": "¡Un crimen ha ocurrido en la sala del 4B! Una compañera sufre el robo de un invaluable y preciado juguete: el Tamagochi Escarlata, por lo que Iñaki y su amigo tortuga Cecilio se transforman en detectives de los años 40 para resolver el misterio.",
"emechiche-el-renacer-de-los-cabeciblancos": "Teotiste ha decidido que no quiere seguir viviendo sola en el campo luego de la desaparición de su marido. Aún así, una fuerza que no entiende, no le permite partir sin antes dejar algo hecho en vida.",
"en-otra-palestina": "Unos niños nadan en el río Jordán de camino a Jerusalén. Es verano y las plantas dan frutas. Hay caminos en todas partes. Personas y recuerdos a la espera de ser nombrados. Es año nuevo en Palestina.",
"garantia-de-por-vida": "En una ciudad donde todo es descartado, una niña de plástico debe escapar antes de ser destruida por su calzado defectuoso. En su huida encuentra refugio en una zapatería olvidada, donde conoce a un artesano que le enseñará que nadie es desechable.",
"guerra-de-verano": "Hugo, un estadounidense campeón de juegos de guerra de tablero y especialista en recreaciones del Tercer Reich, llega a la playa para disfrutar de unas vacaciones tranquilas. Sin embargo, la misteriosa desaparición de otro turista altera la aparente calma y hace que las fronteras entre el juego y la vida real comiencen a desdibujarse. El paisaje soleado se transforma progresivamente en un escenario inquietante, tan amenazante como la propia mente del protagonista.",
"ixquic": "En las montañas, Ixquic camina entre las sombras de un futuro incierto. hasta que el río llora sangre y el fuego de la verdad despierta en ella.",
"karmele": "Ambientada a partir de 1937, en plena Guerra Civil Española, “Karmele” sigue a una mujer y su familia después de verse obligados a abandonar su hogar y refugiarse en Francia. Allí entra en contacto con la embajada cultural vasca en el exilio y conoce a Txomin, un trompetista de quien se enamora. La historia continúa en Venezuela, antes del regreso de la pareja al País Vasco, donde se enfrentan a la dictadura. El director estará presente en la función.",
"la-anatomia-de-los-caballos": "Derrotado tras una revolución en el siglo XVIII, Ángel Pumacahua huye hacia su pueblo y descubre que ha llegado a los Andes peruanos del siglo XXI. La caída de un meteorito parece haber provocado esa ruptura temporal. Ahí conoce a Eustaquia, quien busca a su hermana gemela desaparecida durante la lucha contra una empresa minera. El encuentro entre dos épocas abre una interrogante sobre la vigencia de las luchas revolucionarias y sus motivos: contra qué y contra quién luchar en el presente.",
"la-bola-negra": "“La bola negra” conecta las vidas de tres hombres de distintas épocas, cuyas historias quedan relacionadas a través del deseo, la sexualidad, el dolor y la herencia. En su centro está una de las últimas obras que Federico García Lorca dejó inconclusas. Con Guitarricadelafuente, Miguel Bernardeau, Penélope Cruz y Glenn Close. Premio a la Mejor Dirección en Cannes 2026 y carta de España al Oscar.",
"la-cordillera-de-los-suenos": "Homenaje a Patricio Guzmán (1941–2026). “La cordillera de los sueños” cierra la trilogía que Guzmán dedicó a la memoria de Chile —junto a Nostalgia de la luz y El botón de nácar— y vuelve a preguntar qué guarda la cordillera sobre la historia reciente del país.",
"la-frontera": "Protagonizada por Patricio Contreras, “La frontera” sigue a Ramiro Orellana, un profesor que, tras ser acusado de participar en actividades gremiales, es enviado al extremo sur de Chile durante la dictadura. En ese territorio, marcado por el aislamiento y la amenaza permanente de la naturaleza, enfrenta las heridas de un exilio que lo ha mantenido distante de su hijo. Allí conoce a Maite, una mujer española refugiada en Chile, con quien inicia una relación que le permite recuperar una sensibilidad que parecía perdida, mientras sobre el pueblo vuelve a proyectarse la amenaza de un maremoto. Oso de Plata en Berlín.",
"la-ilusion-de-un-verano-sin-fin": "Desde Argentina llega “La Ilusión de un Verano sin fin” (2026), documental y ópera prima de la reconocida fotógrafa Alessandra Sanguinetti. La película, premiada en Locarno, se construye a lo largo de veinticinco años, siguiendo el crecimiento de dos primas inseparables, Guillermina y Belinda, en la inmensidad de la Pampa argentina. El paso del tiempo se convierte así en parte fundamental de una obra que observa la transformación de sus protagonistas y de la relación que mantienen entre ellas.",
"la-muerte-no-tiene-dueno": "La programación incluye también “La muerte no tiene dueño” (2025), del venezolano Jorge Thielen Armand, una historia donde las disputas por la tierra adquieren una dimensión cada vez más violenta. Una heredera de una plantación de cacao y antiguos trabajadores se enfrentan por la propiedad del terreno, en un conflicto donde las relaciones de poder terminan imponiendo su propia lógica y la violencia se convierte en la consecuencia de una disputa por el territorio.",
"la-ofrenda": "Luego de fracasar en un evento benéfico, un grupo de jóvenes decide robar las ofrendas de una iglesia.",
"la-procesion-de-los-ausentes": "En el vasto desierto de Atacama, un narrador perdido en el tiempo busca la memoria de su difunto padre en los recuerdos que le evoca la festividad de Ayquina. Entretejiendo imágenes actuales con material de archivo, este documental revela cómo la fe y la tradición enraizan un legado que conecta pasado y presente, trascendiendo el tiempo.",
"la-teta-asustada": "Película que aborda las consecuencias de la violencia y la memoria histórica a través de la experiencia de Fausta, una joven marcada por el trauma heredado de una generación que sufrió la violencia política en el Perú. Oso de Oro en Berlín.",
"las-visitas-de-camilo": "Entre los años 90 y 2000, un enigmático hombre cubano visita una y otra vez a una familia argentina. A partir de recuerdos fragmentarios, contradicciones y silencios, surge la pregunta de cómo se construye una identidad.",
"lodo": "En una ciudad en llamas, una ceramista en crisis da forma a esculturas que revelan un mundo interior que se desmorona.",
"los-vencedores": "El director argentino viaja a las islas Malvinas para explorar las huellas de la guerra de 1982, pero la búsqueda de un retrato del conflicto toma un rumbo inesperado cuando surge una amistad con quien encarna al antiguo enemigo. La película desplaza así la mirada desde las marcas de la confrontación hacia la posibilidad de un encuentro entre personas separadas por la historia.",
"lyn-mia": "Documental en el que la directora revisita viejas cartas de su madre.",
"mailin": "Mientras le cuenta un cuento de hadas a su hija, Mailin reconstruye los recuerdos de una infancia traumática. El relato se convierte en un recorrido doloroso por su pasado, en el que la memoria y la búsqueda de justicia se enlazan con el deseo de ofrecerle a la siguiente generación una infancia diferente.",
"matapanki": "La película sigue a Ricardo, un joven punk de la periferia que, después de adquirir superpoderes, decide transformar la sociedad. Un error sangriento desencadena entonces un conflicto que escala hasta dimensiones inesperadas. Distinguida con la Mención Especial del Jurado Internacional en Generation 14+ de la Berlinale 2026, Matapanki ha seguido su camino por diversos festivales del mundo y se perfila como una de las películas chilenas más exitosas del año.",
"mensajeras-sin-mensaje": "A través de recortes, dibujos y papel arrugado, surge un retrato incompleto del día a día de las palomas urbanas, en donde la melancolía, el abandono y la falta de pertenencia tiñen su mundo con impresiones borrosas y preguntas sin respuesta.",
"miriam": "A través de esta videocarta, la directora habla con su tía, quien fue víctima de femicidio años atrás, sobre cómo ha sido para ella crecer con miedo en un país peligroso para las mujeres, tratando de desarrollarse como la única mujer de su familia y sobrellevar el duelo.",
"mnema": "En un mundo de obstáculos y laberintos, Mnema intenta encontrar el camino para avanzar por cada nivel de un videojuego. Entre la realidad y la fantasía, Mnema escucha los testimonios de mujeres que alguna vez estuvieron en su lugar y busca tomar el control en un mundo patriarcal.",
"motel-paraiso": "Completa la selección “Motel Paraíso” (2025), documental del mexicano Lalo Castilla. La película sigue a Daniel, el indisciplinado propietario de un pequeño motel situado en una localidad costera del Golfo de México, a través de la mirada de su nieto. Para hacerlo, utiliza la misma cámara VHS que Daniel empleó en el pasado, estableciendo un vínculo entre distintas generaciones y entre las imágenes que fueron registradas entonces y la mirada que las recupera en el presente.",
"no-prendas-la-luz": "Para algunos niños, los monstruos aparecen al encender la luz.",
"norte-claro-sur-oscuro": "Francisca reabre su casa familiar, vacía desde la muerte de sus padres. Mientras la rehabita junto a su hermano, la figura de su padre alcohólico tomará forma, en una exploración material sobre lo que persiste silenciosamente entre generaciones.",
"nunkui": "La película toma su nombre tanto del espíritu femenino de la huerta en la cosmovisión shuar como de una niña que crece rodeada de plantas, animales, espíritus y una extensa familia. En ese universo exuberante, los sueños premonitorios conviven con la amenaza del avance minero en la cordillera amazónica, en un relato que enlaza la experiencia de la infancia con las tensiones que atraviesan el territorio.",
"o-jardim-magico": "Dos amigos descubren un tesoro escondido, pero ambos se niegan a aceptarlo. Juntos encuentran una solución que hará florecer un hermoso futuro para toda la aldea. “El Jardín Mágico” es una historia sobre la generosidad y el poder transformador de los verdaderos tesoros.",
"pan": "Gilberto, un panadero anciano, debe cerrar su panadería gracias a una cuarentena. Vive con su nieta, con quien tiene una relación distante. Un día, llega una nueva panadería al barrio, equipada con alta tecnología. Gilberto deberá preservar su oficio.",
"paqarina": "Una pandemia y la crisis social obligan a una familia migrante a abandonar la ciudad y retornar a su tierra de origen. Frente a la falta de oportunidades y la incertidumbre, emprenden un viaje donde despiertan memorias ancestrales que los reconectan con su pasado siendo la única esperanza para su supervivencia.",
"paulina": "Paulina Aguilera retrató la vida en Tierra Amarilla durante más de 30 años sin ser reconocida en la historia de la fotografía chilena. Su figura y la memoria de su pueblo se reconstruyen a partir de sus fotos y los recuerdos de quienes la conocieron.",
"pin-de-fartie": "Una niña y un ciego frente a un lago, dos actores que ensayan una antigua obra de teatro, dos ancianos que viven en un contenedor frente al Congreso y una pianista ciega condenada a repetir la única pieza que recuerda de memoria forman parte de un universo de personajes, escenas y despedidas. En medio de ese entramado, dos cineastas filman trenes y lunas mientras persiguen una actividad cuyo sentido parece volverse cada vez más incierto: hacer películas.",
"pinchu-es-asi": "Pinchu es un guarrete y todos y todas le ríen la gracia, incluida su novia Jimena, que cumple 30 años este fin de semana y está montando un fiestón épico. Sólo Bea es capaz de verlo aunque quizás esa experiencia le obligue a plantearse algunas cosas.",
"plata-o-mierda": "Marcos está preso y, desde esa situación, inicia con Bonino un intercambio clandestino que se convierte en el centro de la película. En ese proceso, ambos terminan asumiendo el lugar de directores, en una experiencia que pone en juego los límites de la autoría y las posibilidades de filmar desde el encierro.",
"poblacion-flotante": "La película sigue a pasajeros anónimos que recorren en bus distintos lugares de Chile, entre desplazamientos físicos, espacios mentales y vidas virtuales. El viaje aparece como una experiencia colectiva atravesada por la incertidumbre y por la búsqueda de un lugar de llegada.",
"presepio": "La familia de Dejair se reúne para celebrar la Navidad. Cuando su hijo le regala a su nieto una pistola de agua, Dejair estalla e intenta convencer a su familia de lo absurdo que resulta regalarle un arma a un niño.",
"relicto": "La desaparición de Sixto Muñoz, a los 105 años y conocido como el último hombre Tinigua, impulsa una búsqueda que reconstruye la extinción de toda una cultura. A partir de la huella de una vida, la película se aproxima a la pérdida de una memoria colectiva y a aquello que permanece cuando una comunidad se acerca a su desaparición.",
"replicas": "Película filmada en 2015. Tras un terremoto, Catalina vuelve a la casa familiar para ayudar a su padre a venderla luego de la muerte de su tío Héctor. La convivencia abre un espacio de duelo y reencuentro en el que reaparecen culpas, silencios y conflictos familiares vinculados a una ausencia que permanece demasiado presente.",
"siempre-soy-tu-animal-materno": "La franja comenzará con “Siempre soy tu animal materno” (2026), segundo largometraje de la costarricense Valentina Maurel, estrenado en Cannes. La película sigue a Elsa, una mujer de 28 años que, después de varios años en Europa, vuelve a Costa Rica y se reencuentra con su hermana menor, Amalia. Mientras la joven se interna en una búsqueda de carácter esotérico y existencial, el resto de la familia también atraviesa sus propias transformaciones: el padre intenta reafirmarse a través de nuevas relaciones amorosas y la madre recupera una faceta de su juventud mediante la reedición de sus poemas eróticos. En medio de este escenario, Elsa debe decidir si intervenir en la vida de su hermana o tomar distancia y emprender nuevamente la fuga.",
"sol-menor": "Primavera en flor. Una sonata, un tren, una carta. Samuel, entre su trabajo como profesor de flauta y los rituales de duelo por una viudez prematura, se enfrenta a un nuevo dilema tras la visita de su hermano.",
"sorda": "Continúa con “Sorda” (2025), aclamado drama español dirigido por Eva Libertad y protagonizado por su hermana, la actriz sorda Miriam Garlo, junto a Álvaro Cervantes. Basada en el cortometraje homónimo que la directora estrenó en 2021, es el primer largometraje español protagonizado por una actriz sorda. La película sigue la historia de Ángela, una mujer sorda que trabaja como alfarera y está a punto de tener una hija junto a su pareja oyente, Héctor. La llegada del bebé altera la dinámica de la relación y obliga a Ángela a enfrentarse a la maternidad en una sociedad y un entorno que no están diseñados para ella. La cinta triunfó en los Premios Goya, donde obtuvo los galardones a Mejor Dirección Novel (Eva Libertad), Mejor Actriz Revelación (Miriam Garlo) y Mejor Actor de Reparto (Álvaro Cervantes).",
"tauromaquia": "En un caluroso verano, un grupo de jóvenes se entretiene con juegos violentos en una quinta abandonada, cuando, sin explicación alguna, comienzan a desaparecer uno por uno.",
"tinku": "Un eclipse da inicio al ritual. Sobre un desierto infinito dos antiguos pueblos divididos por una herida en la tierra se reúnen para celebrar un singular y mágico evento.Tinku. En la oscuridad este ritual requerirá el mayor despliegue de valor.",
"trabajo-hecho": "En un pequeño islote de Chiloé, un buzo mariscador vive en su casa suspendida sobre el mar. Entre recuerdos y el silencio del océano, el tiempo parece detenerse. Mientras contempla lo que deja atrás, se prepara para un último viaje.",
"tres-tristes-tias": "Un drama familiar contado desde una mirada cercana al true crime se fractura cuando el director, ahora padre, vuelve la cámara hacia sí mismo para cuestionar la memoria y los vínculos familiares.",
"tv-entreaberta": "Una mujer es abducida al interior de su televisor, donde es atormentada por un caricaturesco presentador estadounidense. A medida que atraviesa diversos géneros televisivos, la protagonista va siendo gradualmente asimilada por este sistema.",
"uatana": "La protagonista es Íris, una oficial de justicia que tiene dificultades para distinguir la verdad. La desaparición de un activista la llevará a cuestionar el sentido de su trabajo y a enfrentarse a una pregunta fundamental: qué significa realmente hacer justicia.",
"videoclub-2001": "Otoño de 2005. La digitalización avanza imparable y los videoclubs están en peligro de extinción. Mila, una joven rebelde que hereda el “Videoclub 2001” tras la muerte de su padre, debe decidir si lucha por mantenerlo vivo. Por su familia…"
}


def slug(t):
    t = t.lower()
    for a, b in zip("áéíóúüñ", "aeiouun"):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def base(d, hora, sala, sec):
    comp = sec.startswith("Competencia")
    return {"dia": f"2026-11-{d:02d}", "hora": hora, "sala": sala,
            "seccion": "En Competencia" if comp else sec, "subseccion": sec if comp else "",
            "acceso": LIBRE, "url": "", "fuente": "pdf", "estado": "", "idioma": "", "sinopsis": "", "premiere": ""}


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
    for f in out:
        f["url"] = FICHA.get(f["id"], "")
        f["sinopsis"] = SINOPSIS.get(f["id"], f["sinopsis"])
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
    s = re.sub(r"const LB=\{.*?\};", lambda m: "const LB=" + json.dumps(LB, ensure_ascii=False) + ";", s, count=1, flags=re.S)
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
    # un solo calendario compartido para los dos
    s = reemplazar(s, '<button type="button" data-p="Ignacio" aria-pressed="true">Ignacio</button>\n      <button type="button" data-p="Marian" aria-pressed="false">Marian</button>',
                   '<button type="button" data-p="Ignacio y Marian" aria-pressed="true">Ignacio y Marian</button>')
    s = reemplazar(s, 'const PERFILES=["Ignacio","Marian"];', 'const PERFILES=["Ignacio y Marian"];')
    s = reemplazar(s, 'let perfil=leer("ficv33-perfil","Ignacio"); if(!PERFILES.includes(perfil)) perfil="Ignacio";',
                   'let perfil=PERFILES[0];')
    s = reemplazar(s, 'dbRef.doc("perfiles/"+p)', 'dbRef.doc("perfiles/juntos")')
    s = reemplazar(s, 'filename:"calendario-"+perfil.toLowerCase()+"-ficv33.pdf"', 'filename:"calendario-ficvina38.pdf"')
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
