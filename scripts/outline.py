#!/usr/bin/env python3
"""outline: mapa de un archivo (funciones, clases, encabezados...) con nº de línea.

Sirve para leer solo el rango necesario en vez del archivo entero.
Soporta: .py .js .jsx .ts .tsx .mjs .php .md .html .htm .css .scss .sql .json .sh .ps1
Otros tipos: muestra nº de líneas y las primeras líneas no vacías.

Uso:
  python outline.py archivo.py
  python outline.py src/app.js src/api.ts        (varios a la vez)
"""
import ast, json, os, re, sys

def py_outline(src):
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"  (no se pudo parsear: {e}) — uso regex"] + regex_outline(src, PATTERNS[".py"])
    def walk(node, depth):
        for n in ast.iter_child_nodes(node):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(n, ast.ClassDef) else "def"
                end = getattr(n, "end_lineno", "?")
                args = ""
                if kind == "def":
                    args = "(" + ", ".join(x.arg for x in n.args.args) + ")"
                out.append(f"{n.lineno:>6}-{end:<6}{'  ' * depth}{kind} {n.name}{args}")
                walk(n, depth + 1)
    walk(tree, 0)
    return out

PATTERNS = {
    ".py":  [r"^\s*(async\s+def|def|class)\s+\w+"],
    ".js":  [r"^\s*(export\s+)?(default\s+)?(async\s+)?function\*?\s+\w+",
             r"^\s*(export\s+)?(default\s+)?class\s+\w+",
             r"^\s*(export\s+)?(const|let|var)\s+\w+\s*=\s*(async\s*)?(\([^)]*\)|\w+)\s*=>",
             r"^\s*(async\s+)?(static\s+)?(get\s+|set\s+)?[A-Za-z_$][\w$]*\s*\([^)]*\)\s*\{\s*$",
             r"^\s*(app|router)\.(get|post|put|patch|delete|use)\(",
             r"^\s*export\s+(interface|type|enum)\s+\w+"],
    ".php": [r"^\s*(abstract\s+|final\s+)?(class|interface|trait)\s+\w+",
             r"^\s*(public|private|protected|static|\s)*function\s+&?\w+"],
    ".md":  [r"^#{1,6}\s+"],
    ".html":[r"<h[1-3][^>]*>", r"<(section|main|nav|header|footer|form|table|script|style)\b[^>]*>",
             r"\bid=\"[^\"]+\""],
    ".css": [r"^\s*@(media|supports|keyframes|layer|font-face)", r"^\s*:root\b",
             r"^[^\s{][^{]*\{\s*$"],
    ".sql": [r"^\s*(create|alter|drop)\s+(or\s+replace\s+)?(table|view|function|index|trigger|procedure|materialized\s+view)\b",
             r"^\s*--\s*=+"],
    ".sh":  [r"^\s*(function\s+)?\w+\s*\(\)\s*\{", r"^\s*function\s+\w+"],
    ".ps1": [r"^\s*function\s+[\w-]+", r"^\s*param\s*\("],
}
ALIASES = {".jsx": ".js", ".ts": ".js", ".tsx": ".js", ".mjs": ".js", ".cjs": ".js",
           ".htm": ".html", ".scss": ".css", ".psm1": ".ps1", ".bash": ".sh"}

def regex_outline(src, pats):
    rxs = [re.compile(p, re.IGNORECASE) for p in pats]
    out = []
    for i, ln in enumerate(src.splitlines(), 1):
        if any(r.search(ln) for r in rxs):
            out.append(f"{i:>6}  {ln.strip()[:140]}")
    return out

def json_outline(src):
    try:
        data = json.loads(src)
    except Exception as e:
        return [f"  (JSON inválido: {e})"]
    def desc(v):
        if isinstance(v, dict):  return f"obj({len(v)} claves)"
        if isinstance(v, list):  return f"lista[{len(v)}]"
        s = json.dumps(v, ensure_ascii=False)
        return s if len(s) < 60 else s[:57] + "..."
    if isinstance(data, dict):
        return [f"  {k}: {desc(v)}" for k, v in list(data.items())[:80]]
    if isinstance(data, list):
        head = [f"  lista[{len(data)}]"]
        if data and isinstance(data[0], dict):
            head.append("  claves del 1er elemento: " + ", ".join(list(data[0])[:40]))
        return head
    return ["  " + desc(data)]

def outline(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        src = f.read()
    ext = os.path.splitext(path)[1].lower()
    ext = ALIASES.get(ext, ext)
    n = src.count("\n") + (0 if src.endswith("\n") or not src else 1)
    print(f"== {path}  ({n} líneas, {len(src.encode('utf-8'))//1024} KB)")
    if ext == ".py":
        items = py_outline(src)
    elif ext == ".json":
        items = json_outline(src)
    elif ext in PATTERNS:
        items = regex_outline(src, PATTERNS[ext])
    else:
        items = [f"  (tipo sin mapa) primeras líneas:"] + \
                [f"{i:>6}  {l[:140]}" for i, l in enumerate(src.splitlines()[:15], 1) if l.strip()]
    if len(items) > 200:
        print("\n".join(items[:200]))
        print(f"  ... {len(items) - 200} entradas más (acota con grep)")
    else:
        print("\n".join(items) if items else "  (sin entradas reconocidas)")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    for p in sys.argv[1:]:
        try:
            outline(p)
        except OSError as e:
            print(f"== {p}: {e}")
