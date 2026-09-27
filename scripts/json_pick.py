#!/usr/bin/env python3
"""json_pick: ver la ESTRUCTURA de un JSON o extraer solo los campos que importan.

No hace falta tener jq (en Windows no suele estar).

Uso:
  python json_pick.py datos.json --schema             estructura: claves, tipos, tamaños
  python json_pick.py datos.json items[0].precio       un valor concreto
  python json_pick.py datos.json "items[*].nombre" --limit 10
  python json_pick.py datos.json "items[*]" --fields id,fecha,precio --limit 5
  curl ... | python json_pick.py - --schema            desde stdin
Rutas: a.b.c, a[0], a[*] (todos los elementos), a[-1] (el último).
"""
import argparse, json, re, sys

def tokens(path):
    for part in re.findall(r"[^.\[\]]+|\[-?\d+\]|\[\*\]", path):
        if part == "[*]":
            yield "*"
        elif part.startswith("["):
            yield int(part[1:-1])
        else:
            yield part

def pick(data, path):
    cur = [data]
    for t in tokens(path):
        nxt = []
        for c in cur:
            if t == "*":
                nxt.extend(c if isinstance(c, list) else (c.values() if isinstance(c, dict) else []))
            elif isinstance(t, int):
                if isinstance(c, list) and -len(c) <= t < len(c):
                    nxt.append(c[t])
            elif isinstance(c, dict) and t in c:
                nxt.append(c[t])
        cur = nxt
    return cur

def schema(v, depth=0, max_depth=6, key="$"):
    pad = "  " * depth
    if isinstance(v, dict):
        print(f"{pad}{key}: obj({len(v)})")
        if depth < max_depth:
            for k, x in list(v.items())[:60]:
                schema(x, depth + 1, max_depth, k)
            if len(v) > 60:
                print(f"{pad}  ... {len(v) - 60} claves más")
    elif isinstance(v, list):
        types = sorted({type(x).__name__ for x in v})
        print(f"{pad}{key}: lista[{len(v)}] de {'/'.join(types) or 'nada'}")
        if v and depth < max_depth and isinstance(v[0], (dict, list)):
            schema(v[0], depth + 1, max_depth, "[0]")
    else:
        s = json.dumps(v, ensure_ascii=False)
        print(f"{pad}{key}: {type(v).__name__} = {s if len(s) <= 50 else s[:47] + '...'}")

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="archivo JSON o - para stdin")
    ap.add_argument("path", nargs="?", help="ruta a extraer")
    ap.add_argument("--schema", action="store_true", help="mostrar estructura")
    ap.add_argument("--fields", help="con objetos: quedarse solo con estas claves (coma)")
    ap.add_argument("--limit", type=int, default=20, help="máx. resultados (20)")
    ap.add_argument("--depth", type=int, default=6, help="profundidad del schema (6)")
    a = ap.parse_args()

    raw = sys.stdin.read() if a.file == "-" else open(a.file, encoding="utf-8-sig").read()
    data = json.loads(raw)
    if a.schema or not a.path:
        schema(data if not a.path else pick(data, a.path), max_depth=a.depth)
        return
    res = pick(data, a.path)
    if a.fields:
        keep = [f.strip() for f in a.fields.split(",")]
        res = [{k: r.get(k) for k in keep} if isinstance(r, dict) else r for r in res]
    total = len(res)
    for r in res[:a.limit]:
        print(json.dumps(r, ensure_ascii=False))
    if total > a.limit:
        print(f"... {total - a.limit} resultados más (total {total}; sube --limit si los necesitas)")
    elif total == 0:
        print("(sin resultados para esa ruta; usa --schema para ver la estructura)")

if __name__ == "__main__":
    main()
