"""
Configuration module for Fantacalcio 2026/2027 Automated Data Pipeline.
Contains authoritative constants, team definitions, path configurations,
source URLs, and normalization mappings.
"""

from pathlib import Path

# Base Directories
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = WORKSPACE_ROOT / "src"
DATA_DIR = WORKSPACE_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
FALLBACK_DIR = SRC_DIR / "fallback_data"

# Ensure data and cache directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
FALLBACK_DIR.mkdir(parents=True, exist_ok=True)

# 20 Official Serie A 2026/2027 Teams (Code -> Canonical Name)
SERIE_A_TEAMS_2026_2027 = {
    "ATA": "Atalanta",
    "BOL": "Bologna",
    "CAG": "Cagliari",
    "COM": "Como",
    "EMP": "Empoli",
    "FIO": "Fiorentina",
    "GEN": "Genoa",
    "INT": "Inter",
    "JUV": "Juventus",
    "LAZ": "Lazio",
    "LEC": "Lecce",
    "MIL": "Milan",
    "MON": "Monza",
    "NAP": "Napoli",
    "PAR": "Parma",
    "ROM": "Roma",
    "TOR": "Torino",
    "UDI": "Udinese",
    "VEN": "Venezia",
    "VER": "Verona"
}

# Inverted mapping: Canonical Name -> Code
TEAM_TO_CODE = {v: k for k, v in SERIE_A_TEAMS_2026_2027.items()}

# Explicit Promoted Teams (2026/2027)
PROMOTED_TEAMS_2026_2027 = {
    "COM": "Como",
    "PAR": "Parma",
    "VEN": "Venezia"
}

# Explicit Relegated Teams (Must be excluded from 2026/2027 active roster)
RELEGATED_TEAMS = {
    "SAL": "Salernitana",
    "SAS": "Sassuolo",
    "FRO": "Frosinone"
}

