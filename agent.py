"""KI-Agent für Schadensmeldungen.

Der Agent liest eine frei formulierte Schadensmeldung, fragt bei fehlenden
Angaben nach und legt den Schaden über die REST-API an (Tool Use).

Start:  python agent.py
"""
import json
import logging
import os
import sys
from datetime import date

import anthropic
import httpx

MODEL = "claude-sonnet-5-5"
API_BASE = os.environ.get("SCHADEN_API_URL", "http://127.0.0.1:8000")
MAX_SCHLEIFEN = 6  # Schutz gegen Endlosschleifen

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("agent")

TOOLS = [
    {
        "name": "schaden_anlegen",
        "description": (
            "Legt eine Schadensmeldung im System an. Erst aufrufen, wenn Datum, Ort, "
            "Fahrzeug und Beschreibung bekannt sind. Fehlt etwas, frage den Benutzer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "schadensdatum": {"type": "string", "description": "Datum im Format JJJJ-MM-TT"},
                "ort": {"type": "string", "description": "Ort des Schadens"},
                "fahrzeug": {"type": "string", "description": "Fahrzeug oder Kennzeichen"},
                "beschreibung": {"type": "string", "description": "Kurzbeschreibung des Schadens"},
                "schweregrad": {"type": "string", "enum": ["gering", "mittel", "hoch"]},
                "melder": {"type": "string", "description": "Name des Melders, falls genannt"},
            },
            "required": ["schadensdatum", "ort", "fahrzeug", "beschreibung"],
        },
    }
]


def system_prompt() -> str:
    return (
        "Du bist ein Assistent für Schadensmeldungen. Heute ist der "
        f"{date.today().isoformat()}. Rechne relative Angaben wie 'gestern' in ein "
        "konkretes Datum um. Erfinde keine Angaben: Wenn Datum, Ort, Fahrzeug oder "
        "Beschreibung fehlen, frage kurz nach. Antworte auf Deutsch und knapp."
    )


def tool_ausfuehren(name: str, args: dict) -> tuple[str, bool]:
    """Führt ein Tool aus. Gibt (Ergebnistext, ist_fehler) zurück."""
    if name != "schaden_anlegen":
        return f"Unbekanntes Tool: {name}", True
    try:
        antwort = httpx.post(f"{API_BASE}/schaeden", json=args, timeout=10)
        if antwort.status_code == 201:
            log.info("Schaden angelegt: %s", antwort.json().get("id"))
            return json.dumps(antwort.json(), ensure_ascii=False), False
        log.warning("API lehnte ab (%s): %s", antwort.status_code, antwort.text)
        return f"API-Fehler {antwort.status_code}: {antwort.text}", True
    except httpx.HTTPError as fehler:
        log.error("API nicht erreichbar: %s", fehler)
        return f"API nicht erreichbar: {fehler}", True


def agent_antwort(client: anthropic.Anthropic, nachrichten: list) -> str:
    """Lässt das Modell antworten und führt dabei angeforderte Tools aus."""
    for _ in range(MAX_SCHLEIFEN):
        antwort = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system_prompt(),
            tools=TOOLS,
            messages=nachrichten,
        )
        nachrichten.append({"role": "assistant", "content": antwort.content})

        if antwort.stop_reason != "tool_use":
            return "".join(b.text for b in antwort.content if b.type == "text")

        ergebnisse = []
        for block in antwort.content:
            if block.type == "tool_use":
                log.info("Tool-Aufruf: %s %s", block.name, block.input)
                text, fehler = tool_ausfuehren(block.name, block.input)
                ergebnisse.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": text, "is_error": fehler}
                )
        nachrichten.append({"role": "user", "content": ergebnisse})
    return "Abbruch: zu viele Tool-Schritte."


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Umgebungsvariable ANTHROPIC_API_KEY ist nicht gesetzt (siehe README).")
    client = anthropic.Anthropic()
    nachrichten: list = []
    print("Schadensmeldungs-Agent. Beschreibe den Schaden (leere Eingabe beendet).")
    while True:
        eingabe = input("\nDu: ").strip()
        if not eingabe:
            break
        nachrichten.append({"role": "user", "content": eingabe})
        try:
            print("\nAgent:", agent_antwort(client, nachrichten))
        except anthropic.APIError as fehler:
            log.error("Claude-API-Fehler: %s", fehler)
            print("\nAgent: Es gab ein Problem mit der KI-Schnittstelle, bitte erneut versuchen.")
            nachrichten.pop()  # fehlgeschlagene Eingabe verwerfen


if __name__ == "__main__":
    main()
