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

## Qué se puntúa (de momento)

Por ahora solo se puntúan las dos categorías base, que se calculan en
automático a partir de `data/resultados.csv`:

- **Fase de grupos**: 1X2, marcador exacto y diferencia de goles, partido a
  partido.
- **Fases finales**: equipos que pasan de ronda, bonus de posición y campeón.

Los premios extra (Roberswingger, Champ, Paraguaya Chupona, Pinwis, Lobby,
Columna Churu) están **eliminados de momento** de `engine/score.py` y de la
web. `data/manual.json` se deja en el repo por si se reactivan más adelante.

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

## Las 3 páginas

- **`index.html`** — Clasificación general (POFANTASY WORLDCUP 2026). Cada jugador
  es desplegable y muestra, partido a partido, el resultado oficial y los puntos
  obtenidos (verde si son positivos, rojo si son negativos).
- **`predicciones.html`** — Todos los partidos de la fase de grupos, agrupados de
  A a L, con el resultado oficial y, debajo, el pronóstico y los puntos de cada
  jugador.
- **`jugador.html?j=ALIAS`** — Repaso individual: las 72 predicciones de grupos de
  ese jugador (acierto 1X2 / exacto / fallo y puntos), más su pick de fases
  finales.

## Puntuación implementada (de las bases)

- Grupos: 1X2 **+30**, marcador exacto **+30** más, **−3** por cada gol de diferencia.
- Fases finales (por equipo acertado): R32 **+30** (**+30** extra si aciertas la posición),
  octavos **+50**, cuartos **+80**, semis **+120**, final **+170**, campeón **+250**.

> Herramienta de apoyo. Verifica los datos sensibles a mano antes de pagar premios.
