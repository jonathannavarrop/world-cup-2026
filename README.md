# Porra Mundial 2026 — clasificación automática

Una clasificación **en vivo, con un solo enlace** para los 5 participantes (CHURU, JONY,
CHAMP, NEGREIRA, PEP). Coge los pronósticos de cada Excel, los resultados oficiales de
una API gratuita, aplica las bases y publica una tabla que todos ven en la misma URL.

```
Excel de cada uno ─► predictions.json ─┐
API-Football ─► fetch_results.py ─► results.json ─┤
admin (a mano) ─► manual.json ────────┘
                                       └► score.py ─► data/standings.json ─► index.html (GitHub Pages)
```

## Por qué este montaje

- **Gratis y un solo enlace**: GitHub Pages sirve `index.html` en
  `https://TU-USUARIO.github.io/porra-2026/`. Esa es la URL que repartes.
- **Se actualiza solo**: GitHub Actions ejecuta el cálculo cada pocas horas y publica
  la tabla. Nadie tiene que tocar nada en día de partido.
- **Sin servidor que mantener** y los pronósticos quedan congelados en el repo.

## Qué se puntúa solo y qué hay que meter a mano

Ninguna API gratuita da TODO lo que piden las bases. Reparto realista:

| Categoría | Automático (API) | A mano (`manual.json`) |
|---|---|---|
| Marcadores de grupo, 1X2, diferencia de goles | ✅ | |
| Equipos que pasan de ronda + bonus de posición | ✅ | |
| Premio LOBBY (peor selección) | ✅ | |
| Roberswingger: gol normal / penalti / penalti fallado / bota de oro | ✅ | falta vs olímpico (+30/+50) |
| Paraguaya Chupona: amarillas, rojas, goles en propia | ✅ | (penaltis cometidos: revisa) |
| Pinwis: amarilla / doble amarilla / roja | ✅ | |
| Champ: mejor jugador del torneo / MVP del partido | | ✅ (la API gratis no da MVP) |
| Columna Churu: MVP portero / penaltis parados | | ✅ |

Lo manual son 4 cosas y se editan en `data/manual.json` tras cada jornada. Es poco.

## Fuente de datos

- **Principal: API-Football** (`api-football.com`) — plan gratis 100 peticiones/día,
  cubre el Mundial con goles, tarjetas, penaltis y clasificaciones. Suficiente si no
  refrescas cada segundo (con el cron cada 3 h sobra).
- **Alternativas**: `football-data.org` (gratis, 10 llamadas/min, más básico) y
  `openfootball/worldcup.json` (dominio público, sin clave, pero **no** en vivo:
  sirve de respaldo para marcadores).
- Si un día la API falla, puedes editar `data/results.json` a mano: el motor lo acepta igual.

## Puesta en marcha (una vez)

1. Crea un repo en GitHub y sube esta carpeta.
2. Saca clave gratis en api-football.com → repo **Settings ▸ Secrets ▸ Actions** →
   crea `APIFOOTBALL_KEY`.
3. **Settings ▸ Pages** → *Deploy from branch* → `main` / `(root)`.
4. Listo: la URL de Pages es el enlace que repartes.

## Meter / actualizar pronósticos

Cuando alguien cambie su Excel (incluido CHURU, que aún no ha rellenado el bracket):

```bash
python engine/extract_predictions.py /ruta/a/los/excels
```

Los **6 premios extra todavía no están en los Excel**. Pon el pick de cada uno en
`data/predictions.json`, dentro de `"prizes"` de cada jugador, p.ej.:

```json
"prizes": {
  "roberswingger": "Kylian Mbappe",
  "champ": "Lamine Yamal",
  "paraguaya_chupona": "Uruguay",
  "pinwis": ["Cristian Romero", "Marcos Acuna"],
  "lobby": "Haiti",
  "columna_churu": "Emiliano Martinez"
}
```

(Usa nombres en inglés, igual que la API; las selecciones igual que en `engine/_names.py`.)

## Cómo se actualiza día a día (vía MANUAL recomendada)

Los pronósticos NO cambian. Lo único que rellenas es **`data/resultados.csv`**, que se
edita como una hoja de cálculo. Columnas: `ronda, local, visitante, gl, gv, clasifica`.

- Grupos: `ronda` = letra del grupo (A..L). Pones `gl` y `gv` cuando se juega el partido.
- Eliminatorias: `ronda` = `R32 R16 QF SF Final`; añades la fila del cruce con su marcador,
  y en `clasifica` el equipo que pasa (en la Final, el campeón).

Después de cada jornada:

```bash
python engine/build_results.py   # CSV -> data/results.json (calcula tablas y quién pasa)
python engine/score.py           # -> data/standings.json (la web lee esto)
```

En GitHub: editas `resultados.csv` (incluso desde el móvil, en la web del repo), guardas,
y el Action recalcula y publica la tabla solo. Todos la ven en el mismo enlace de Pages.

### Opción "edito en Google Sheets" (cero JSON, cero CSV en el repo)

1. Sube `resultados.csv` a una hoja de Google.
2. *Archivo ▸ Compartir ▸ Publicar en la web ▸ CSV* y copia el enlace.
3. Repo **Settings ▸ Variables ▸ Actions** → crea `RESULTS_CSV_URL` con ese enlace.

Ahora editas marcadores en la hoja; el Action la lee cada 6 h y actualiza el enlace.

> Datos de premios (goles de tu goleador, tarjetas, MVP, paradas) van en `data/manual.json`,
> no en el CSV. Así sobreviven aunque regeneres los resultados.

## Probar en local

```bash
pip install openpyxl
python engine/extract_predictions.py /ruta/a/los/excels   # solo si cambian los Excel
python engine/build_results.py                            # CSV -> results.json
python engine/score.py                                    # -> standings.json + tabla
```

Abre `index.html` y verás la clasificación. *(La vía con API, `fetch_results.py`, sigue
disponible si algún día la quieres; necesita `APIFOOTBALL_KEY`.)*

## Puntuación implementada (de las bases)

- Grupos: 1X2 **+30**, marcador exacto **+30** más, **−3** por cada gol de diferencia.
- Fases finales (por equipo acertado): R32 **+30** (**+30** extra si aciertas la posición),
  octavos **+50**, cuartos **+80**, semis **+120**, final **+170**, campeón **+250**.
- Roberswingger: normal +20, falta +30, olímpico +50, penalti +10, fallado −10, bota de oro +60.
- Champ: mejor jugador del torneo +100, MVP de partido +25.
- Paraguaya Chupona: amarilla +15, roja directa +60, doble amarilla +30 (2 amarillas),
  gol en propia +100, penalti cometido +50.
- Pinwis: amarilla +15, doble amarilla +50, roja directa +100.
- Lobby: +100 (peor por pts → DG → GF).
- Columna Churu: MVP +80, penalti parado +50.

> Herramienta de apoyo. Verifica los datos sensibles (MVP, tipos de gol) a mano antes de pagar premios.
