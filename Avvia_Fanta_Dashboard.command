#!/bin/bash
cd "$(dirname "$0")"
echo "=========================================="
echo " FANTA AI WAR ROOM 2026/2027"
echo " Avvio del server locale in corso..."
echo "=========================================="
python3 -m http.server 8080 &
SERVER_PID=$!
sleep 1
open "http://localhost:8080/dashboard/index.html" || true
echo "Dashboard aperta nel browser!"
echo "Chiudi questa finestra per spegnere il server."
wait $SERVER_PID
