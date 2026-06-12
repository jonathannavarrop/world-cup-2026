#!/usr/bin/env python3
"""
Trae los resultados oficiales del Mundial 2026 desde API-Football (plan gratis)
y los vuelca en data/results.json con el esquema que consume score.py.

Config:
  - Crea cuenta gratis en https://www.api-football.com/  (100 peticiones/día)
  - Exporta tu clave:   export APIFOOTBALL_KEY=xxxxxxxx
  - League id del Mundial = 1 ; temporada = 2026

Lo que NO da la API (mejor jugador, MVP, paradas de penalti, falta/olímpico):
  -> se rellena a mano en data/manual.json. Ver README.

Uso:  python engine/fetch_results.py
"""
import os, json, time, urllib.request, datetime

KEY = os.environ.get("APIFOOTBALL_KEY", "")
HOST = "https://v3.football.api-sports.io"
LEAGUE, SEASON = 1, 2026
DATA = os.path.join(os.path.dirname(__file__), "..", "data")

# Mapea el nombre de la API al canónico de la porra si difiere (rellena según veas)
ALIAS = {"USA": "USA", "South Korea": "South Korea", "Czech Republic": "Czechia",
         "Turkey": "Turkiye", "Côte d'Ivoire": "Ivory Coast", "Curaçao": "Curacao",
         "Cape Verde Islands": "Cape Verde", "DR Congo": "DR Congo"}
def canon(n): return ALIAS.get(n, n)

ROUND_MAP = {  # nombre de ronda en la API -> clave de la porra
    "Round of 32": "R32", "Round of 16": "R16", "Quarter-finals": "QF",
    "Semi-finals": "SF", "Final": "Final",
}


def api(path, **params):
    q = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    req = urllib.request.Request(f"{HOST}{path}?{q}", headers={"x-apisports-key": KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["response"]


def build():
    res = {
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "group_results": {}, "final_standings": {},
        "advanced": {k: [] for k in ["R32", "R16", "QF", "SF", "Final", "Champion"]},
        "goals": [], "golden_boot": [], "best_player": None, "motm": [],
        "cards": [], "own_goals_by_team": {}, "penalties_conceded_by_team": {},
        "penalties_saved": {},
    }
    fixtures = api("/fixtures", league=LEAGUE, season=SEASON)
    scorers = {}

    for fx in fixtures:
        st = fx["fixture"]["status"]["short"]
        finished = st in ("FT", "AET", "PEN")
        rnd = fx["league"]["round"]
        home = canon(fx["teams"]["home"]["name"])
        away = canon(fx["teams"]["away"]["name"])
        gh, ga = fx["goals"]["home"], fx["goals"]["away"]

        # --- fase de grupos: marcador real por nº de partido ---
        # API-Football numera la jornada en 'round' (Group Stage - N). Aquí usamos
        # el nº secuencial 1..72 si lo mapeas; si no, usa (home,away) para casar.
        if rnd.startswith("Group") and finished:
            # Empareja por equipos contra predictions (más robusto que el nº):
            res["group_results"][f"{home}|{away}"] = {"home": home, "away": away, "gh": gh, "ga": ga}

        # --- fases finales: quién pasa ---
        key = ROUND_MAP.get(rnd.split(" - ")[0])
        if key and finished:
            winner = home if (gh, ga) > (ga, gh) else away  # PEN ya viene resuelto en goals
            res["advanced"][key] += [home, away] if key == "R32" else []
            res["advanced"][key].append(winner)
            if key == "Final":
                res["advanced"]["Champion"].append(winner)

        # --- eventos (goles, tarjetas, penaltis) ---
        if finished:
            for ev in api("/fixtures/events", fixture=fx["fixture"]["id"]):
                team = canon(ev["team"]["name"])
                pl = (ev.get("player") or {}).get("name")
                typ, det = ev["type"], (ev.get("detail") or "")
                if typ == "Goal":
                    if det == "Own Goal":
                        res["own_goals_by_team"][team] = res["own_goals_by_team"].get(team, 0) + 1
                    elif det == "Missed Penalty":
                        res["goals"].append({"player": pl, "team": team, "type": "missed"})
                    elif det == "Penalty":
                        res["goals"].append({"player": pl, "team": team, "type": "penalty"})
                        scorers[pl] = scorers.get(pl, 0) + 1
                        # penalti concedido por el rival:
                        opp = away if team == home else home
                        res["penalties_conceded_by_team"][opp] = res["penalties_conceded_by_team"].get(opp, 0) + 1
                    else:
                        res["goals"].append({"player": pl, "team": team, "type": "normal"})
                        scorers[pl] = scorers.get(pl, 0) + 1
                elif typ == "Card":
                    kind = "yellow" if det == "Yellow Card" else "red"
                    if det == "Red Card" and "second yellow" in (ev.get("comments") or "").lower():
                        kind = "double_yellow"
                    res["cards"].append({"match": fx["fixture"]["id"], "player": pl, "team": team, "type": kind})
            time.sleep(0.2)  # cuidado con el rate-limit del plan gratis

    # --- standings finales por grupo (posición 1A..4L) ---
    try:
        groups = api("/standings", league=LEAGUE, season=SEASON)[0]["league"]["standings"]
        for grp in groups:
            letter = grp[0]["group"].replace("Group ", "").strip()[:1]
            for row in grp:
                code = f"{row['rank']}{letter}"
                res["final_standings"][code] = {
                    "team": canon(row["team"]["name"]), "pts": row["points"],
                    "gf": row["all"]["goals"]["for"], "gd": row["goalsDiff"],
                }
    except Exception as e:
        print("  (standings aún no disponibles)", e)

    # --- bota de oro (al acabar el torneo) ---
    if scorers:
        mx = max(scorers.values())
        res["golden_boot"] = [p for p, n in scorers.items() if n == mx]

    return res


if __name__ == "__main__":
    if not KEY:
        raise SystemExit("Falta APIFOOTBALL_KEY. Ver README.")
    data = build()
    with open(os.path.join(DATA, "results.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"-> results.json  ({len(data['group_results'])} partidos de grupo, "
          f"{len(data['goals'])} goles, {len(data['cards'])} tarjetas)")
