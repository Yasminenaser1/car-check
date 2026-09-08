import sqlite3
from typing import Literal, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from scoring import score_all
from recommend import recommend, explain, BODY_LABELS

app = FastAPI(title="Car Check")

# Scores are computed once at startup — the data only changes when you re-ingest
_conn = sqlite3.connect("cars.db", check_same_thread=False)
CARS = score_all(_conn)


class Request(BaseModel):
    kids: int = Field(0, ge=0, le=6)
    priority: Literal["balanced", "reliability", "safety"] = "balanced"
    min_year: Optional[int] = Field(None, ge=2016, le=2026)


@app.get("/meta")
def meta():
    years = sorted({c["year"] for c in CARS})
    return {
        "car_count": len(CARS),
        "model_count": len({(c["make"], c["model"]) for c in CARS}),
        "years": years,
        "body_types": sorted({BODY_LABELS[c["body"]] for c in CARS}),
        "source": "NHTSA (api.nhtsa.gov): recalls, complaints, NCAP safety ratings",
    }


@app.post("/recommend")
def get_recommendations(req: Request):
    results, notes = recommend(
        CARS, kids=req.kids, priority=req.priority,
        min_year=req.min_year, top_n=6)

    return {
        "notes": notes,
        "results": [{
            "year": c["year"],
            "make": c["make"].title(),
            "model": c["model"].title(),
            "body": BODY_LABELS[c["body"]],
            "seats": c["seats"],
            "fit": c["fit"],
            "reliability": c["reliability"],
            "safety": c["safety"],
            "why": explain(c),
            "caveats": c.get("caveats", []),
            "investigations": round(c["investigations"], 1),
            "recalls": c["recalls"],
            "complaints_per_year": round(c["complaints_per_year"]),
        } for c in results],
    }


@app.get("/")
def home():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
