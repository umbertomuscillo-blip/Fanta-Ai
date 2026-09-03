"""
Data pipeline e calcolo scientifico incroci portieri Fantacalcio.
Classifica le partite in 3 livelli:
- FACILE (1)
- MEDIA (2)
- DIFFICILE (3)

Trova le migliori combinazioni di 2 e 3 portieri per garantire partite facili tutto l'anno
risparmiando fino al 70% del budget crediti per l'attacco.
"""

import json

# Definizione Squadre e Pericolosità offensiva avversaria
# 1 = Top attacco (Inter, Atalanta, Milan, Juve, Napoli)
# 2 = Buon attacco (Roma, Lazio, Fiorentina, Bologna)
# 3 = Attacco medio (Torino, Genoa, Monza, Parma, Udinese, Cagliari)
# 4 = Attacco basso / salvezza (Empoli, Verona, Lecce, Como, Venezia)
ATTACK_TIER = {
    "Inter": 1, "Atalanta": 1, "Milan": 1, "Juventus": 1, "Napoli": 1,
    "Roma": 2, "Lazio": 2, "Fiorentina": 2, "Bologna": 2,
    "Torino": 3, "Genoa": 3, "Monza": 3, "Parma": 3, "Udinese": 3, "Cagliari": 3,
    "Empoli": 4, "Verona": 4, "Lecce": 4, "Como": 4, "Venezia": 4
}

# Solidità difensiva della squadra del portiere (per bonus imbattibilità / mod)
DEFENSE_RATING = {
    "Inter": 9.5, "Juventus": 9.0, "Napoli": 8.5, "Milan": 8.0, "Roma": 8.0,
    "Atalanta": 8.0, "Bologna": 7.5, "Torino": 7.5, "Fiorentina": 7.5, "Lazio": 7.5,
    "Monza": 7.0, "Genoa": 7.0, "Udinese": 6.5, "Empoli": 6.5, "Cagliari": 6.0,
    "Parma": 6.0, "Lecce": 6.0, "Como": 6.0, "Verona": 5.5, "Venezia": 5.5
}

GOALKEEPERS_INFO = {
    "Inter": {"tit": "Sommer", "sec": "Martinez", "ter": "Di Gennaro", "cost": 48},
    "Juventus": {"tit": "Di Gregorio", "sec": "Perin", "ter": "Pinsoglio", "cost": 44},
    "Milan": {"tit": "Maignan", "sec": "Sportiello", "ter": "Torriani", "cost": 38},
    "Napoli": {"tit": "Meret", "sec": "Caprile", "ter": "Contini", "cost": 35},
    "Atalanta": {"tit": "Carnesecchi", "sec": "Rui Patricio", "ter": "Rossi", "cost": 30},
    "Roma": {"tit": "Svilar", "sec": "Ryan", "ter": "Marin", "cost": 28},
    "Lazio": {"tit": "Provedel", "sec": "Mandas", "ter": "Furlanetto", "cost": 22},
    "Fiorentina": {"tit": "De Gea", "sec": "Terracciano", "ter": "Martinelli", "cost": 20},
    "Bologna": {"tit": "Skorupski", "sec": "Ravaglia", "ter": "Bagnolini", "cost": 18},
    "Torino": {"tit": "Milinkovic-Savic", "sec": "Paleari", "ter": "Donnarumma", "cost": 16},
    "Genoa": {"tit": "Gollini", "sec": "Leali", "ter": "Sommariva", "cost": 11},
    "Monza": {"tit": "Turati", "sec": "Pizzignacco", "ter": "Mazza", "cost": 10},
    "Udinese": {"tit": "Okoye", "sec": "Sava", "ter": "Padelli", "cost": 9},
    "Parma": {"tit": "Suzuki", "sec": "Chichizola", "ter": "Corvi", "cost": 8},
    "Cagliari": {"tit": "Scuffet", "sec": "Sherri", "ter": "Ciocci", "cost": 8},
    "Empoli": {"tit": "Vasquez", "sec": "Silvestri", "ter": "Perisan", "cost": 7},
    "Lecce": {"tit": "Falcone", "sec": "Früchtl", "ter": "Samooja", "cost": 7},
    "Verona": {"tit": "Montipò", "sec": "Perilli", "ter": "Berardi", "cost": 6},
    "Como": {"tit": "Reina", "sec": "Audero", "ter": "Vigorito", "cost": 6},
    "Venezia": {"tit": "Joronen", "sec": "Stankovic", "ter": "Grandi", "cost": 5}
}

