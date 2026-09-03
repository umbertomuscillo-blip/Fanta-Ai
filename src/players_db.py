"""
Database Statistico e Valutazione Giocatori Fantacalcio 2026/2027
Lega: 10 squadre | Budget: 500 crediti | Modificatore Difesa (+1 -> +6)
"""

import json

PLAYERS_DATABASE = {
    "P": [
        {"nome": "Sommer", "squadra": "Inter", "ruolo": "P", "tier": "1 Top", "prezzo_target": 48, "prezzo_max": 55, "mv": 6.30, "fm": 5.80, "note": "Miglior difesa della Serie A, record di clean sheet."},
        {"nome": "Di Gregorio", "squadra": "Juventus", "ruolo": "P", "tier": "1 Top", "prezzo_target": 42, "prezzo_max": 48, "mv": 6.40, "fm": 5.75, "note": "Altissima media voto da modificatore, difesa blindata da Motta."},
        {"nome": "Maignan", "squadra": "Milan", "ruolo": "P", "tier": "2 Semi-Top", "prezzo_target": 36, "prezzo_max": 42, "mv": 6.25, "fm": 5.40, "note": "Pararigori formidabile, ma il Milan concede qualcosa."},
        {"nome": "Meret", "squadra": "Napoli", "ruolo": "P", "tier": "2 Semi-Top", "prezzo_target": 32, "prezzo_max": 38, "mv": 6.15, "fm": 5.35, "note": "Conte cura molto la fase difensiva, pochi gol subiti attesi."},
        {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "tier": "2 Semi-Top", "prezzo_target": 26, "prezzo_max": 30, "mv": 6.35, "fm": 5.45, "note": "Portiere che fa miracoli e prende 6.5/7 fisso. Ottimo per il modificatore."},
        {"nome": "Carnesecchi", "squadra": "Atalanta", "ruolo": "P", "tier": "3 Medio-Alto", "prezzo_target": 24, "prezzo_max": 28, "mv": 6.20, "fm": 5.25, "note": "Squadra offensiva, può subire gol ma fa parate decisive."},
        {"nome": "Provedel", "squadra": "Lazio", "ruolo": "P", "tier": "3 Medio-Alto", "prezzo_target": 20, "prezzo_max": 24, "mv": 6.15, "fm": 5.15, "note": "Buon rendimento, affidabile a prezzo contenuto."},
        {"nome": "De Gea", "squadra": "Fiorentina", "ruolo": "P", "tier": "3 Medio-Alto", "prezzo_target": 18, "prezzo_max": 22, "mv": 6.30, "fm": 5.10, "note": "Classe mondiale, acquisto di prestigio."},
        {"nome": "Milinkovic-Savic", "squadra": "Torino", "ruolo": "P", "tier": "4 Low-Cost Gold", "prezzo_target": 15, "prezzo_max": 18, "mv": 6.25, "fm": 5.20, "note": "Portiere dal rendimento altissimo in casa, para i rigori!"},
        {"nome": "Turati", "squadra": "Monza", "ruolo": "P", "tier": "4 Low-Cost Gold", "prezzo_target": 10, "prezzo_max": 13, "mv": 6.20, "fm": 4.90, "note": "Titolare certo, tante parate, perfetto in coppia con un big."},
        {"nome": "Gollini", "squadra": "Genoa", "ruolo": "P", "tier": "4 Low-Cost Gold", "prezzo_target": 9, "prezzo_max": 12, "mv": 6.15, "fm": 4.85, "note": "Genoa in casa è un fortino."},
        {"nome": "Okoye", "squadra": "Udinese", "ruolo": "P", "tier": "5 Scommessa", "prezzo_target": 8, "prezzo_max": 10, "mv": 6.10, "fm": 4.80, "note": "Fisicità impressionante, buon rendimento."},
        {"nome": "Vasquez", "squadra": "Empoli", "ruolo": "P", "tier": "5 Scommessa", "prezzo_target": 7, "prezzo_max": 9, "mv": 6.20, "fm": 4.75, "note": "Ottimo inizio, parate continue."},
        {"nome": "Suzuki", "squadra": "Parma", "ruolo": "P", "tier": "5 Scommessa", "prezzo_target": 7, "prezzo_max": 9, "mv": 6.05, "fm": 4.60, "note": "Parma gioca a viso aperto."},
        {"nome": "Falcone", "squadra": "Lecce", "ruolo": "P", "tier": "5 Scommessa", "prezzo_target": 6, "prezzo_max": 8, "mv": 6.15, "fm": 4.60, "note": "Para tantissimo, prende voti alti ma subisce diversi gol."}
    ],
    "D": [
        # Difensori Top da Modificatore & Bonus
        {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "tier": "1 Fuoriclasse", "prezzo_target": 40, "prezzo_max": 48, "mv": 6.45, "fm": 7.20, "mod_rating": "TOP", "piazzati": "Corner, Punizioni", "note": "È un attaccante aggiunto. 5-7 gol e 6-8 assist."},
        {"nome": "Theo Hernandez", "squadra": "Milan", "ruolo": "D", "tier": "1 Fuoriclasse", "prezzo_target": 38, "prezzo_max": 46, "mv": 6.35, "fm": 7.05, "mod_rating": "TOP", "piazzati": "Rigori secondario", "note": "Treno sulla fascia, gol pesanti, qualche cartellino di troppo."},
        {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "tier": "1 Muro Modificatore", "prezzo_target": 32, "prezzo_max": 38, "mv": 6.55, "fm": 6.80, "mod_rating": "DIVINO", "piazzati": "Colpi di testa", "note": "Il miglior difensore puro della Serie A. Prende 6.5 e 7 costanti."},
        {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "tier": "2 Top Modificatore", "prezzo_target": 24, "prezzo_max": 30, "mv": 6.40, "fm": 6.60, "mod_rating": "SUPER", "piazzati": "Cross/Assist", "note": "Voti regali, assist frequenti nelle sovrapposizioni."},
        {"nome": "Bellanova", "squadra": "Atalanta", "ruolo": "D", "tier": "2 Bonus Machine", "prezzo_target": 22, "prezzo_max": 27, "mv": 6.30, "fm": 6.65, "mod_rating": "BUONO", "piazzati": "Cross", "note": "Con Gasperini gli esterni volano e producono caterve di bonus."},
        {"nome": "Buongiorno", "squadra": "Napoli", "ruolo": "D", "tier": "2 Muro Modificatore", "prezzo_target": 20, "prezzo_max": 25, "mv": 6.45, "fm": 6.60, "mod_rating": "SUPER", "piazzati": "Colpi di testa", "note": "Pilastro di Conte, perfetto per il modificatore."},
        {"nome": "Pavard", "squadra": "Inter", "ruolo": "D", "tier": "2 Muro Modificatore", "prezzo_target": 18, "prezzo_max": 22, "mv": 6.35, "fm": 6.45, "mod_rating": "SUPER", "note": "Titolare nell'Inter, voto sempre positivo."},
        {"nome": "Gatti", "squadra": "Juventus", "ruolo": "D", "tier": "2 Sorpresa Bonus", "prezzo_target": 15, "prezzo_max": 19, "mv": 6.30, "fm": 6.55, "mod_rating": "BUONO", "note": "Titolare fisso con Motta, pericoloso sui calci d'angolo (3-4 gol)."},
        {"nome": "Tavares", "squadra": "Lazio", "ruolo": "D", "tier": "2 Bug Listone", "prezzo_target": 14, "prezzo_max": 18, "mv": 6.35, "fm": 6.70, "mod_rating": "SUPER", "note": "Terzino di spinta devastante, sforna assist."},
        {"nome": "Dumfries / Darmian", "squadra": "Inter", "ruolo": "D", "tier": "3 Semi-Top", "prezzo_target": 14, "prezzo_max": 18, "mv": 6.20, "fm": 6.50, "mod_rating": "BUONO", "note": "Spinta e gol, gestione ballottaggio."},
        {"nome": "Gosens", "squadra": "Fiorentina", "ruolo": "D", "tier": "2 Bug Listone", "prezzo_target": 16, "prezzo_max": 22, "mv": 6.30, "fm": 6.75, "mod_rating": "SUPER", "note": "Esterno d'attacco puro nel 3-5-2 di Palladino. Macchina da gol."},
        {"nome": "Zappacosta / Ruggeri", "squadra": "Atalanta", "ruolo": "D", "tier": "3 Semi-Top", "prezzo_target": 12, "prezzo_max": 15, "mv": 6.25, "fm": 6.40, "mod_rating": "BUONO", "note": "Esterni atalantini sempre nel vivo del gioco."},
        {"nome": "Beukema", "squadra": "Bologna", "ruolo": "D", "tier": "3 Regolarista Mod", "prezzo_target": 10, "prezzo_max": 13, "mv": 6.30, "fm": 6.35, "mod_rating": "OTTIMO", "note": "Media voto altissima, pochi malus."},
        {"nome": "Coco", "squadra": "Torino", "ruolo": "D", "tier": "3 Low-Cost Top", "prezzo_target": 9, "prezzo_max": 12, "mv": 6.35, "fm": 6.50, "mod_rating": "OTTIMO", "note": "Impatto devastante a Torino, difensore goleador."},
        {"nome": "Vasquez / Vogliacco", "squadra": "Genoa", "ruolo": "D", "tier": "4 Low-Cost Mod", "prezzo_target": 5, "prezzo_max": 8, "mv": 6.20, "fm": 6.20, "mod_rating": "BUONO", "note": "Genoa molto solido dietro."},
        {"nome": "Luperto", "squadra": "Cagliari", "ruolo": "D", "tier": "4 Regolarista Low-Cost", "prezzo_target": 5, "prezzo_max": 7, "mv": 6.15, "fm": 6.15, "mod_rating": "BUONO", "note": "Capitano di Nicola, 38 presenze garantite."},
        {"nome": "Kolasinac", "squadra": "Atalanta", "ruolo": "D", "tier": "3 Braccetto da Mod", "prezzo_target": 8, "prezzo_max": 11, "mv": 6.30, "fm": 6.30, "mod_rating": "OTTIMO", "note": "Roccia difensiva da 6.5."},
        {"nome": "Delprato", "squadra": "Parma", "ruolo": "D", "tier": "4 Scommessa", "prezzo_target": 4, "prezzo_max": 6, "mv": 6.15, "fm": 6.25, "mod_rating": "DISCRETO", "note": "Capitano, calcia e si inserisce."},
        {"nome": "Dorgu", "squadra": "Lecce", "ruolo": "D", "tier": "3 Bug Listone", "prezzo_target": 8, "prezzo_max": 12, "mv": 6.20, "fm": 6.45, "mod_rating": "BUONO", "note": "Listato difensore ma gioca ala d'attacco nel 4-2-3-1!"}
    ],
    "C": [
        # Centrocampisti: Gol, Assist, Rigori
        {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "tier": "1 Fuoriclasse", "prezzo_target": 45, "prezzo_max": 55, "mv": 6.50, "fm": 7.60, "piazzati": "RIGORISTA 1°, Punizioni, Corner", "note": "Infallibile dal dischetto (10-12 gol a stagione). Vale come un 1° attaccante."},
        {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "tier": "1 Fuoriclasse", "prezzo_target": 40, "prezzo_max": 48, "mv": 6.40, "fm": 7.40, "piazzati": "RIGORISTA 1°, Capitano", "note": "Nuovo numero 10 e capitano, calcia i rigori e gioca nel tridente."},
        {"nome": "Koopmeiners", "squadra": "Juventus", "ruolo": "C", "tier": "1 Fuoriclasse", "prezzo_target": 42, "prezzo_max": 50, "mv": 6.45, "fm": 7.50, "piazzati": "Tiri piazzati, Rigori", "note": "Centrocampista totale da 10 gol e 5 assist con Thiago Motta."},
        {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "tier": "1 Fuoriclasse", "prezzo_target": 45, "prezzo_max": 52, "mv": 6.45, "fm": 7.55, "piazzati": "Rigori / Piazzati", "note": "Se listato C è il miglior colpo del fantacalcio: ala pura da 12 gol."},
        {"nome": "Barella", "squadra": "Inter", "ruolo": "C", "tier": "2 Top Regolarista", "prezzo_target": 22, "prezzo_max": 28, "mv": 6.45, "fm": 6.75, "note": "Voto 6.5 fisso garantito, 3-5 gol, pochi cartellini."},
        {"nome": "Mkhitaryan", "squadra": "Inter", "ruolo": "C", "tier": "2 Top Regolarista", "prezzo_target": 18, "prezzo_max": 23, "mv": 6.40, "fm": 6.65, "note": "Cervello dell'Inter, titolarità solida."},
        {"nome": "Man", "squadra": "Parma", "ruolo": "C", "tier": "2 Semi-Top Bonus", "prezzo_target": 20, "prezzo_max": 26, "mv": 6.40, "fm": 7.10, "piazzati": "RIGORISTA 1°, Punizioni", "note": "Ala d'attacco listato centrocampista. Rigorista del Parma, 8-10 gol potenziali."},
        {"nome": "Orsolini", "squadra": "Bologna", "ruolo": "C", "tier": "2 Semi-Top Bonus", "prezzo_target": 25, "prezzo_max": 32, "mv": 6.30, "fm": 7.25, "piazzati": "RIGORISTA 1°, Punizioni", "note": "Specialista assoluto dei rigori, 10 gol ogni anno."},
        {"nome": "Nico Paz", "squadra": "Como", "ruolo": "C", "tier": "3 Crack / Scommessa Top", "prezzo_target": 12, "prezzo_max": 18, "mv": 6.50, "fm": 7.00, "note": "Talento puro ex Real Madrid. Assist e conclusioni continue."},
        {"nome": "Frattesi", "squadra": "Inter", "ruolo": "C", "tier": "2 Spaccapartite", "prezzo_target": 18, "prezzo_max": 24, "mv": 6.30, "fm": 7.15, "note": "Anche quando entra al 70' segna. 6-8 gol da centrocampista."},
        {"nome": "Ederson", "squadra": "Atalanta", "ruolo": "C", "tier": "2 Regolarista & Bonus", "prezzo_target": 17, "prezzo_max": 22, "mv": 6.45, "fm": 6.80, "note": "Titolarissimo di Gasp, inserimenti letali."},
        {"nome": "Samardzic", "squadra": "Atalanta", "ruolo": "C", "tier": "3 Scommessa Bonus", "prezzo_target": 14, "prezzo_max": 19, "mv": 6.35, "fm": 6.85, "piazzati": "Tiri piazzati", "note": "Piede mancino fatato, trequartista."},
        {"nome": "Colpani", "squadra": "Fiorentina", "ruolo": "C", "tier": "3 Titolare Bonus", "prezzo_target": 15, "prezzo_max": 20, "mv": 6.25, "fm": 6.70, "note": "Pupillo di Palladino, trequartista titolare."},
        {"nome": "Pasalic", "squadra": "Atalanta", "ruolo": "C", "tier": "3 Titolare Bonus", "prezzo_target": 15, "prezzo_max": 19, "mv": 6.25, "fm": 6.85, "piazzati": "Rigori secondario", "note": "Tappa-buchi ideale, 6-7 gol garantiti ogni stagione."},
        {"nome": "Frendrup", "squadra": "Genoa", "ruolo": "C", "tier": "3 Muro Regolarista", "prezzo_target": 8, "prezzo_max": 11, "mv": 6.35, "fm": 6.35, "note": "Miglior recuperatore di palloni della Serie A, voto 6.5 garantito."},
        {"nome": "Gaetano", "squadra": "Cagliari", "ruolo": "C", "tier": "3 Titolare Piazzati", "prezzo_target": 10, "prezzo_max": 14, "mv": 6.30, "fm": 6.75, "piazzati": "RIGORISTA / Punizioni", "note": "Trequartista titolare, 5-7 gol."},
        {"nome": "Maldini", "squadra": "Monza", "ruolo": "C", "tier": "4 Low-Cost Crack", "prezzo_target": 8, "prezzo_max": 12, "mv": 6.35, "fm": 6.80, "note": "Qualità infinita, titolare e tiro micidiale."},
        {"nome": "Brescianini", "squadra": "Atalanta", "ruolo": "C", "tier": "4 Low-Cost Bonus", "prezzo_target": 7, "prezzo_max": 11, "mv": 6.25, "fm": 6.70, "note": "Inserimenti perfetti nel sistema Gasp."}
    ],
    "A": [
        # Attaccanti: I Re del Gol
        {"nome": "Lautaro Martinez", "squadra": "Inter", "ruolo": "A", "tier": "1 Top Assoluto", "prezzo_target": 170, "prezzo_max": 190, "mv": 6.60, "fm": 8.80, "piazzati": "RIGORISTA 2°, Capitano", "note": "Capocannoniere e trascinatore dell'Inter. 20-25 gol attesi."},
        {"nome": "Vlahovic", "squadra": "Juventus", "ruolo": "A", "tier": "1 Top Assoluto", "prezzo_target": 150, "prezzo_max": 170, "mv": 6.45, "fm": 8.30, "piazzati": "RIGORISTA 1°, Punizioni", "note": "Perno centrale del gioco di Motta, tira tutto."},
        {"nome": "Lukaku", "squadra": "Napoli", "ruolo": "A", "tier": "1 Top Assoluto", "prezzo_target": 145, "prezzo_max": 165, "mv": 6.50, "fm": 8.20, "piazzati": "RIGORISTA 1°", "note": "Con Conte ha sempre fatto stagioni mostruose da 20+ gol."},
        {"nome": "Thuram", "squadra": "Inter", "ruolo": "A", "tier": "2 Secondo Top", "prezzo_target": 95, "prezzo_max": 115, "mv": 6.50, "fm": 8.10, "note": "Crescita esponenziale, 15+ gol e tanti assist."},
        {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "tier": "2 Secondo Top", "prezzo_target": 90, "prezzo_max": 110, "mv": 6.45, "fm": 8.05, "piazzati": "RIGORISTA 1°", "note": "Nel sistema super offensivo di Gasperini è una macchina da gol (15-18 gol)."},
        {"nome": "Lookman", "squadra": "Atalanta", "ruolo": "A", "tier": "2 Secondo Top", "prezzo_target": 80, "prezzo_max": 95, "mv": 6.50, "fm": 7.90, "note": "Devastante nell'uno contro uno, gol e assist."},
        {"nome": "Dovbyk", "squadra": "Roma", "ruolo": "A", "tier": "2 Secondo Top", "prezzo_target": 85, "prezzo_max": 105, "mv": 6.35, "fm": 7.80, "piazzati": "RIGORISTA 1°/2°", "note": "Pichichi della Liga l'anno scorso con 24 gol. Forte fisicamente."},
        {"nome": "Kvaratskhelia", "squadra": "Napoli", "ruolo": "A", "tier": "2 Secondo Top", "prezzo_target": 85, "prezzo_max": 105, "mv": 6.55, "fm": 7.95, "note": "Fantasista indispensabile per Conte."},
        {"nome": "Morata", "squadra": "Milan", "ruolo": "A", "tier": "2 Secondo Top", "prezzo_target": 75, "prezzo_max": 90, "mv": 6.35, "fm": 7.60, "note": "Punta centrale titolare del Milan, 12-15 gol."},
        {"nome": "Leao", "squadra": "Milan", "ruolo": "A", "tier": "2 Secondo Top", "prezzo_target": 75, "prezzo_max": 90, "mv": 6.40, "fm": 7.70, "note": "Talento cristallino, ma voti a volte incostanti."},
        {"nome": "Dybala", "squadra": "Roma", "ruolo": "A", "tier": "2 Secondo Top (Se sano)", "prezzo_target": 65, "prezzo_max": 80, "mv": 6.60, "fm": 8.00, "piazzati": "RIGORISTA 1°, Punizioni", "note": "Qualità indiscutibile, rigori e punizioni, gestione fisica."},
        {"nome": "Castellanos", "squadra": "Lazio", "ruolo": "A", "tier": "3 Terzo Slot Titolare", "prezzo_target": 45, "prezzo_max": 55, "mv": 6.35, "fm": 7.30, "piazzati": "RIGORISTA 2°", "note": "Nuovo centravanti titolare della Lazio dopo l'addio di Immobile (12-14 gol)."},
        {"nome": "Zapata", "squadra": "Torino", "ruolo": "A", "tier": "3 Terzo Slot Titolare", "prezzo_target": 45, "prezzo_max": 55, "mv": 6.40, "fm": 7.35, "piazzati": "Capitano", "note": "Condottiero del Torino, fisicità dominante (12-15 gol)."},
        {"nome": "Castro", "squadra": "Bologna", "ruolo": "A", "tier": "3 Terzo Slot Titolare", "prezzo_target": 35, "prezzo_max": 45, "mv": 6.35, "fm": 7.20, "note": "Erede designato di Zirkzee, grinta e gol."},
        {"nome": "Lucca", "squadra": "Udinese", "ruolo": "A", "tier": "3 Terzo Slot Titolare", "prezzo_target": 30, "prezzo_max": 40, "mv": 6.25, "fm": 7.15, "piazzati": "Colpi di testa", "note": "Gigante d'area di rigore (10-12 gol)."},
        {"nome": "Pinamonti", "squadra": "Genoa", "ruolo": "A", "tier": "3 Terzo Slot Titolare", "prezzo_target": 25, "prezzo_max": 35, "mv": 6.20, "fm": 7.05, "piazzati": "RIGORISTA 1°", "note": "Rigorista e titolare inamovibile a Genova (10-12 gol)."},
        {"nome": "Krstovic", "squadra": "Lecce", "ruolo": "A", "tier": "4 Low-Cost Titolare", "prezzo_target": 18, "prezzo_max": 25, "mv": 6.15, "fm": 6.90, "piazzati": "RIGORISTA 1°", "note": "Tira tantissimo verso la porta ogni partita."},
        {"nome": "Dia", "squadra": "Lazio", "ruolo": "A", "tier": "3 Terzo Slot / Jolly", "prezzo_target": 22, "prezzo_max": 30, "mv": 6.30, "fm": 7.10, "note": "Centravanti e seconda punta, molto mobile."},
        {"nome": "Mosquera / Tengstedt", "squadra": "Verona", "ruolo": "A", "tier": "4 Low-Cost", "prezzo_target": 10, "prezzo_max": 15, "mv": 6.15, "fm": 6.80, "note": "Punte del Verona, ottimi 5°/6° slot."},
        {"nome": "Bonny", "squadra": "Parma", "ruolo": "A", "tier": "4 Low-Cost Crack", "prezzo_target": 12, "prezzo_max": 18, "mv": 6.30, "fm": 6.95, "piazzati": "Rigori secondario", "note": "Attaccante moderno, fisico e velocissimo."},
        {"nome": "Cutrone", "squadra": "Como", "ruolo": "A", "tier": "4 Low-Cost Titolare", "prezzo_target": 10, "prezzo_max": 15, "mv": 6.20, "fm": 6.85, "note": "Capitano e simbolo del Como."}
    ]
}

def export_json():
    with open("/Users/umbertomuscillo/Documents/Fantacalcio/data/players_db.json", "w", encoding="utf-8") as f:
        json.dump(PLAYERS_DATABASE, f, ensure_ascii=False, indent=2)
    print("Database salvato con successo!")

if __name__ == "__main__":
    export_json()
