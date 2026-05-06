from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from app.schemas import OBDSnapshot
from app.csv_writer import append_snapshot

app = FastAPI(
    title="OBD Data Logger",
    description="Receives OBD-II sensor snapshots and persists them to CSV.",
    version="1.0.0",
)


@app.post(
    "/obd/snapshot",
    status_code=status.HTTP_201_CREATED,
    summary="Save an OBD snapshot",
)
def save_snapshot(snapshot: OBDSnapshot) -> JSONResponse:
    try:
        rows = append_snapshot(snapshot)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write CSV: {exc}",
        )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"saved_records": rows, "timestamp": snapshot.timestamp.isoformat()},
    )


@app.get("/health", summary="Health check")
def health() -> dict:
    return {"status": "ok"}
