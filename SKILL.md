---
name: ahorro-tokens
description: Úsala en toda tarea de varios pasos con herramientas (código, archivos, shell, bases de datos, búsquedas) para gastar menos tokens: lecturas acotadas, salidas filtradas, sin repeticiones ni retrabajo.
---

# Ahorro de tokens

El gasto grande no es lo que escribo: es lo que **leo** (archivos enteros, salidas de comandos, listados, datos) y lo que **rehago**. Todo lo leído se queda en el contexto y se vuelve a pagar en cada turno siguiente.

Regla de oro: se recorta el ruido, **nunca la explicación**. DVD quiere entender el porqué de cada decisión; lo que sobra es narrar la mecánica y repetir lo ya dicho. Y ningún atajo de esta skill borra, trunca ni descarta datos: todos los scripts son de solo lectura y la salida completa queda siempre en un log.

## 1. Herramientas (usar SIEMPRE antes que leer a pelo)

| Situación | En vez de… | Usa |
|---|---|---|
| Comando con salida larga (build, install, tests, scraper) | ejecutarlo y leer todo | `run_quiet.py "comando"` |
| Archivo de código/markdown de más de ~150 líneas | leerlo entero | `outline.py archivo` → leer solo el rango |
| JSON grande o respuesta de API | abrirlo | `json_pick.py f.json --schema`, luego `json_pick.py f.json "ruta[*]" --fields a,b --limit 5` |
| CSV, TSV, TXT de datos, log, SQLite | abrirlo o `head` a ciegas | `data_peek.py archivo` (SQLite: `--table X --rows 3`, `--no-count` si es enorme) |

Medido en archivos reales de gentilicios: CSV de 22 MB → 785 car.; JSON de 23 MB → 4.000 car.; script de 916 líneas → 700 car.; build con error enterrado → 98 % menos y el error localizado con su nº de línea.

