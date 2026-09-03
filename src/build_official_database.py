"""
Parser Ufficiale Fantacalcio 2026/2027
Estrae tutti i 588 giocatori reali del Listone Ufficiale Fantacalcio.it
con Ruoli Classic, Ruoli Mantra, Squadra reale, QA, FVM Classic (scalato a 500 crediti),
Rigoristi, Tiratori, Bug di Listone e Indici Modificatore Difesa.
"""

import re
import json

HTML_PATH = '/Users/umbertomuscillo/.gemini/antigravity/brain/3dcb8ab2-7ba8-4aeb-a48d-4a56a9436e33/.system_generated/steps/47/content.md'
OUTPUT_JSON = '/Users/umbertomuscillo/Documents/Fantacalcio/data/players_db.json'

TEAM_NAMES = {
    'ATA': 'Atalanta', 'BOL': 'Bologna', 'CAG': 'Cagliari', 'COM': 'Como',
    'FIO': 'Fiorentina', 'FRO': 'Frosinone', 'GEN': 'Genoa', 'INT': 'Inter',
    'JUV': 'Juventus', 'LAZ': 'Lazio', 'LEC': 'Lecce', 'MIL': 'Milan',
    'MON': 'Monza', 'NAP': 'Napoli', 'PAR': 'Parma', 'ROM': 'Roma',
    'SAS': 'Sassuolo', 'TOR': 'Torino', 'UDI': 'Udinese', 'VEN': 'Venezia'
}

# Rigoristi e Tiratori noti 2026/2027
PENALTY_TAKERS = {
    'Calhanoglu': '1° Rigorista, Punizioni, Corner (Infallibile)',
    'Martinez L.': '2° Rigorista, Capitano',
    'Malen': '1° Rigorista / Perno Attacco Roma',
    'Hojlund': '1° Rigorista Napoli',
    'Ramos G.': '1° Rigorista Milan',
    'Pulisic': 'Rigorista Milan, Punizioni',
    'Zaccagni': '1° Rigorista Lazio, Capitano',
    'Orsolini': '1° Rigorista Bologna, Punizioni',
    'Man': '1° Rigorista Parma, Punizioni',
    'Retegui': '1° Rigorista Atalanta',
    'Pinamonti': '1° Rigorista Genoa',
    'Krstovic': '1° Rigorista Lecce',
    'Berardi': '1° Rigorista Sassuolo, Punizioni, Corner',
    'Laurientè': '2° Rigorista Sassuolo',
    'Zapata': '1° Rigorista / Capitano Torino',
    'Lucca': '1° Rigorista Udinese',
    'Cutrone': '1° Rigorista Como, Capitano',
    'Pohjanpalo': '1° Rigorista Venezia, Capitano',
    'Soulè': 'Punizioni, Corner, Rigorista secondario Roma',
    'Koopmeiners': 'Punizioni, Rigorista secondario Juventus',
    'Gudmundsson': '1° Rigorista Fiorentina, Punizioni'
}

# Modificatore Top Difensori
MOD_DEFENDERS = {
    'Dimarco': {'mod': 'TOP', 'note': 'Attaccante aggiunto, batte punizioni e corner'},
    'Theo Hernandez': {'mod': 'TOP', 'note': 'Treno di fascia, bonus costanti'},
    'Bremer': {'mod': 'DIVINO', 'note': 'Media voto 6.55+, muro invalicabile'},
    'Bastoni': {'mod': 'SUPER', 'note': 'Media voto eccellente, assist a ripetizione'},
    'Buongiorno': {'mod': 'SUPER', 'note': 'Pilastro difensivo con Conte'},
    'Gatti': {'mod': 'BUONO', 'note': 'Pericoloso sui corner (3-4 gol attesi)'},
    'Tavares': {'mod': 'SUPER', 'note': 'Macchina da assist sulla fascia'},
    'Gosens': {'mod': 'SUPER', 'note': 'Esterno offensivo nel 3-5-2 di Palladino'},
    'Bellanova': {'mod': 'BUONO', 'note': 'Corsa, cross e assist continui'},
    'Beukema': {'mod': 'OTTIMO', 'note': 'Regolarista assoluto da 6.5 fisso'},
    'Coco': {'mod': 'OTTIMO', 'note': 'Rendimento altissimo a Torino'},
    'Dorgu': {'mod': 'BUONO', 'note': 'BUG LISTONE: difensore che gioca attaccante!'},
    'Kolasinac': {'mod': 'OTTIMO', 'note': 'Roccia difensiva di Gasperini'}
}

