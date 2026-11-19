# Schadensmeldungs-Agent (Python, Claude API, FastAPI)

Ein KI-Agent, der frei formulierte Schadensmeldungen versteht, bei fehlenden Angaben nachfragt
und den Schaden per REST-API in einem Backend anlegt. Das Projekt zeigt, wie ein LLM-Agent über
Tool Use in ein bestehendes System integriert wird. Es verwendet nur erfundene Beispieldaten.

## Aufbau

- `api_server.py`: Test-Backend mit FastAPI (POST/GET `/schaeden`), Validierung mit Pydantic
- `agent.py`: Agent mit Tool Use, Fehlerbehandlung, Logging und Schutz vor Endlosschleifen

## Ablauf

1. Benutzer beschreibt den Schaden in einem Satz.
2. Das Modell prüft, ob Datum, Ort, Fahrzeug und Beschreibung vorhanden sind, und fragt sonst nach.
3. Es ruft das Tool `schaden_anlegen` auf, der Agent leitet den Aufruf per HTTP an die API weiter.
4. API-Fehler (z. B. Datum in der Zukunft) gehen als `is_error` zurück ans Modell, das sie dem Benutzer erklärt.

## Start (Windows, PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Terminal 1: Backend
uvicorn api_server:app --port 8000

# Terminal 2: Agent (neues Terminal, venv wieder aktivieren)
$env:ANTHROPIC_API_KEY = "dein-key"
python agent.py
```

Die API-Dokumentation steht unter http://127.0.0.1:8000/docs, die angelegten Schäden unter
http://127.0.0.1:8000/schaeden.

## Beispiel

```
Du: Gestern Abend wurde mein Firmenwagen W-99XY auf dem Parkplatz in Wien am Seitenspiegel beschädigt.
Agent: Schaden angelegt (ID 1) ...
```

## Ideen zum Ausbauen

- Persistenz mit SQL Server statt Speicher
- Fotos mit der Vision-Funktion auswerten
- Authentifizierung der API mit OAuth 2.0
- Automatisierte Tests mit gemocktem Modell
