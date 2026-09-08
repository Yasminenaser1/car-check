import sqlite3

# body: sedan | compact_suv | midsize_suv | large_suv | minivan | offroad
# seats: typical max seating
MODELS = {
    ("toyota", "camry"):          ("sedan", 5),
    ("toyota", "corolla"):        ("sedan", 5),
    ("toyota", "rav4"):           ("compact_suv", 5),
    ("toyota", "highlander"):     ("large_suv", 8),
    ("honda", "accord"):          ("sedan", 5),
    ("honda", "civic"):           ("sedan", 5),
    ("honda", "cr-v"):            ("compact_suv", 5),
    ("honda", "pilot"):           ("large_suv", 8),
    ("honda", "odyssey"):         ("minivan", 8),
    ("ford", "escape"):           ("compact_suv", 5),
    ("ford", "explorer"):         ("large_suv", 7),
    ("chevrolet", "equinox"):     ("compact_suv", 5),
    ("chevrolet", "malibu"):      ("sedan", 5),
    ("chevrolet", "traverse"):    ("large_suv", 8),
    ("nissan", "rogue"):          ("compact_suv", 5),
    ("nissan", "altima"):         ("sedan", 5),
    ("nissan", "sentra"):         ("sedan", 5),
    ("subaru", "outback"):        ("midsize_suv", 5),
    ("subaru", "forester"):       ("compact_suv", 5),
    ("hyundai", "elantra"):       ("sedan", 5),
    ("hyundai", "santa fe"):      ("midsize_suv", 5),
    ("hyundai", "tucson"):        ("compact_suv", 5),
    ("kia", "sorento"):           ("midsize_suv", 7),
    ("mazda", "cx-5"):            ("compact_suv", 5),
    ("jeep", "grand cherokee"):   ("midsize_suv", 5),
    ("jeep", "wrangler"):         ("offroad", 5),
    ("volkswagen", "jetta"):      ("sedan", 5),
    ("dodge", "charger"):         ("sedan", 5),
}

if __name__ == "__main__":
    conn = sqlite3.connect("cars.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS model_meta (
            make TEXT, model TEXT, body TEXT, seats INTEGER,
            PRIMARY KEY (make, model)
        )
    """)
    for (make, model), (body, seats) in MODELS.items():
        conn.execute("INSERT OR REPLACE INTO model_meta VALUES (?,?,?,?)",
                     (make, model, body, seats))
    conn.commit()

    missing = conn.execute("""
        SELECT DISTINCT s.make, s.model FROM safety s
        LEFT JOIN model_meta m ON s.make = m.make AND s.model = m.model
        WHERE m.body IS NULL
    """).fetchall()
    print("models in safety with no metadata:", missing or "none")

    print("\nby body type:")
    for row in conn.execute("""
        SELECT m.body, COUNT(DISTINCT s.make || s.model) AS models, COUNT(*) AS rows
        FROM safety s JOIN model_meta m ON s.make = m.make AND s.model = m.model
        GROUP BY m.body ORDER BY rows DESC
    """):
        print(f"  {row[0]:14s} {row[1]:2d} models, {row[2]:3d} rows")
    conn.close()