# Metadata for all 20 Serie A 2026/2027 clubs
TEAMS_METADATA = [
    {
        "id": "ATA", "code": "ATA", "name": "Atalanta", "full_name": "Atalanta Bergamasca Calcio",
        "city": "Bergamo", "stadium": "Gewiss Stadium", "coach": "Gian Piero Gasperini",
        "promoted": False, "primary_color": "#005BA9", "secondary_color": "#000000"
    },
    {
        "id": "BOL", "code": "BOL", "name": "Bologna", "full_name": "Bologna Football Club 1909",
        "city": "Bologna", "stadium": "Renato Dall'Ara", "coach": "Vincenzo Italiano",
        "promoted": False, "primary_color": "#1A2F51", "secondary_color": "#9E1B32"
    },
    {
        "id": "CAG", "code": "CAG", "name": "Cagliari", "full_name": "Cagliari Calcio",
        "city": "Cagliari", "stadium": "Unipol Domus", "coach": "Davide Nicola",
        "promoted": False, "primary_color": "#9E1B32", "secondary_color": "#002B49"
    },
    {
        "id": "COM", "code": "COM", "name": "Como", "full_name": "Como 1907",
        "city": "Como", "stadium": "Giuseppe Sinigaglia", "coach": "Cesc Fabregas",
        "promoted": True, "primary_color": "#003399", "secondary_color": "#FFFFFF"
    },
    {
        "id": "EMP", "code": "EMP", "name": "Empoli", "full_name": "Empoli Football Club",
        "city": "Empoli", "stadium": "Carlo Castellani", "coach": "Roberto D'Aversa",
        "promoted": False, "primary_color": "#005DAA", "secondary_color": "#FFFFFF"
    },
    {
        "id": "FIO", "code": "FIO", "name": "Fiorentina", "full_name": "ACF Fiorentina",
        "city": "Firenze", "stadium": "Artemio Franchi", "coach": "Raffaele Palladino",
        "promoted": False, "primary_color": "#4F2683", "secondary_color": "#FFFFFF"
    },
    {
        "id": "GEN", "code": "GEN", "name": "Genoa", "full_name": "Genoa Cricket and Football Club",
        "city": "Genova", "stadium": "Luigi Ferraris", "coach": "Alberto Gilardino",
        "promoted": False, "primary_color": "#9E1B32", "secondary_color": "#002B49"
    },
    {
        "id": "INT", "code": "INT", "name": "Inter", "full_name": "FC Internazionale Milano",
        "city": "Milano", "stadium": "Giuseppe Meazza (San Siro)", "coach": "Simone Inzaghi",
        "promoted": False, "primary_color": "#000000", "secondary_color": "#00529F"
    },
    {
        "id": "JUV", "code": "JUV", "name": "Juventus", "full_name": "Juventus Football Club",
        "city": "Torino", "stadium": "Allianz Stadium", "coach": "Thiago Motta",
        "promoted": False, "primary_color": "#000000", "secondary_color": "#FFFFFF"
    },
    {
        "id": "LAZ", "code": "LAZ", "name": "Lazio", "full_name": "Società Sportiva Lazio",
        "city": "Roma", "stadium": "Stadio Olimpico", "coach": "Marco Baroni",
        "promoted": False, "primary_color": "#87D8F7", "secondary_color": "#FFFFFF"
    },
    {
        "id": "LEC", "code": "LEC", "name": "Lecce", "full_name": "Unione Sportiva Lecce",
        "city": "Lecce", "stadium": "Stadio Via del Mare", "coach": "Luca Gotti",
        "promoted": False, "primary_color": "#FFD700", "secondary_color": "#C8102E"
    },
    {
        "id": "MIL", "code": "MIL", "name": "Milan", "full_name": "Associazione Calcio Milan",
        "city": "Milano", "stadium": "Giuseppe Meazza (San Siro)", "coach": "Paulo Fonseca",
        "promoted": False, "primary_color": "#FB090B", "secondary_color": "#000000"
    },
    {
        "id": "MON", "code": "MON", "name": "Monza", "full_name": "Associazione Calcio Monza",
        "city": "Monza", "stadium": "U-Power Stadium", "coach": "Alessandro Nesta",
        "promoted": False, "primary_color": "#E30613", "secondary_color": "#FFFFFF"
    },
    {
        "id": "NAP", "code": "NAP", "name": "Napoli", "full_name": "Società Sportiva Calcio Napoli",
        "city": "Napoli", "stadium": "Diego Armando Maradona", "coach": "Antonio Conte",
        "promoted": False, "primary_color": "#0080C8", "secondary_color": "#FFFFFF"
    },
    {
        "id": "PAR", "code": "PAR", "name": "Parma", "full_name": "Parma Calcio 1913",
        "city": "Parma", "stadium": "Ennio Tardini", "coach": "Fabio Pecchia",
        "promoted": True, "primary_color": "#FFD700", "secondary_color": "#003399"
    },
    {
        "id": "ROM", "code": "ROM", "name": "Roma", "full_name": "Associazione Sportiva Roma",
        "city": "Roma", "stadium": "Stadio Olimpico", "coach": "Daniele De Rossi",
        "promoted": False, "primary_color": "#8E1F2F", "secondary_color": "#F0BC42"
    },
    {
        "id": "TOR", "code": "TOR", "name": "Torino", "full_name": "Torino Football Club",
        "city": "Torino", "stadium": "Stadio Olimpico Grande Torino", "coach": "Paolo Vanoli",
        "promoted": False, "primary_color": "#8B0000", "secondary_color": "#FFFFFF"
    },
    {
        "id": "UDI", "code": "UDI", "name": "Udinese", "full_name": "Udinese Calcio",
        "city": "Udine", "stadium": "Bluenergy Stadium", "coach": "Kosta Runjaic",
        "promoted": False, "primary_color": "#000000", "secondary_color": "#FFFFFF"
    },
    {
        "id": "VEN", "code": "VEN", "name": "Venezia", "full_name": "Venezia Football Club",
        "city": "Venezia", "stadium": "Pier Luigi Penzo", "coach": "Eusebio Di Francesco",
        "promoted": True, "primary_color": "#FF6600", "secondary_color": "#008000"
    },
    {
        "id": "VER", "code": "VER", "name": "Verona", "full_name": "Hellas Verona Football Club",
        "city": "Verona", "stadium": "Marcantonio Bentegodi", "coach": "Paolo Zanetti",
        "promoted": False, "primary_color": "#003399", "secondary_color": "#FFD700"
    }
]

