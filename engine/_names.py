# Mapa nombre-plantilla (ES) -> nombre canónico (EN), el mismo que usan la API y el HTML.
ES2EN = {
 "México": "Mexico", "Sudáfrica": "South Africa", "Corea del Sur": "South Korea",
 "República Checa": "Czechia", "Canadá": "Canada", "Suiza": "Switzerland", "Catar": "Qatar",
 "Bosnia y Herzegovina": "Bosnia-Herzegovina", "Brasil": "Brazil", "Marruecos": "Morocco",
 "Escocia": "Scotland", "Haití": "Haiti", "Estados Unidos": "USA", "Paraguay": "Paraguay",
 "Australia": "Australia", "Turquía": "Turkiye", "Alemania": "Germany", "Ecuador": "Ecuador",
 "Costa de Marfil": "Ivory Coast", "Curazao": "Curacao", "Países Bajos": "Netherlands",
 "Japón": "Japan", "Túnez": "Tunisia", "Suecia": "Sweden", "Bélgica": "Belgium", "Irán": "Iran",
 "Egipto": "Egypt", "Nueva Zelanda": "New Zealand", "España": "Spain", "Uruguay": "Uruguay",
 "Arabia Saudita": "Saudi Arabia", "Cabo Verde": "Cape Verde", "Francia": "France",
 "Senegal": "Senegal", "Noruega": "Norway", "Irak": "Iraq", "Argentina": "Argentina",
 "Austria": "Austria", "Argelia": "Algeria", "Jordania": "Jordan", "Portugal": "Portugal",
 "Colombia": "Colombia", "Uzbekistán": "Uzbekistan", "RD Congo": "DR Congo",
 "Inglaterra": "England", "Croacia": "Croatia", "Panamá": "Panama", "Ghana": "Ghana",
}
EN2ES = {v: k for k, v in ES2EN.items()}

def en(name):
    if name is None:
        return None
    return ES2EN.get(str(name).strip(), str(name).strip())
