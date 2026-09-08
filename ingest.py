import sqlite3
import time
import requests

DB = "cars.db"
DELAY = 0.3

SEED = [
    ("toyota", "camry"), ("toyota", "corolla"), ("toyota", "rav4"),
    ("toyota", "highlander"), ("honda", "accord"), ("honda", "civic"),
    ("honda", "cr-v"), ("honda", "pilot"), ("honda", "odyssey"),
    ("ford", "explorer"), ("ford", "escape"), ("ford", "f-150"),
    ("chevrolet", "equinox"), ("chevrolet", "malibu"), ("chevrolet", "traverse"),
    ("nissan", "rogue"), ("nissan", "altima"), ("nissan", "sentra"),
    ("subaru", "outback"), ("subaru", "forester"),
    ("hyundai", "elantra"), ("hyundai", "santa fe"), ("hyundai", "tucson"),
    ("kia", "sorento"), ("kia", "telluride"), ("mazda", "cx-5"),
    ("jeep", "grand cherokee"), ("jeep", "wrangler"),
    ("volkswagen", "jetta"), ("dodge", "charger"),
]
YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2022]


def get(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    time.sleep(DELAY)
    return r.json()


def setup(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS vehicles (
        year INTEGER, make TEXT, model TEXT,
        recall_count INTEGER, complaint_count INTEGER,
        fetched_at TEXT,
        PRIMARY KEY (year, make, model)
    );
    CREATE TABLE IF NOT EXISTS safety (
        year INTEGER, make TEXT, model TEXT,
        vehicle_id INTEGER PRIMARY KEY, description TEXT,
        overall TEXT, front TEXT, side TEXT, rollover TEXT,
        rollover_possibility REAL,
        investigations INTEGER,
        esc TEXT, fcw TEXT, ldw TEXT
    );
    """)


def ingest(conn, year, make, model):
    recalls = get(f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}")
    complaints = get(f"https://api.nhtsa.gov/complaints/complaintsByVehicle?make={make}&model={model}&modelYear={year}")

    conn.execute(
        "INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,datetime('now'))",
        (year, make, model, recalls.get("Count", 0), complaints.get("count", 0)),
    )

    listing = get(f"https://api.nhtsa.gov/SafetyRatings/modelyear/{year}/make/{make}/model/{model}")
    for variant in listing.get("Results", []):
        vid = variant.get("VehicleId")
        if not vid:
            continue
        detail = get(f"https://api.nhtsa.gov/SafetyRatings/VehicleId/{vid}")
        d = (detail.get("Results") or [{}])[0]
        conn.execute(
            "INSERT OR REPLACE INTO safety VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (year, make, model, vid, d.get("VehicleDescription"),
             d.get("OverallRating"), d.get("OverallFrontCrashRating"),
             d.get("OverallSideCrashRating"), d.get("RolloverRating"),
             d.get("RolloverPossibility"), d.get("InvestigationCount"),
             d.get("NHTSAElectronicStabilityControl"),
             d.get("NHTSAForwardCollisionWarning"),
             d.get("NHTSALaneDepartureWarning")),
        )

    print(f"  {year} {make} {model}: {recalls.get('Count', 0)} recalls, "
          f"{complaints.get('count', 0)} complaints, {listing.get('Count', 0)} variants")


if __name__ == "__main__":
    conn = sqlite3.connect(DB)
    setup(conn)
    for year in YEARS:
        for make, model in SEED:
            try:
                ingest(conn, year, make, model)
                conn.commit()
            except Exception as e:
                print(f"  FAILED {year} {make} {model}: {e}")
    conn.close()
    print("done")
