#!/usr/bin/env python3
"""
Convierte el CSV de resultados (lo rellenas tú) en data/results.json.

Lee el CSV de:
  - un fichero local  data/resultados.csv   (por defecto), o
  - una URL (Google Sheet publicado como CSV) si defines:
        export RESULTS_CSV_URL="https://docs.google.com/.../pub?output=csv"

Columnas del CSV:  ronda, local, visitante, gl, gv, clasifica
  - ronda  = letra de grupo (A..L)  |  R32 R16 QF SF Final
  - gl, gv = goles local / visitante  (déjalo vacío si no se ha jugado)
  - clasifica = (solo eliminatorias) equipo que pasa; en la Final, el campeón

Calcula solo las clasificaciones de grupo (pts -> DG -> GF) y quién llega a
cada ronda. Los datos de premios (goles del goleador, tarjetas, MVP, paradas)
van en data/manual.json, que NO se toca aquí.

Uso:  python engine/build_results.py
"""
import os, csv, json, io, datetime, urllib.request

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
KO = {"R32", "R16", "QF", "SF", "FINAL", "FINAL "}
ROUND_KEY = {"R32": "R32", "R16": "R16", "QF": "QF", "SF": "SF", "FINAL": "Final"}


def read_csv():
    url = os.environ.get("RESULTS_CSV_URL")
    if url:
        with urllib.request.urlopen(url, timeout=30) as r:
            text = r.read().decode("utf-8")
    else:
        with open(os.path.join(DATA, "resultados.csv"), encoding="utf-8") as f:
            text = f.read()
    return list(csv.DictReader(io.StringIO(text)))


def num(x):
    x = (x or "").strip()
    return int(x) if x.lstrip("-").isdigit() else None


def build(rows):
    res = {
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "group_results": {}, "final_standings": {}, "matches": [],
        "advanced": {k: [] for k in ["R32", "R16", "QF", "SF", "Final", "Champion"]},
    }
    tables = {}  # grupo -> {equipo: [pts, gf, gc]}

    for r in rows:
        ronda = (r.get("ronda") or "").strip()
        h, a = (r.get("local") or "").strip(), (r.get("visitante") or "").strip()
        gl, gv = num(r.get("gl")), num(r.get("gv"))
        if not h or not a:
            continue
        key = ronda.upper()

        if key in ROUND_KEY:                      # ----- eliminatorias -----
            rk = ROUND_KEY[key]
            res["advanced"][rk] += [h, a]
            clf = (r.get("clasifica") or "").strip()
            if rk == "Final" and clf:
                res["advanced"]["Champion"].append(clf)
            continue

        # ----- fase de grupos -----
        # Use match number from CSV ("lo num" column) to preserve correct ordering
        match_num = num(r.get("lo num"))
        res["matches"].append({
            "num": match_num, "group": ronda.upper(), "home": h, "away": a,
            "gh": gl, "ga": gv, "played": gl is not None and gv is not None,
            "date": (r.get("fecha") or "").strip(),
        })
        if gl is None or gv is None:
            continue
        res["group_results"][f"{h}|{a}"] = {"home": h, "away": a, "gh": gl, "ga": gv}
        g = ronda.upper()
        t = tables.setdefault(g, {})
        t.setdefault(h, [0, 0, 0]); t.setdefault(a, [0, 0, 0])
        t[h][1] += gl; t[h][2] += gv
        t[a][1] += gv; t[a][2] += gl
        if gl > gv:   t[h][0] += 3
        elif gv > gl: t[a][0] += 3
        else:         t[h][0] += 1; t[a][0] += 1

    # clasificación final por grupo (pts -> DG -> GF)
    for g, t in tables.items():
        ranked = sorted(t.items(), key=lambda kv: (-kv[1][0], -(kv[1][1] - kv[1][2]), -kv[1][1]))
        for i, (team, s) in enumerate(ranked, 1):
            res["final_standings"][f"{i}{g}"] = {"team": team, "pts": s[0], "gf": s[1], "gd": s[1] - s[2]}

    # dedup manteniendo orden
    for k in res["advanced"]:
        res["advanced"][k] = list(dict.fromkeys(res["advanced"][k]))
    return res


if __name__ == "__main__":
    data = build(read_csv())
    with open(os.path.join(DATA, "results.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"-> results.json  ({len(data['group_results'])} partidos, "
          f"{len(data['final_standings'])} posiciones de grupo)")
