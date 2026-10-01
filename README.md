# Programa 33° FICValdivia

Script que navega <https://33.ficvaldivia.cl/programacion> y arma el programa **por día y sección**.

```bash
pip install -r requirements.txt
playwright install chromium
python ficv_programa.py              # genera salida/programa.{html,md,json}
python ficv_programa.py --detalles   # visita cada ficha para precisar la sección
python ficv_programa.py --ver --dump # ver el navegador y guardar el HTML (depuración)
```

Abre `salida/programa.html`: pestañas por día, filtro por sección y buscador.

El script usa dos estrategias: intercepta la API JSON si la web carga la programación así,
y si no, lee el DOM haciendo clic en cada pestaña de día y detectando las funciones por su hora.
Las secciones se reconocen con la lista `SECCIONES` del script (ajústala si la web usa otros nombres).
Si ya tienes un Chromium instalado, puedes usarlo con `CHROMIUM_PATH=/ruta/al/chromium`.

## La web del festival

La programación está hecha en **Softr** (tabla "Películas"). El script detecta la lista, pulsa
"Cargar más" hasta el final y lee los registros que la página pide a
`/v1/datasource/.../records`. Cada película trae su **Agenda** (`"Viernes 16 - 11:00"`), y de ahí sale
una función por cada día y hora. Si una película se exhibe en dos salas, la API no indica qué sala
corresponde a cada función; en ese caso aparecen las dos.

Para reprocesar respuestas ya guardadas, sin abrir el navegador:

```bash
python ficv_programa.py --desde-json programa/depuracion/api
```

## GitHub Actions

`.github/workflows/programa.yml` ejecuta el script cuando cambia, a mano (*Run workflow*), y a diario
en octubre, y deja el resultado en `programa/` (`programa.html`, `programa.md`, `programa.json`).
