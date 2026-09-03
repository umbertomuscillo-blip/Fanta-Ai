# Original User Request

## 2026-09-02T14:29:18+02:00

# Teamwork Project Prompt — Draft

> Status: Ready for launch — awaiting user approval
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Un team completo (Full Team) composto da ricercatori, sviluppatori e revisori che lavorano in parallelo.

Costruire un programma automatizzato per il Fantacalcio 2026/2027 che, quando avviato manualmente, recupera, pulisce e salva statistiche, probabili formazioni e risultati aggiornati. Il programma fungerà da base dati locale (in formato JSON/CSV) per le future analisi dell'AI.

Working directory: ~/Documents/Fantacalcio
Integrity mode: benchmark

## Requirements

### R1. Pipeline di Aggiornamento Manuale
Il sistema deve fornire uno script principale (es. `update_fanta_data.py`) che l'utente può eseguire manualmente per avviare il processo di aggiornamento di tutti i dati.

### R2. Ricerca e Selezione Fonti Autonoma
Il team di agenti deve ricercare sul web e selezionare in autonomia le migliori fonti gratuite (siti web di fantacalcio, testate sportive o API) per estrarre statistiche dei calciatori, probabili formazioni e calendario/incroci. 

### R3. Estrazione e Strutturazione dei Dati
I dati estratti devono essere puliti e salvati localmente all'interno della cartella `data/` in formati facilmente leggibili dall'AI e dall'utente (es. JSON o CSV organizzati per categoria).

### R4. Validazione Stagione 2026/2027
Tutti i dati estratti devono essere strettamente pertinenti alla stagione di Serie A 2026/2027 (devono includere le neopromosse come Como, Parma e Venezia, ed escludere le retrocesse).

## Acceptance Criteria

### Programmatic Verification (Automated Tests)
- [ ] Esiste uno script di test automatico (es. `test_data_integrity.py`) che verifica l'esistenza dei file generati.
- [ ] Il test verifica programmaticamente che nei dati siano presenti le squadre della stagione 2026/2027 (es. Como, Parma) e non le vecchie retrocesse.
- [ ] L'esecuzione dello script di aggiornamento termina con codice di uscita 0 (senza errori) ed effettua l'aggiornamento dei file.

### Agent-as-Judge Verification
- [ ] Un agente revisore indipendente deve ispezionare i file JSON/CSV generati e confermare tramite una rubrica di valutazione che i dati siano logicamente coerenti per il Fantacalcio (es. ruoli corretti, presenza di voti/statistiche, formazioni realistiche).

## 2026-09-02T15:25:29+02:00

# Teamwork Project Prompt — Draft

> Status: Ready for launch — awaiting user approval
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Un team completo (Full Team) per gestire lo sviluppo parallelo di 3 funzionalità complesse.

Costruire una suite di strumenti avanzati per il Fantacalcio 2026/2027 integrata nell'ecosistema esistente, comprendente: un calcolatore live del prezzo massimo per l'asta, un algoritmo generatore della migliore formazione titolare e un modulo per il calcolo dell'Indice Moneyball (xG/xA).

Working directory: ~/Documents/Fantacalcio
Integrity mode: benchmark

## Requirements

### R1. Calcolatore Prezzo Massimo (Frontend)
Modificare la `dashboard/index.html` esistente aggiungendo un modulo o widget Javascript per il calcolo del "Prezzo Massimo". L'algoritmo JS deve suggerire il limite massimo di spesa per un calciatore considerando il budget residuo dell'utente, i crediti degli avversari e gli slot liberi rimanenti.

### R2. Algoritmo "Chi Schiero" (Backend Python)
Sviluppare uno script Python (es. `best_lineup.py`) che, data in input una rosa di calciatori dell'utente, incroci i dati con le formazioni probabili (`lineups.json` / `.csv`) e la griglia portieri per calcolare matematicamente il miglior 11 titolare (valutando anche i vantaggi del Modificatore Difesa).

### R3. Indice Moneyball (Backend Python)
Integrare nella pipeline dati esistente un sistema per il recupero di statistiche avanzate (Expected Goals - xG, Expected Assists - xA) e generare un "Moneyball Index" per ogni giocatore, salvandolo nei dataset JSON in modo da evidenziare i giocatori sottovalutati.

## Acceptance Criteria

### Programmatic Verification (Automated Tests)
- [ ] Il test suite (`test_lineup_logic.py`) verifica che l'algoritmo generi moduli validi (es. 4-3-3, 3-4-3), non schieri giocatori dati come "Infortunati/Squalificati" e applichi correttamente il calcolo del Modificatore.
- [ ] Il test suite verifica che il dataset JSON dei giocatori mantenga la sua struttura originale e contenga le nuove chiavi per xG/xA o Moneyball Index senza corrompersi.

### Agent-as-Judge Verification
- [ ] Un agente revisore indipendente ispeziona il codice HTML della dashboard confermando la corretta integrazione del calcolatore budget.
- [ ] L'agente revisore esegue lo script `best_lineup.py` su una rosa fittizia e compila una rubrica valutando se le scelte tattiche dell'AI (titolari vs panchina) seguono una logica calcistica sensata e ottimale per il Fantacalcio.