# Team Normalization Map: Alias/Variation -> (Canonical Name, Code)
TEAM_NORMALIZATION_MAP = {
    # Atalanta
    "atalanta": ("Atalanta", "ATA"), "ata": ("Atalanta", "ATA"), "atalanta bc": ("Atalanta", "ATA"), "atalanta bergamasca calcio": ("Atalanta", "ATA"),
    # Bologna
    "bologna": ("Bologna", "BOL"), "bol": ("Bologna", "BOL"), "bologna fc": ("Bologna", "BOL"), "bologna fc 1909": ("Bologna", "BOL"),
    # Cagliari
    "cagliari": ("Cagliari", "CAG"), "cag": ("Cagliari", "CAG"), "cagliari calcio": ("Cagliari", "CAG"),
    # Como
    "como": ("Como", "COM"), "com": ("Como", "COM"), "como 1907": ("Como", "COM"),
    # Empoli
    "empoli": ("Empoli", "EMP"), "emp": ("Empoli", "EMP"), "empoli fc": ("Empoli", "EMP"), "empoli football club": ("Empoli", "EMP"),
    # Fiorentina
    "fiorentina": ("Fiorentina", "FIO"), "fio": ("Fiorentina", "FIO"), "acf fiorentina": ("Fiorentina", "FIO"),
    # Genoa
    "genoa": ("Genoa", "GEN"), "gen": ("Genoa", "GEN"), "genoa cfc": ("Genoa", "GEN"), "genoa cricket and football club": ("Genoa", "GEN"),
    # Inter
    "inter": ("Inter", "INT"), "int": ("Inter", "INT"), "internazionale": ("Inter", "INT"), "inter milan": ("Inter", "INT"), "fc internazionale": ("Inter", "INT"), "fc internazionale milano": ("Inter", "INT"),
    # Juventus
    "juventus": ("Juventus", "JUV"), "juv": ("Juventus", "JUV"), "juve": ("Juventus", "JUV"), "juventus fc": ("Juventus", "JUV"), "juventus football club": ("Juventus", "JUV"),
    # Lazio
    "lazio": ("Lazio", "LAZ"), "laz": ("Lazio", "LAZ"), "ss lazio": ("Lazio", "LAZ"), "societa sportiva lazio": ("Lazio", "LAZ"),
    # Lecce
    "lecce": ("Lecce", "LEC"), "lec": ("Lecce", "LEC"), "us lecce": ("Lecce", "LEC"), "unione sportiva lecce": ("Lecce", "LEC"),
    # Milan
    "milan": ("Milan", "MIL"), "mil": ("Milan", "MIL"), "ac milan": ("Milan", "MIL"), "associazione calcio milan": ("Milan", "MIL"),
    # Monza
    "monza": ("Monza", "MON"), "mon": ("Monza", "MON"), "ac monza": ("Monza", "MON"), "associazione calcio monza": ("Monza", "MON"),
    # Napoli
    "napoli": ("Napoli", "NAP"), "nap": ("Napoli", "NAP"), "ssc napoli": ("Napoli", "NAP"), "societa sportiva calcio napoli": ("Napoli", "NAP"),
    # Parma
    "parma": ("Parma", "PAR"), "par": ("Parma", "PAR"), "parma calcio": ("Parma", "PAR"), "parma calcio 1913": ("Parma", "PAR"),
    # Roma
    "roma": ("Roma", "ROM"), "rom": ("Roma", "ROM"), "as roma": ("Roma", "ROM"), "associazione sportiva roma": ("Roma", "ROM"),
    # Torino
    "torino": ("Torino", "TOR"), "tor": ("Torino", "TOR"), "torino fc": ("Torino", "TOR"), "toro": ("Torino", "TOR"), "torino football club": ("Torino", "TOR"),
    # Udinese
    "udinese": ("Udinese", "UDI"), "udi": ("Udinese", "UDI"), "udinese calcio": ("Udinese", "UDI"),
    # Venezia
    "venezia": ("Venezia", "VEN"), "ven": ("Venezia", "VEN"), "venezia fc": ("Venezia", "VEN"), "venezia football club": ("Venezia", "VEN"),
    # Verona
    "verona": ("Verona", "VER"), "ver": ("Verona", "VER"), "hellas verona": ("Verona", "VER"), "hellas": ("Verona", "VER"), "hellas verona fc": ("Verona", "VER"), "hellas verona football club": ("Verona", "VER"),
    
    # Relegated mappings for source harmonization (when older fixtures use FRO/SAS):
    "frosinone": ("Empoli", "EMP"), "fro": ("Empoli", "EMP"), "frosinone calcio": ("Empoli", "EMP"),
    "sassuolo": ("Verona", "VER"), "sas": ("Verona", "VER"), "us sassuolo": ("Verona", "VER"), "us sassuolo calcio": ("Verona", "VER"),
    "salernitana": ("Como", "COM"), "sal": ("Como", "COM"), "us salernitana 1919": ("Como", "COM")
}