**Dónde están los scripts** (los cuatro, Python 3, sin dependencias). Fuente única: repo GitHub https://github.com/dvdzapata/ahorro-tokens (carpeta `scripts/`).
- Windows (DVD): `C:\Users\dvdza\ahorro-tokens\scripts\` — ejecutar con `python`. Actualizar: `git -C C:\Users\dvdza\ahorro-tokens pull -q`.
- Servidor Ubuntu: `~/ahorro-tokens/scripts/` — ejecutar con `python3`. Actualizar: `git -C ~/ahorro-tokens pull -q`.
- Sesión en la nube: añadir el repo a la sesión y clonarlo una vez (`git clone -q …`), luego usar `scripts/` desde ahí.
- Si faltan en una máquina: clonar el repo en esa ruta. Nunca reescribirlos de memoria ni incrustarlos en un comando.
- Mejoras a un script: se hacen en el repo (commit + push) y se propagan con `pull`; no editar copias sueltas.

## 2. Antes de empezar: evitar retrabajo

- Leer primero las notas del proyecto (`CLAUDE.md`, `ESTADO.md`, `PROYECTO.md`…) — con `outline.py` si son largas, y luego solo la sección que toca.
- Una ambigüedad que obligaría a rehacer trabajo caro se pregunta **una vez al principio**.
- Pensar el plan entero antes de la primera herramienta: qué necesito, dónde está, en qué orden.

## 3. Leer lo justo

- **Buscar antes de leer**: Grep/`Select-String` para localizar, luego leer solo el rango (offset/limit).
- **No listar carpetas grandes enteras**: filtrar por tipo, tamaño o nombre (ver tabla §6). Un listado completo de `C:\gentilicios` cuesta ~20.000 caracteres.
- **Nada de recursivos sin límite** en carpetas enormes: dan timeout y no devuelven nada. Acotar con `-Depth`, carpeta concreta o patrón.
- Varios archivos → una sola llamada o llamadas en paralelo en el mismo mensaje.
- **No releer** lo que acabo de escribir o editar.

## 4. Escribir lo justo

- Cambios pequeños → Edit del fragmento exacto, no reescribir archivos.
- En el chat no se pega un archivo completo: se describe el cambio o se muestra el diff mínimo.
- Cierre breve: qué salió, el archivo, un siguiente paso si lo hay. Sin recapitular pasos.
- Explicar decisiones y hallazgos (el porqué); omitir la narración paso a paso (el qué-estoy-haciendo).

## 5. Mover archivos sin pasarlos por el contexto

- Para llevar archivos a la máquina de DVD: **conectar la carpeta** y usar la copia directa (commit de archivos). Nunca incrustar el contenido en un comando (base64, here-strings): se paga dos veces.
- Para traer archivos del PC al entorno de trabajo: copiarlos (stage), no leerlos y re-escribirlos.

## 6. Entorno de DVD: comandos y trampas conocidas

**Windows — PowerShell 5.1** (no es PowerShell 7):
- `&&` y `||` **no existen**: encadenar con `;` o con `if ($?) { … }`.
- No hay `grep`, `tail`, `head`, `jq`, `wc`:

| Linux | PowerShell 5.1 |
|---|---|
| `grep -n patrón f` | `Select-String -Pattern patrón f` |
| `tail -n 50 f` | `Get-Content f -Tail 50` |
| `head -n 20 f` | `Get-Content f -TotalCount 20` |
| `wc -l f` | `(Get-Content f \| Measure-Object -Line).Lines` (lento en archivos enormes → `data_peek.py`) |
| `ls` filtrado | `Get-ChildItem -File -Filter *.csv \| Sort Length -Desc \| Select -First 10 Name,Length` |
| `jq` | `json_pick.py` |

- Python: `python` = 3.14 (también existe `py` = 3.13). Hay `git`, no hay `gh`.
- Git tiene `core.autocrlf=true`: los archivos clonados salen con CRLF y su hash no coincide con la copia LF aunque el contenido sea idéntico. Comparar normalizando saltos de línea antes de concluir que "son distintos".
- Borrar en carpetas de proyecto: borrar solo el elemento concreto, tras comprobar su contenido; no pedir permisos de borrado sobre la carpeta entera del proyecto.
- Las respuestas de la herramienta de PowerShell pueden tardar; si un comando no responde en 60 s, no relanzarlo igual: acotarlo.

**Servidor Ubuntu 24.04:**
- `pip install` necesita `--break-system-packages`; usar `-q`.
- PostgreSQL: `psql -h localhost` (la autenticación peer falla sin `-h`).
- Autenticación SSH por clave.

**Instalaciones silenciosas:** `pip install -q`, `npm i --silent --no-fund --no-audit`.

## 7. Datos (gentilicios y similares)

- Nunca abrir un SQLite, CSV, TSV o JSON de datos para "ver qué tiene": `data_peek.py` / `json_pick.py --schema`.
- Consultas SQL de exploración siempre con `LIMIT`; para tamaños, `COUNT(*)` en vez de traer filas.
- Resultados de consultas grandes → a archivo, y leer el resumen.
- Solo lectura al explorar (`data_peek` abre SQLite en modo `ro`). Borrar o descartar datos está prohibido salvo orden expresa.

## 8. No repetir fallos

- Un comando que falla dos veces: **parar y diagnosticar** (error, versión, ruta, permisos). No relanzar con variaciones a ciegas.
- Recurso bloqueado o timeout: cambiar de vía, no reintentar lo mismo.

## 9. Convertir lo recurrente en reutilizable

- Procedimiento que se repite → script dentro del proyecto; a partir de ahí, una sola llamada.
- Trampa de entorno descubierta → anotarla en el `CLAUDE.md` del proyecto (o proponer añadirla a §6 de esta skill).
- Tipo de tarea frecuente → proponer una skill.

## 10. Herramientas caras con criterio

- No lanzar subagentes salvo que DVD lo pida: arrancan en frío y releen lo que ya sé.
- Web: consultas cortas y específicas; con WebFetch, pedir exactamente el dato.
- Llamadas independientes → en paralelo, en un mismo mensaje.

## 11. Conversaciones largas: traspaso

Cuando el contexto es muy largo y el tema cambia, proponer chat nuevo y entregar este resumen para pegar al empezar:

```
TRASPASO — <proyecto> — <fecha>
Objetivo: <una frase>
Hecho: <3-6 puntos, con rutas>
Decisiones tomadas (y por qué): <puntos>
Estado actual: <qué funciona, qué no>
Pendiente, en orden: <pasos>
Archivos clave: <rutas + qué contiene cada uno>
Trampas encontradas: <comandos/rutas que fallaron y la solución>
```

## Chequeo rápido antes de cada herramienta

1. ¿Ya tengo este dato? → no volver a pedirlo.
2. ¿Hay script para esto? → usarlo.
3. ¿Puedo pedir solo una parte? → rango, filtro, `LIMIT`, `-Tail`.
4. ¿Puedo agrupar esta llamada con otras?
5. ¿Esto ya ha fallado? → diagnosticar en vez de repetir.