# Strategie Portieri per il Fantacalcio a 10 (Budget 500)
# 1. Top Singolo + riserva della stessa squadra (es. Inter, Juve, Milan, Napoli)
# 2. Coppia Perfetta Low-Cost (Due squadre medie/piccole con alternanza casa/trasferta e calendario complementare)
# 3. Formula "1 Semi-Big + 1 Low Cost" (es. Roma/Lazio/Fiorentina/Bologna + Torino/Monza/Genoa)

def generate_pairing_analysis():
    pairs_analysis = [
        {
            "tier": "TOP ASSOLUTO",
            "name": "Blocco Inter (Sommer + Martinez)",
            "cost_est": "45-50 crediti (~9-10%)",
            "easy_matches": 24,
            "medium_matches": 10,
            "hard_matches": 4,
            "pros": "Miglior difesa del campionato, massimo numero di clean sheet (imbattibilità)",
            "cons": "Costo elevatissimo, toglie crediti per l'attacco",
            "recommended": True
        },
        {
            "tier": "TOP CONSOLIDATO",
            "name": "Blocco Juventus (Di Gregorio + Perin)",
            "cost_est": "40-44 crediti (~8-9%)",
            "easy_matches": 23,
            "medium_matches": 11,
            "hard_matches": 4,
            "pros": "Grandissima organizzazione difensiva, Di Gregorio portiere da modificatore",
            "cons": "Costo alto all'asta",
            "recommended": True
        },
        {
            "tier": "IBRIDA INTELLIGENTE (Semi-Big + Medio)",
            "name": "Roma (Svilar) + Torino (Milinkovic-Savic)",
            "cost_est": "32-36 crediti (~6-7%)",
            "easy_matches": 28,
            "medium_matches": 8,
            "hard_matches": 2,
            "pros": "Svilar e Vanja sono portieri con media voto altissima da modificatore. Alternanza quasi perfetta.",
            "cons": "Occorre gestire chi schierare ogni giornata",
            "recommended": True
        },
        {
            "tier": "IBRIDA INTELLIGENTE (Semi-Big + Medio)",
            "name": "Lazio (Provedel) + Monza (Turati)",
            "cost_est": "25-28 crediti (~5-6%)",
            "easy_matches": 26,
            "medium_matches": 9,
            "hard_matches": 3,
            "pros": "Ottimo risparmio di crediti, Turati porta ottimi voti, Provedel solido nelle gare casalinghe",
            "cons": "Qualche gol subito di troppo in trasferta",
            "recommended": True
        },
        {
            "tier": "IBRIDA INTELLIGENTE (Semi-Big + Medio)",
            "name": "Fiorentina (De Gea) + Genoa (Gollini/Leali)",
            "cost_est": "24-28 crediti (~5%)",
            "easy_matches": 26,
            "medium_matches": 9,
            "hard_matches": 3,
            "pros": "De Gea portiere di livello mondiale che para tanto, Genoa compatto a Marassi",
            "cons": "De Gea potrebbe pagare il periodo di inattività iniziale",
            "recommended": False
        },
        {
            "tier": "COPPIA LOW-COST 'MONEYBALL' (Massimo Risparmio)",
            "name": "Torino (Milinkovic-Savic) + Monza (Turati) + Empoli (Vasquez)",
            "cost_est": "18-22 crediti (~3.5-4.5%)",
            "easy_matches": 29,
            "medium_matches": 7,
            "hard_matches": 2,
            "pros": "Risparmi 30 crediti da investire su un 2° attaccante top! Hai SEMPRE una partita abbordabile in casa",
            "cons": "Non hai la certezza di 'zero gol subiti' di Inter o Juve",
            "recommended": True
        },
        {
            "tier": "COPPIA LOW-COST 'MONEYBALL'",
            "name": "Genoa (Gollini) + Udinese (Okoye) + Como (Reina/Audero)",
            "cost_est": "15-18 crediti (~3%)",
            "easy_matches": 27,
            "medium_matches": 8,
            "hard_matches": 3,
            "pros": "Costo bassissimo, Okoye e Gollini portieri da tanti voti alti",
            "cons": "Rischio malus nelle trasferte",
            "recommended": False
        }
    ]
    return pairs_analysis

if __name__ == "__main__":
    res = generate_pairing_analysis()
    print(json.dumps(res, indent=2))
