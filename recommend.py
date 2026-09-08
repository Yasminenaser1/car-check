import sqlite3
from scoring import score_all

BODY_LABELS = {
    "sedan": "Sedan", "compact_suv": "Compact SUV", "midsize_suv": "Midsize SUV",
    "large_suv": "Large SUV", "minivan": "Minivan", "offroad": "Off-road SUV",
}


def recommend(cars, kids=0, priority="balanced", min_year=None, top_n=5):
    """Rank cars for one person's situation. Returns (results, notes)."""
    notes = []

    # Hard filters: things that rule a car out rather than score it down
    people = kids + 2
    pool = [c for c in cars if c["seats"] >= people]
    if not pool:
        return [], [f"No car in the database seats {people} people."]
    if kids >= 3:
        notes.append(
            f"Showing cars that seat {people}+. Five-seaters technically qualify, "
            "but three car seats across one rear bench is a tight fit — those are "
            "flagged below.")

    # Per-car caveats rather than hard exclusions: the person decides
    for c in pool:
        c["caveats"] = []
        if kids >= 3 and c["seats"] <= 5:
            c["caveats"].append("only 5 seats — three car seats side by side is tight")

    if min_year:
        newer = [c for c in pool if c["year"] >= min_year]
        if newer:
            pool = newer
        else:
            notes.append(f"No {min_year}+ cars matched, so older years are still shown.")

    weights = {
        "balanced":    {"reliability": 0.5, "safety": 0.5},
        "reliability": {"reliability": 0.8, "safety": 0.2},
        "safety":      {"reliability": 0.2, "safety": 0.8},
    }[priority]

    for c in pool:
        c["fit"] = round(weights["reliability"] * c["reliability"] +
                         weights["safety"] * c["safety"])

    ranked = sorted(pool, key=lambda c: -c["fit"])

    spread = max(c["safety"] for c in pool) - min(c["safety"] for c in pool)
    if priority == "safety" and spread < 25:
        notes.append(
            f"Safety scores here only span {spread} points — every car cleared "
            "NHTSA testing, so this preference barely changes the order.")

    return ranked[:top_n], notes


def explain(car):
    bits = []
    if car["investigations"] == 0:
        bits.append("no NHTSA investigations")
    else:
        bits.append(f"{car['investigations']:.0f} NHTSA investigation(s)")
    bits.append(f"{car['recalls']} recalls")
    bits.append(f"{car['complaints_per_year']:.0f} complaints/year on the road")
    if not car.get("stars_tested"):
        bits.append("not crash-tested — safety score is a neutral placeholder")
    return "; ".join(bits)


def caveat_lines(car):
    return [f"     heads up: {c}" for c in car.get("caveats", [])]


if __name__ == "__main__":
    conn = sqlite3.connect("cars.db")
    cars = score_all(conn)

    scenarios = [
        ("Mom, 3 kids, reliability matters most", dict(kids=3, priority="reliability")),
        ("Mom, 3 kids, safety matters most",      dict(kids=3, priority="safety")),
        ("Couple, 1 kid, balanced, 2018+",        dict(kids=1, priority="balanced", min_year=2018)),
    ]

    for label, kwargs in scenarios:
        results, notes = recommend(cars, **kwargs)
        print(f"\n=== {label} ===")
        for n in notes:
            print(f"  note: {n}")
        for i, c in enumerate(results, 1):
            print(f"  {i}. {c['year']} {c['make'].title()} {c['model'].title()} "
                  f"({BODY_LABELS[c['body']]}, {c['seats']} seats) — fit {c['fit']}")
            print(f"     {explain(c)}")
            for line in caveat_lines(c):
                print(line)
    conn.close()
