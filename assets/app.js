// PORRA FANTASY - MUNDIAL DE LOS 2000 — helpers compartidos por todas las páginas.

const PLAYERS = ["CHAMP", "JONY", "PEP", "NEGREIRA", "CHURU"];

// nombre EN (igual que predictions.json / results.json) -> {es, code ISO-3166}
const TEAMS = {
  "Mexico": { es: "México", code: "MX" },
  "South Africa": { es: "Sudáfrica", code: "ZA" },
  "South Korea": { es: "Corea del Sur", code: "KR" },
  "Czechia": { es: "Rep. Checa", code: "CZ" },
  "Canada": { es: "Canadá", code: "CA" },
  "Switzerland": { es: "Suiza", code: "CH" },
  "Qatar": { es: "Catar", code: "QA" },
  "Bosnia-Herzegovina": { es: "Bosnia", code: "BA" },
  "Brazil": { es: "Brasil", code: "BR" },
  "Morocco": { es: "Marruecos", code: "MA" },
  "Scotland": { es: "Escocia", code: "GB" },
  "Haiti": { es: "Haití", code: "HT" },
  "USA": { es: "Estados Unidos", code: "US" },
  "Paraguay": { es: "Paraguay", code: "PY" },
  "Australia": { es: "Australia", code: "AU" },
  "Turkiye": { es: "Turquía", code: "TR" },
  "Germany": { es: "Alemania", code: "DE" },
  "Ecuador": { es: "Ecuador", code: "EC" },
  "Ivory Coast": { es: "Costa de Marfil", code: "CI" },
  "Curacao": { es: "Curazao", code: "CW" },
  "Netherlands": { es: "Países Bajos", code: "NL" },
  "Japan": { es: "Japón", code: "JP" },
  "Tunisia": { es: "Túnez", code: "TN" },
  "Sweden": { es: "Suecia", code: "SE" },
  "Belgium": { es: "Bélgica", code: "BE" },
  "Iran": { es: "Irán", code: "IR" },
  "Egypt": { es: "Egipto", code: "EG" },
  "New Zealand": { es: "Nueva Zelanda", code: "NZ" },
  "Spain": { es: "España", code: "ES" },
  "Uruguay": { es: "Uruguay", code: "UY" },
  "Saudi Arabia": { es: "Arabia Saudí", code: "SA" },
  "Cape Verde": { es: "Cabo Verde", code: "CV" },
  "France": { es: "Francia", code: "FR" },
  "Senegal": { es: "Senegal", code: "SN" },
  "Norway": { es: "Noruega", code: "NO" },
  "Iraq": { es: "Irak", code: "IQ" },
  "Argentina": { es: "Argentina", code: "AR" },
  "Austria": { es: "Austria", code: "AT" },
  "Algeria": { es: "Argelia", code: "DZ" },
  "Jordan": { es: "Jordania", code: "JO" },
  "Portugal": { es: "Portugal", code: "PT" },
  "Colombia": { es: "Colombia", code: "CO" },
  "Uzbekistan": { es: "Uzbekistán", code: "UZ" },
  "DR Congo": { es: "RD Congo", code: "CD" },
  "England": { es: "Inglaterra", code: "GB" },
  "Croatia": { es: "Croacia", code: "HR" },
  "Panama": { es: "Panamá", code: "PA" },
  "Ghana": { es: "Ghana", code: "GH" },
};

function flagEmoji(code) {
  if (!code) return "🏳️";
  return code.toUpperCase().split("").map(c => String.fromCodePoint(127397 + c.charCodeAt(0))).join("");
}

function teamES(name) {
  return (TEAMS[name] && TEAMS[name].es) || name;
}

function teamFlag(name) {
  return flagEmoji(TEAMS[name] && TEAMS[name].code);
}

// Devuelve el HTML de los puntos con signo y color (verde positivo / rojo negativo).
function ptsHtml(points) {
  if (points === null || points === undefined) return '<span class="pts-na">—</span>';
  const cls = points > 0 ? "pts-pos" : (points < 0 ? "pts-neg" : "pts-zero");
  const sign = points > 0 ? "+" : "";
  return `<span class="${cls}">${sign}${points}pts</span>`;
}

const WEEKDAYS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];
const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

// "2026-06-13 3:00" -> "sáb 13 jun · 03:00"
function matchDateLabel(dateStr) {
  if (!dateStr) return "";
  const m = dateStr.match(/^(\d{4})-(\d{2})-(\d{2}) (\d{1,2}):(\d{2})$/);
  if (!m) return "";
  const [, y, mo, d, h, mi] = m.map(Number);
  const date = new Date(y, mo - 1, d, h, mi);
  const time = `${String(h).padStart(2, "0")}:${String(mi).padStart(2, "0")}`;
  return `${WEEKDAYS[date.getDay()]} ${d} ${MONTHS[mo - 1]} · ${time}`;
}

async function fetchJSON(path) {
  const res = await fetch(`${path}?t=${Date.now()}`);
  if (!res.ok) throw new Error(`No se pudo cargar ${path}`);
  return res.json();
}

// Inserta la barra de navegación compartida en el elemento con id="nav".
function renderNav(active) {
  const el = document.getElementById("nav");
  if (!el) return;
  const links = [
    { href: "index.html", label: "Clasificación", key: "clasificacion" },
    { href: "predicciones.html", label: "Predicciones", key: "predicciones" },
  ];
  const navLinksBefore = links.map(l =>
    `<a class="nav-link ${active === l.key ? "active" : ""}" href="${l.href}">${l.label}</a>`).join("");
  el.innerHTML = `
    <div class="nav-inner">
      <a class="brand" href="index.html">
        <span class="brand-ball">⚽</span>
        <span class="brand-text"><span class="brand-porra">PORRA FANTASY</span><span class="brand-wc">MUNDIAL DE LOS 2000</span></span>
      </a>
      <div class="nav-links">
        ${navLinksBefore}
        <a class="nav-link ${active && active.startsWith("jugador") ? "active" : ""}" href="jugador.html">Mi porra</a>
        <a class="nav-link ${active === "reglas" ? "active" : ""}" href="reglas.html">Reglas</a>
      </div>
    </div>`;
}
