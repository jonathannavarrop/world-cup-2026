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

GOAL_POINTS = {"normal": 20, "freekick": 30, "olympic": 50, "penalty": 10, "missed": -10}
GOLDEN_BOOT = 60
BEST_PLAYER = 100
MOTM = 25
CARD_TEAM = {"yellow": 15, "double_yellow": 30, "red": 60}     # Paraguaya Chupona
OWN_GOAL_TEAM = 100
PENALTY_CONCEDED_TEAM = 50
CARD_PINWIS = {"yellow": 15, "double_yellow": 50, "red": 100}  # Pinwis
LOBBY = 100
KEEPER_MOTM = 80
KEEPER_PEN_SAVED = 50


def load(name, default):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sign(gh, ga):
    return "1" if gh > ga else ("2" if ga > gh else "X")


def worst_team(final_standings):
    """Peor selección: menos pts -> peor DG -> menos GF (premio LOBBY)."""
    teams = [v for v in final_standings.values() if isinstance(v, dict) and v.get("team")]
    if not teams:
        return None
    teams.sort(key=lambda t: (t.get("pts", 0), t.get("gd", 0), t.get("gf", 0)))
    return teams[0]["team"]


def score_player(pred, res, manual):
    b = collections.OrderedDict()  # desglose por bloque

    # ---------- FASE DE GRUPOS ----------
    gp = 0
    gres = res.get("group_results", {})
    for num, p in pred["group"].items():
        a = gres.get(f"{p['home']}|{p['away']}") or gres.get(str(num))
        if not a or p["gh"] is None:
            continue
        if sign(p["gh"], p["ga"]) == sign(a["gh"], a["ga"]):
            gp += 30                                   # acierto 1X2
            if p["gh"] == a["gh"] and p["ga"] == a["ga"]:
                gp += 30                               # marcador exacto
        gp -= 3 * (abs(p["gh"] - a["gh"]) + abs(p["ga"] - a["ga"]))  # diferencia de goles
    b["grupos"] = gp

    # ---------- FASES FINALES (equipos que pasan de ronda) ----------
    adv = res.get("advanced", {})
    kp = 0
    for rnd, pts in KO_POINTS.items():
        hit = set(pred["advance"].get(rnd, [])) & set(adv.get(rnd, []))
        kp += pts * len(hit)
    # bonus +30 por acertar la posición exacta del grupo (solo dieciseisavos)
    actual_pos = {v["team"]: code for code, v in res.get("final_standings", {}).items() if isinstance(v, dict) and v.get("team")}
    pred_pos = {v["team"]: code for code, v in pred.get("standings", {}).items() if isinstance(v, dict) and v.get("team")}
    for team in set(pred["advance"].get("R32", [])) & set(adv.get("R32", [])):
        if pred_pos.get(team) and pred_pos.get(team) == actual_pos.get(team):
            kp += R32_POSITION_BONUS
    # campeón
    if pred["advance"].get("Champion") and pred["advance"]["Champion"][0] in adv.get("Champion", []):
        kp += CHAMPION_POINTS
    b["fases_finales"] = kp

    pz = pred["prizes"]

    # ---------- ROBERSWINGGER (máximo goleador) ----------
    rob = 0
    pick = pz.get("roberswingger")
    if pick:
        for g in res.get("goals", []):
            if g.get("player") == pick:
                rob += GOAL_POINTS.get(g.get("type", "normal"), 0)
        if pick in res.get("golden_boot", []):
            rob += GOLDEN_BOOT
    b["roberswingger"] = rob

    # ---------- CHAMP (mejor jugador) ----------
    ch = 0
    pick = pz.get("champ")
    if pick:
        ch += MOTM * res.get("motm", []).count(pick)
        if res.get("best_player") == pick:
            ch += BEST_PLAYER
    b["champ"] = ch

    # ---------- PARAGUAYA CHUPONA (selección más agresiva) ----------
    pc = 0
    team = pz.get("paraguaya_chupona")
    if team:
        for c in res.get("cards", []):
            if c.get("team") == team:
                pc += CARD_TEAM.get(c.get("type", "yellow"), 0)
        pc += OWN_GOAL_TEAM * res.get("own_goals_by_team", {}).get(team, 0)
        pc += PENALTY_CONCEDED_TEAM * res.get("penalties_conceded_by_team", {}).get(team, 0)
    b["paraguaya_chupona"] = pc

    # ---------- PINWIS (2 jugadores más guarros) ----------
    pw = 0
    for pick in (pz.get("pinwis") or []):
        if not pick:
            continue
        for c in res.get("cards", []):
            if c.get("player") == pick:
                pw += CARD_PINWIS.get(c.get("type", "yellow"), 0)
    b["pinwis"] = pw

    # ---------- LOBBY (peor selección) ----------
    lb = 0
    pick = pz.get("lobby")
    if pick and res.get("final_standings"):
        if pick == worst_team(res["final_standings"]):
            lb = LOBBY
    b["lobby"] = lb

    # ---------- COLUMNA CHURU (mejor portero) ----------
    cc = 0
    pick = pz.get("columna_churu")
    if pick:
        cc += KEEPER_MOTM * res.get("motm", []).count(pick)
        cc += KEEPER_PEN_SAVED * res.get("penalties_saved", {}).get(pick, 0)
    b["columna_churu"] = cc

    total = sum(b.values())
    return total, b


def main():
    preds = load("predictions.json", {})
    res = load("results.json", {})
    manual = load("manual.json", {})

    # los datos manuales sobrescriben/rellenan lo que la API no puede dar
    for k, v in manual.items():
        if isinstance(v, dict):
            res.setdefault(k, {}).update(v)
        elif isinstance(v, list):
            res[k] = (res.get(k) or []) + v
        else:
            res[k] = v

    table = []
    for alias, pred in preds.items():
        total, breakdown = score_player(pred, res, manual)
        table.append({"player": alias, "total": total, "breakdown": breakdown})
    table.sort(key=lambda x: -x["total"])
    for i, row in enumerate(table, 1):
        row["pos"] = i

    out = {
        "updated": res.get("updated"),
        "matches_played": len(res.get("group_results", {})),
        "table": table,
    }
    with open(os.path.join(DATA, "standings.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"{'#':>2}  {'JUGADOR':10} {'TOTAL':>6}   desglose")
    for row in table:
        bd = "  ".join(f"{k[:4]}={v}" for k, v in row["breakdown"].items() if v)
        print(f"{row['pos']:>2}  {row['player']:10} {row['total']:>6}   {bd}")


if __name__ == "__main__":
    main()
