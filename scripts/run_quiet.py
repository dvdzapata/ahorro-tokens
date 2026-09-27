#!/usr/bin/env python3
"""run_quiet: ejecuta un comando y devuelve un resumen corto en lugar de toda la salida.

La salida COMPLETA se guarda siempre en un log (no se pierde nada); por pantalla
solo sale: código de salida, duración, nº de líneas, líneas con errores/avisos
(deduplicadas) y las últimas N líneas.

Uso:
  python run_quiet.py "npm run build"
  python run_quiet.py --tail 30 --log build.log "pytest -x"
  python run_quiet.py --pattern "FAIL|Traceback" "comando"
Funciona igual en Linux y en Windows (en Windows el comando lo interpreta cmd.exe;
para PowerShell usa: python run_quiet.py "powershell -NoProfile -Command ...").
"""
import argparse, os, re, subprocess, sys, tempfile, time

DEFAULT_PATTERN = (r"\b(error|errors|failed|failure|fatal|exception|traceback|"
                   r"warning|warn|denied|not found|cannot|unable|panic)\b|✖|✗")

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", help="comando a ejecutar, entre comillas")
    ap.add_argument("--tail", type=int, default=15, help="últimas líneas a mostrar (15)")
    ap.add_argument("--max-matches", type=int, default=25, help="máx. líneas de error/aviso (25)")
    ap.add_argument("--pattern", default=DEFAULT_PATTERN, help="regex de líneas relevantes")
    ap.add_argument("--short", type=int, default=40, help="si hay <= N líneas, mostrar todo (40)")
    ap.add_argument("--log",help="ruta del log completo (por defecto, uno temporal)")
    ap.add_argument("--cwd", help="directorio de trabajo")
    ap.add_argument("--timeout", type=int, default=None, help="segundos antes de abortar")
    a = ap.parse_args()

    log = a.log or os.path.join(tempfile.gettempdir(), f"run_quiet_{int(time.time())}.log")
    t0 = time.time()
    try:
        p = subprocess.run(a.command, shell=True, cwd=a.cwd, capture_output=True,
                           timeout=a.timeout)
        code, raw = p.returncode, p.stdout + (b"\n" + p.stderr if p.stderr else b"")
    except subprocess.TimeoutExpired as e:
        code, raw = "TIMEOUT", (e.stdout or b"") + (e.stderr or b"")
    dur = time.time() - t0

    text = raw.decode("utf-8", errors="replace")
    with open(log, "w", encoding="utf-8") as f:
        f.write(text)
    lines = text.splitlines()

    head = f"[run_quiet] salida={code}  tiempo={dur:.1f}s  líneas={len(lines)}  log={log}"
    if len(lines) <= a.short:           # salida corta: resumir costaría más que mostrarla
        print(f"[run_quiet] salida={code}  tiempo={dur:.1f}s")
        print(text.rstrip())
        sys.exit(0 if code == 0 else 1)

    tail_start = len(lines) - min(a.tail, len(lines)) + 1
    rx = re.compile(a.pattern, re.IGNORECASE)
    seen, matches = set(), []
    for i, ln in enumerate(lines[:tail_start - 1], 1):   # lo que ya sale en la cola no se repite
        if rx.search(ln):
            key = re.sub(r"\d+", "#", ln.strip())[:200]   # agrupa líneas casi idénticas
            if key in seen:
                continue
            seen.add(key)
            matches.append(f"  {i}: {ln.strip()[:300]}")
    total_matches = len(matches)

    print(head)
    if matches:
        print(f"-- líneas con error/aviso ({total_matches} distintas"
              f"{', mostrando ' + str(a.max_matches) if total_matches > a.max_matches else ''}):")
        print("\n".join(matches[:a.max_matches]))
    if lines:
        n = min(a.tail, len(lines))
        print(f"-- últimas {n} líneas:")
        print("\n".join("  " + l[:300] for l in lines[-n:]))
    print("-- (salida completa en el log; léela por rangos si hace falta)")
    sys.exit(0 if code == 0 else 1)

if __name__ == "__main__":
    main()