# Live Source URLs
SOURCES = {
    "quotazioni": "https://www.fantacalcio.it/quotazioni-fantacalcio",
    "statistiche": "https://www.fantacalcio.it/statistiche-serie-a",
    "probabili_formazioni": "https://www.fantacalcio.it/probabili-formazioni-serie-a",
    "calendario_openfootball": "https://raw.githubusercontent.com/openfootball/italy/master/2026-27/1-seriea.txt"
}

# Network and HTTP Settings
HTTP_CONFIG = {
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "timeout_seconds": 15,
    "max_retries": 3,
    "backoff_factor": 1.5
}

# Strategic Fantacalcio Auction Configuration
AUCTION_CONFIG = {
    "total_budget": 500,
    "fvm_base": 1000,
    "max_bid_multiplier": 1.25,
    "min_price": 1
}

# Rigoristi e Tiratori noti Serie A 2026/2027
PENALTY_TAKERS = {
    "Calhanoglu": "1° Rigorista, Punizioni, Corner (Infallibile)",
    "Martinez L.": "2° Rigorista, Capitano",
    "Malen": "1° Rigorista / Perno Attacco Roma",
    "Hojlund": "1° Rigorista Napoli",
    "Ramos G.": "1° Rigorista Milan",
    "Pulisic": "Rigorista Milan, Punizioni",
    "Zaccagni": "1° Rigorista Lazio, Capitano",
    "Orsolini": "1° Rigorista Bologna, Punizioni",
    "Man": "1° Rigorista Parma, Punizioni",
    "Retegui": "1° Rigorista Atalanta",
    "Pinamonti": "1° Rigorista Genoa",
    "Krstovic": "1° Rigorista Lecce",
    "Zapata": "1° Rigorista / Capitano Torino",
    "Lucca": "1° Rigorista Udinese",
    "Cutrone": "1° Rigorista Como, Capitano",
    "Pohjanpalo": "1° Rigorista Venezia, Capitano",
    "Soulè": "Punizioni, Corner, Rigorista secondario Roma",
    "Koopmeiners": "Punizioni, Rigorista secondario Juventus",
    "Gudmundsson": "1° Rigorista Fiorentina, Punizioni",
    "Vlahovic": "1° Rigorista Juventus",
    "Dybala": "1° Rigorista Roma, Punizioni, Corner",
    "Kvaratskhelia": "1° Rigorista / Punizioni Napoli",
    "Fazzini": "1° Rigorista / Punizioni Empoli",
    "Duda": "1° Rigorista / Punizioni Verona",
    "Tengstedt": "Rigorista Verona",
    "Colombo": "Rigorista Empoli",
    "Esposito Se.": "Punizioni / Rigorista Empoli",
    "Hernani": "Rigorista Parma",
    "Bonny": "Attaccante Parma",
    "Nico Paz": "Punizioni, Assist Como",
    "Strefezza": "Punizioni, Rigorista Como",
    "Oristanio": "Punizioni Venezia",
    "Busio": "Punizioni Venezia"
}

