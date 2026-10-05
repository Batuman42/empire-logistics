# Empire Logistics OS

Flask-MVP für Last-Mile-Disposition: Sendungen anlegen, Fahrzeugwahl per „KI-Dispatch“ (lernt aus `mission_log`), Live-Karte mit Leaflet und CSV-Export.

## Lokal starten

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
FLASK_DEBUG=1 python routentool_mvp.py
```

Dann http://localhost:5000 öffnen.

## Routen

| Route | Methode | Zweck |
|---|---|---|
| `/` | GET | Weiterleitung auf `/dashboard` |
| `/dashboard` | GET | Karte, Kennzahlen, Live-Radar |
| `/add_manual` | POST | Sendung manuell anlegen |
| `/ai_auto_dispatch` | POST | KI wählt Fahrzeug und startet Mission |
| `/export` | GET | Alle Sendungen als CSV (`;`-getrennt) |

## Konfiguration

| Variable | Standard | Bedeutung |
|---|---|---|
| `DATABASE_PATH` | `lastmile.db` | Pfad zur SQLite-Datei |
| `FLASK_DEBUG` | `0` | Nur lokal auf `1` setzen |

## Deploy

`Procfile` startet die App mit gunicorn (Render, Railway, Heroku). SQLite liegt dort auf flüchtigem Speicher: Für echten Betrieb ein persistentes Volume oder Postgres nutzen.

## Tests

```bash
pytest -q
```
