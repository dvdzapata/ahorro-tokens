#!/usr/bin/env python3
"""data_peek: ver de qué va un archivo de datos GRANDE sin cargarlo entero. Solo lectura.

  CSV/TSV/TXT : tamaño, nº de filas (en streaming), cabecera, 3 filas de muestra y
                % de relleno por columna (sobre las primeras --sample filas)
  SQLite      : tablas, columnas con tipo, índices y nº de filas
  Otros       : tamaño, nº de líneas y primeras líneas

Uso:
  python data_peek.py archivo.csv
  python data_peek.py alternateNames.txt --sep tab --no-header
  python data_peek.py database_v2.sqlite                 (todas las tablas)
  python data_peek.py database_v2.sqlite --table demonyms --rows 3
  python data_peek.py database_v2.sqlite --no-count       (sin COUNT(*), más rápido)
"""
import argparse, csv, io, os, sqlite3, sys

def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024: return f"{n:.0f} {u}"
        n /= 1024
    return f"{n:.1f} TB"

def count_lines(path):
    n, last = 0, b"\n"
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b: break
            n += b.count(b"\n"); last = b[-1:]
    return n + (0 if last == b"\n" else 1)

def cut(s, w=40):
    s = str(s).replace("\n", " ")
    return s if len(s) <= w else s[:w - 1] + "…"

def peek_table_file(path, a):
    enc = "utf-8-sig"
    with open(path, encoding=enc, errors="replace", newline="") as f:
        head = f.read(64 * 1024)
    if a.sep:
        sep = "\t" if a.sep == "tab" else a.sep
    else:
        try:
            sep = csv.Sniffer().sniff(head, delimiters=",;\t|").delimiter
        except csv.Error:
            sep = "\t" if head.count("\t") > head.count(",") else ","
    total = count_lines(path)
    print(f"== {path}  ({human(os.path.getsize(path))}, {total:,} líneas, separador={sep!r})")
    csv.field_size_limit(10**9)
    with open(path, encoding=enc, errors="replace", newline="") as f:
        rd = csv.reader(f, delimiter=sep)
        first = next(rd, [])
        if a.no_header:
            cols, rows = [f"c{i}" for i in range(len(first))], [first]
        else:
            cols, rows = first, []
        filled = [0] * len(cols); widths = set(); n = 0
        it = iter(rows)
        def gen():
            yield from it
            yield from rd
        samples = []
        for r in gen():
            n += 1; widths.add(len(r))
            if len(samples) < a.rows: samples.append(r)
            for i, v in enumerate(r[:len(cols)]):
                if v.strip(): filled[i] += 1
            if n >= a.sample: break
    print(f"-- columnas ({len(cols)}):  relleno sobre las primeras {n:,} filas")
    for i, c in enumerate(cols):
        pct = 100 * filled[i] / n if n else 0
        ex = next((cut(s[i], 30) for s in samples if i < len(s) and s[i].strip()), "")
        print(f"  {i:>3} {cut(c, 28):<28} {pct:5.1f}%   ej: {ex}")
    if len(widths) > 1:
        print(f"  !! filas con distinto nº de campos: {sorted(widths)[:10]} (revisar separador/comillas)")
    print(f"-- {len(samples)} filas de muestra:")
    for s in samples:
        print("  " + " | ".join(cut(v, 25) for v in s[:12]) + (" | …" if len(s) > 12 else ""))

def peek_sqlite(path, a):
    print(f"== {path}  ({human(os.path.getsize(path))}, SQLite)")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)   # solo lectura, garantizado
    cur = con.cursor()
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    if a.table:
        tables = [t for t in tables if t == a.table] or print(f"  (no existe la tabla {a.table})") or []
    for t in tables:
        q = 'SELECT COUNT(*) FROM "%s"' % t
        cnt = "" if a.no_count else f"{cur.execute(q).fetchone()[0]:,} filas"
        cols = cur.execute(f'PRAGMA table_info("{t}")').fetchall()
        idx = [r[1] for r in cur.execute(f'PRAGMA index_list("{t}")')]
        print(f"-- {t}  {cnt}")
        print("   " + ", ".join(f"{c[1]} {c[2] or '?'}{' PK' if c[5] else ''}" for c in cols))
        if idx: print("   índices: " + ", ".join(idx))
        if a.table and a.rows:
            for r in cur.execute(f'SELECT * FROM "{t}" LIMIT {int(a.rows)}'):
                print("   · " + " | ".join(cut(v, 25) for v in r))
    con.close()

def peek_other(path, a):
    print(f"== {path}  ({human(os.path.getsize(path))}, {count_lines(path):,} líneas)")
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, ln in zip(range(a.rows + 5), f):
            print(f"  {i+1:>4}  {cut(ln.rstrip(), 160)}")

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--sep", help="separador: , ; | o 'tab' (por defecto se detecta)")
    ap.add_argument("--no-header", action="store_true", help="la 1ª fila ya son datos")
    ap.add_argument("--rows", type=int, default=3, help="filas de muestra (3)")
    ap.add_argument("--sample", type=int, default=5000, help="filas para calcular el relleno (5000)")
    ap.add_argument("--table", help="SQLite: solo esta tabla (y muestra --rows filas)")
    ap.add_argument("--no-count", action="store_true", help="SQLite: no contar filas")
    a = ap.parse_args()
    for p in a.files:
        try:
            with open(p, "rb") as f: magic = f.read(16)
            ext = os.path.splitext(p)[1].lower()
            if magic.startswith(b"SQLite format 3"): peek_sqlite(p, a)
            elif ext in (".csv", ".tsv", ".txt", ".tab", ".psv"): peek_table_file(p, a)
            else: peek_other(p, a)
        except Exception as e:
            print(f"== {p}: ERROR {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