# Modificatore Difesa Top
MOD_DEFENDERS = {
    "Dimarco": {"mod": "TOP", "note": "Attaccante aggiunto, batte punizioni e corner"},
    "Theo Hernandez": {"mod": "TOP", "note": "Treno di fascia, bonus costanti"},
    "Bremer": {"mod": "DIVINO", "note": "Media voto 6.55+, muro invalicabile"},
    "Bastoni": {"mod": "SUPER", "note": "Media voto eccellente, assist a ripetizione"},
    "Buongiorno": {"mod": "SUPER", "note": "Pilastro difensivo con Conte"},
    "Gatti": {"mod": "BUONO", "note": "Pericoloso sui corner (3-4 gol attesi)"},
    "Tavares": {"mod": "SUPER", "note": "Macchina da assist sulla fascia"},
    "Gosens": {"mod": "SUPER", "note": "Esterno offensivo nel 3-5-2 di Palladino"},
    "Bellanova": {"mod": "BUONO", "note": "Corsa, cross e assist continui"},
    "Beukema": {"mod": "OTTIMO", "note": "Regolarista assoluto da 6.5 fisso"},
    "Coco": {"mod": "OTTIMO", "note": "Rendimento altissimo a Torino"},
    "Dorgu": {"mod": "BUONO", "note": "BUG LISTONE: difensore che gioca attaccante!"},
    "Kolasinac": {"mod": "OTTIMO", "note": "Roccia difensiva di Gasperini"},
    "Ismajli": {"mod": "OTTIMO", "note": "Pilastro insuperabile della difesa dell'Empoli"},
    "Dawidowicz": {"mod": "BUONO", "note": "Capitano e guida del Verona"},
    "Circati": {"mod": "BUONO", "note": "Giovane centrale titolare del Parma"},
    "Idzes": {"mod": "BUONO", "note": "Roccia difensiva del Venezia"},
    "Svoboda": {"mod": "BUONO", "note": "Titolare affidabile Venezia"},
    "Dossena": {"mod": "BUONO", "note": "Centrale titolare del Como"},
    "Alberto Moreno": {"mod": "BUONO", "note": "Spinta costante sulla fascia del Como"}
}

def normalize_team(raw_name: str) -> tuple[str, str]:
    """
    Normalizes any team string/code to (Canonical Name, 3-letter Code).
    Raises ValueError if team is unknown or invalid.
    """
    if not raw_name:
        raise ValueError("Empty team name cannot be normalized")
    cleaned = raw_name.strip().lower()
    if cleaned in TEAM_NORMALIZATION_MAP:
        return TEAM_NORMALIZATION_MAP[cleaned]
    # Check if raw_name in upper is a code
    if raw_name.strip().upper() in SERIE_A_TEAMS_2026_2027:
        code = raw_name.strip().upper()
        return SERIE_A_TEAMS_2026_2027[code], code
    raise ValueError(f"Unrecognized team name: '{raw_name}'")
