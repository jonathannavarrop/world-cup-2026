#!/usr/bin/env python3
"""
Motor de puntuación de la Porra Mundial 2026.

Lee:
  data/predictions.json   -> pronósticos de cada jugador (de extract_predictions.py)
  data/results.json       -> resultados oficiales (de fetch_results.py o a mano)
  data/manual.json        -> datos que la API no da (MVP, paradas de penalti, etc.)
Escribe:
  data/standings.json     -> clasificación + desglose por categoría (lo lee la web)

El motor solo suma lo que ya tiene dato, así que puede correr en vivo
durante todo el torneo y la clasificación se va actualizando sola.
"""
import json, os, collections

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

KO_POINTS = {"R32": 30, "R16": 50, "QF": 80, "SF": 120, "Final": 170}
CHAMPION_POINTS = 250
R32_POSITION_BONUS = 30

# Ajustes manuales permanentes (se aplican después del cálculo automático).
# Formato: {jugador: {bloque: delta_pts}}
MANUAL_ADJUSTMENTS = {
    "JONY": {"grupos": -3},
}


def load(name, default):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sign(gh, ga):
    return "1" if gh > ga else ("2" if ga > gh else "X")


def score_match(p, a):
    """Puntos de un pronóstico de partido de grupos frente al resultado real."""
    pts = 0
    if sign(p["gh"], p["ga"]) == sign(a["gh"], a["ga"]):
        pts += 30                                   # acierto 1X2
        if p["gh"] == a["gh"] and p["ga"] == a["ga"]:
            pts += 30                               # marcador exacto
    pts -= 3 * (abs(p["gh"] - a["gh"]) + abs(p["ga"] - a["ga"]))  # diferencia de goles
    return pts


def score_prizes(pred, prize_points):
    """Puntos de premios especiales a partir de data/manual.json['prize_points']."""
    picks = pred.get("prizes", {})
    breakdown = {}
    total = 0
    for key, value in picks.items():
        table = prize_points.get(key, {})
        if isinstance(value, list):
            pts = sum(table.get(v, 0) for v in value if v)
        elif value:
            pts = table.get(value, 0)
        else:
            pts = 0
        breakdown[key] = pts
        total += pts
    return total, breakdown


def score_player(pred, res, prize_points):
    b = collections.OrderedDict()  # desglose por bloque

    # ---------- FASE DE GRUPOS ----------
    gp = 0
    gres = res.get("group_results", {})
    for num, p in pred["group"].items():
        a = gres.get(f"{p['home']}|{p['away']}") or gres.get(str(num))
        if not a or p["gh"] is None:
            continue
        gp += score_match(p, a)
    b["grupos"] = gp

    # ---------- FASES FINALES (equipos que pasan de ronda) ----------
    adv = res.get("advanced", {})
    actual_pos = {v["team"]: code for code, v in res.get("final_standings", {}).items() if isinstance(v, dict) and v.get("team")}
    pred_pos   = {v["team"]: code for code, v in pred.get("standings",      {}).items() if isinstance(v, dict) and v.get("team")}

    # R32: 30 pts por equipo + 30 bonus si misma posición (solo 1os y 2os, nunca 3os)
    r32_teams = set(pred["advance"].get("R32", [])) & set(adv.get("R32", []))
    r32 = 30 * len(r32_teams)
    for team in r32_teams:
        apos = actual_pos.get(team, "")
        if pred_pos.get(team) == apos and apos and apos[0] in ("1", "2"):
            r32 += R32_POSITION_BONUS
    b["r32"] = r32

    # R16, QF, SF, Final — puntos por ronda
    for rnd, pts in [("R16", 50), ("QF", 80), ("SF", 120), ("Final", 170)]:
        hit = set(pred["advance"].get(rnd, [])) & set(adv.get(rnd, []))
        key = rnd.lower()
        b[key] = b.get(key, 0) + pts * len(hit)

    # Campeón
    champ = pred["advance"].get("Champion", [])
    b["champion"] = CHAMPION_POINTS if champ and champ[0] in adv.get("Champion", []) else 0

    # ---------- PREMIOS ESPECIALES ----------
    prize_total, prize_breakdown = score_prizes(pred, prize_points)
    b["premios"] = prize_total

    total = sum(b.values())
    return total, b, prize_breakdown


def apply_adjustments(alias, total, breakdown):
    adj = MANUAL_ADJUSTMENTS.get(alias, {})
    for block, delta in adj.items():
        breakdown[block] = breakdown.get(block, 0) + delta
    total = sum(breakdown.values())
    return total, breakdown


def main():
    preds = load("predictions.json", {})
    res = load("results.json", {})
    manual = load("manual.json", {})
    prize_points = manual.get("prize_points", {})

    table = []
    prize_scores = {}
    for alias, pred in preds.items():
        total, breakdown, prize_breakdown = score_player(pred, res, prize_points)
        total, breakdown = apply_adjustments(alias, total, breakdown)
        row = {"player": alias, "total": total}
        row.update(breakdown)          # aplana grupos, r32, r16, qf, sf, champion, premios
        row.update(prize_breakdown)    # aplana cada premio especial como columna propia
        table.append(row)
        prize_scores[alias] = prize_breakdown
    table.sort(key=lambda x: -x["total"])
    for i, row in enumerate(table, 1):
        row["pos"] = i

    # ---------- desglose por partido (fase de grupos) ----------
    matches = []
    for m in res.get("matches", []):
        entry = dict(m)
        predictions = {}
        for alias, pred in preds.items():
            p = pred["group"].get(str(m["num"]))
            if p and m["played"]:
                predictions[alias] = {"gh": p["gh"], "ga": p["ga"], "points": score_match(p, m)}
            elif p:
                predictions[alias] = {"gh": p["gh"], "ga": p["ga"], "points": None}
        entry["predictions"] = predictions
        matches.append(entry)

    # ---------- picks de fases finales por jugador ----------
    advance = {}
    for alias, pred in preds.items():
        advance[alias] = pred.get("advance", {})

    # ---------- picks de premios especiales por jugador ----------
    prizes = {}
    for alias, pred in preds.items():
        prizes[alias] = pred.get("prizes", {})

    out = {
        "updated": res.get("updated"),
        "matches_played": len(res.get("group_results", {})),
        "table": table,
        "matches": matches,
        "advance": advance,
        "prizes": prizes,
        "prize_scores": prize_scores,
        "actual_advanced": res.get("advanced", {}),
        "final_standings": res.get("final_standings", {}),
        "pred_standings": {alias: pred.get("standings", {}) for alias, pred in preds.items()},
    }
    with open(os.path.join(DATA, "standings.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"{'#':>2}  {'JUGADOR':10} {'TOTAL':>6} {'GRUPOS':>7} {'1/16':>6} {'1/8':>6} {'1/4':>6} {'SEMI':>6} {'FINAL':>6} {'CAMP':>6} {'PREMIOS':>8}")
    for row in table:
        print(f"{row['pos']:>2}  {row['player']:10} {row['total']:>6} {row.get('grupos',0):>7} {row.get('r32',0):>6} {row.get('r16',0):>6} {row.get('qf',0):>6} {row.get('sf',0):>6} {row.get('final',0):>6} {row.get('champion',0):>6} {row.get('premios',0):>8}")


if __name__ == "__main__":
    main()