def parse_database():
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        text = f.read()

    trs = re.findall(r'<tr[^>]*>(.*?)</tr>', text, re.DOTALL)
    players = []

    for tr in trs[1:]:
        m_role = re.search(r'<th class=\"player-role player-role-classic\">\s*<span class=\"role\" data-value=\"([padcPADCPADC])\"', tr)
        if not m_role:
            continue
        role = m_role.group(1).upper()

        m_mantra = re.findall(r'<span class=\"role role-mantra\" data-value=\"([^\"]+)\"', tr)
        mantra_roles = ";".join(m_mantra) if m_mantra else ""

        m_name = re.search(r'<span>([^<]+)</span>\s*</a>', tr)
        name = m_name.group(1).strip() if m_name else 'Unknown'

        m_team = re.search(r'<td class=\"player-team\" data-col-key=\"sq\">\s*([^<\s]+)', tr)
        team_code = m_team.group(1).strip() if m_team else 'Unknown'
        team_full = TEAM_NAMES.get(team_code, team_code)

        m_qa = re.search(r'<td class=\"player-classic-current-price\" data-col-key=\"c_qa\">\s*(\d+)', tr)
        qa = int(m_qa.group(1)) if m_qa else 1

        m_fvm = re.search(r'<td class=\"player-classic-fvm\" data-col-key=\"c_fvm\">\s*(\d+)', tr)
        fvm = int(m_fvm.group(1)) if m_fvm else 1

        # Budget 500 crediti: il prezzo target consigliato è FVM / 2 (dato che FVM è su 1000)
        target_500 = max(1, round(fvm / 2))
        max_bid_500 = max(1, round(target_500 * 1.25))

        # Determina Tier e Note
        tier = "Regolare"
        note = ""
        piazzati = ""
        mod_rating = ""

        # Controllo piazzati / rigori
        for k, v in PENALTY_TAKERS.items():
            if k.lower() in name.lower():
                piazzati = v
                break

        # Controllo modificatore
        for k, v in MOD_DEFENDERS.items():
            if k.lower() in name.lower():
                mod_rating = v['mod']
                if not note:
                    note = v['note']
                break

        if role == 'P':
            if target_500 >= 30:
                tier = "1 Top Portiere"
            elif target_500 >= 20:
                tier = "2 Semi-Top"
            elif target_500 >= 10:
                tier = "3 Titolare Medio"
            else:
                tier = "4 Low-Cost / Riserva"
        elif role == 'D':
            if target_500 >= 20:
                tier = "1 Top Difesa"
            elif target_500 >= 10:
                tier = "2 Semi-Top / Mod"
            elif target_500 >= 5:
                tier = "3 Titolare Low-Cost"
            else:
                tier = "4 Riserva a 1 cr"
        elif role == 'C':
            if target_500 >= 30:
                tier = "1 Top Centrocampo"
            elif target_500 >= 18:
                tier = "2 Semi-Top Bonus"
            elif target_500 >= 8:
                tier = "3 Titolare / Scommessa"
            else:
                tier = "4 Low-Cost a 1 cr"
        elif role == 'A':
            if target_500 >= 100:
                tier = "1 Top Assoluto (1° Slot)"
            elif target_500 >= 50:
                tier = "2 Secondo Slot di Lusso"
            elif target_500 >= 20:
                tier = "3 Terzo Slot Titolare"
            elif target_500 >= 8:
                tier = "4 Quarto/Quinto Slot"
            else:
                tier = "5 Scommessa / Riserva"

        # Note speciali
        if 'paz' in name.lower():
            tier = "Crack Assoluto ⭐"
            note = "Fenomeno del Como, titolare inamovibile, tiri e assist costanti."
        elif 'mctominay' in name.lower():
            tier = "Top Bonus Inserimento 🔥"
            note = "Conte lo fa giocare incursore d'area nel Napoli, potenziale da 8-10 gol."
        elif 'malen' in name.lower():
            tier = "1 Top Assoluto (1° Slot)"
            note = "Nuovo numero 9 della Roma, bomber titolare e rigorista."
        elif 'hojlund' in name.lower():
            tier = "1 Top Assoluto (1° Slot)"
            note = "Centravanti titolare del Napoli di Conte."
        elif 'ramos g.' in name.lower():
            tier = "1 Top Assoluto (1° Slot)"
            note = "Nuovo bomber del Milan, riferimento offensivo titolare."
        elif 'vicario' in name.lower():
            note = "Nuovo portiere titolare della Juventus, blindatissimo da Thiago Motta."
        elif 'martinez jo.' in name.lower():
            note = "Portiere titolare dell'Inter (scavalcato Sommer)."

        players.append({
            'nome': name,
            'squadra': team_full,
            'squadra_code': team_code,
            'ruolo': role,
            'ruolo_mantra': mantra_roles,
            'qa': qa,
            'fvm_1000': fvm,
            'prezzo_target': target_500,
            'prezzo_max': max_bid_500,
            'tier': tier,
            'piazzati': piazzati,
            'mod_rating': mod_rating,
            'note': note
        })

    # Ordina per FVM decrescente
    players.sort(key=lambda x: x['fvm_1000'], reverse=True)

    # Raggruppa per ruolo
    by_role = {'P': [], 'D': [], 'C': [], 'A': []}
    for p in players:
        by_role[p['ruolo']].append(p)

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(by_role, f, ensure_ascii=False, indent=2)

    print(f"Salvato con successo database con {len(players)} calciatori reali in {OUTPUT_JSON}!")
    return players, by_role

if __name__ == '__main__':
    parse_database()
