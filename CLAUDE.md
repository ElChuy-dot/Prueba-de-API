# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python project for reading vehicle diagnostic data via OBD-II. Uses the `python-obd` library to connect to an ELM327 adapter and query vehicle sensors continuously.

## Setup

Uses [UV](https://docs.astral.sh/uv/) for dependency and environment management.

```bash
uv sync          # instala dependencias y crea .venv
uv sync --group dev  # incluye dependencias de desarrollo (pytest, httpx)
```

## Running

```bash
# Terminal 1 — API
uv run uvicorn app.main:app --reload

# Terminal 2 — OBD reader
uv run python obd/Cicloif.py
```

The OBD script connects to a serial port (currently hardcoded to `COM9` — update for your adapter: `/dev/ttyUSB0` on Linux/Mac). It polls all supported commands every second and POSTs each snapshot to the API at `http://127.0.0.1:8000/obd/snapshot`.

## Architecture

- `app/main.py` — FastAPI app with `POST /obd/snapshot` and `GET /health`.
- `app/schemas.py` — Pydantic models: `OBDRecord`, `OBDSnapshot`.
- `app/csv_writer.py` — writes snapshots to `data/obd_log.csv`.
- `obd/Cicloif.py` — reads OBD-II data and sends it to the API each cycle.
- `data/` — CSV storage directory (auto-created on first write).
- `pyproject.toml` — project metadata and pinned dependencies (managed by UV).
- `uv.lock` — exact lockfile, commit this to guarantee reproducible installs.

## OBD Connection States

The script handles three connection states from `python-obd`:
- `CAR_CONNECTED` — full communication, queries all supported commands
- `OBD_CONNECTED` — adapter found but car not responding (engine may be off)
- `ELM_CONNECTED` — ELM327 chip responds but no OBD communication
