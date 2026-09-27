# ahorro-tokens
Úsala en toda tarea de varios pasos con herramientas (código, archivos, shell, bases de datos, búsquedas) para gastar menos tokens: lecturas acotadas, salidas filtradas, sin repeticiones ni retrabajo.

Herramientas de solo lectura para que Claude lea **solo lo necesario** y gaste menos tokens.
Van con la skill `ahorro-tokens` (copia de referencia en `SKILL.md`).

| Script | Qué hace |
|---|---|
| `scripts/run_quiet.py "cmd"` | Ejecuta un comando; muestra código de salida, líneas de error (con nº de línea) y la cola. Salida completa en un log. |
| `scripts/outline.py archivo` | Mapa de funciones/clases/encabezados con rango de líneas (py, js/ts, php, md, html, css, sql, json, sh, ps1). |
| `scripts/json_pick.py f.json --schema` | Estructura de un JSON, o extracción de rutas/campos (`"items[*]" --fields a,b --limit 5`). Sustituye a `jq`. |
| `scripts/data_peek.py archivo` | CSV/TSV/TXT/log/SQLite grandes sin cargarlos: filas, columnas, % de relleno, muestra, esquema. SQLite en modo solo lectura. |

Python 3.8+ sin dependencias. Funcionan igual en Linux y Windows.

## Instalación

```powershell
# Windows
git clone https://github.com/dvdzapata/ahorro-tokens C:\Users\dvdza\ahorro-tokens
```
```bash
# Servidor
git clone https://github.com/dvdzapata/ahorro-tokens ~/ahorro-tokens
```

Actualizar: `git -C <ruta> pull -q`.

## Ahorro medido (archivos reales)

| Caso | Sin script | Con script |
|---|---|---|
| CSV 22 MB (geotargets) | 23.473.011 car. | 785 |
| JSON 23 MB | 23.164.387 | 4.152 |
| Script Python de 916 líneas | 38.957 | 706 |
| Log de 1,8 MB | 1.843.505 | 428 |
| Build de 800 líneas con 1 error | 37.262 | 1.051 |
| Salida corta (≤ 40 líneas) | se muestra entera, +1 línea de cabecera |
