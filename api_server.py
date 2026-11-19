"""Kleine Test-API für Schadensmeldungen (nur Beispieldaten, keine echten Firmendaten).

Start:  uvicorn api_server:app --port 8000
Doku:   http://127.0.0.1:8000/docs
"""
import logging
from datetime import date
from itertools import count
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("api")

app = FastAPI(title="Schadensmeldungen Test-API", version="0.1.0")


class SchadenNeu(BaseModel):
    schadensdatum: date = Field(description="Datum des Schadens (JJJJ-MM-TT)")
    ort: str = Field(min_length=2, description="Ort des Schadens")
    fahrzeug: str = Field(min_length=2, description="Fahrzeug oder Kennzeichen")
    beschreibung: str = Field(min_length=5, description="Kurzbeschreibung des Schadens")
    schweregrad: Literal["gering", "mittel", "hoch"] = "gering"
    melder: str | None = None


class Schaden(SchadenNeu):
    id: int


_ids = count(1)
_daten: dict[int, Schaden] = {}


@app.post("/schaeden", response_model=Schaden, status_code=201)
def schaden_anlegen(neu: SchadenNeu) -> Schaden:
    if neu.schadensdatum > date.today():
        raise HTTPException(status_code=422, detail="Schadensdatum liegt in der Zukunft.")
    schaden = Schaden(id=next(_ids), **neu.model_dump())
    _daten[schaden.id] = schaden
    log.info("Schaden %s angelegt: %s, %s", schaden.id, schaden.fahrzeug, schaden.ort)
    return schaden


@app.get("/schaeden", response_model=list[Schaden])
def schaeden_liste() -> list[Schaden]:
    return list(_daten.values())


@app.get("/schaeden/{schaden_id}", response_model=Schaden)
def schaden_lesen(schaden_id: int) -> Schaden:
    if schaden_id not in _daten:
        raise HTTPException(status_code=404, detail="Schaden nicht gefunden.")
    return _daten[schaden_id]
