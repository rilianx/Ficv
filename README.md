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
