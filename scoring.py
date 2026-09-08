import sqlite3


def fetch_rows(conn):
    """One row per model-year, with safety aggregated across variants."""
    return conn.execute("""
        SELECT v.year, v.make, v.model, m.body, m.seats,
               v.recall_count, v.complaint_count,
               AVG(s.investigations)         AS investigations,
               AVG(s.rollover_possibility)   AS rollover,
               AVG(CASE WHEN s.overall GLOB '[0-9]*'
                        THEN CAST(s.overall AS INTEGER) END) AS stars
        FROM vehicles v
        JOIN model_meta m ON v.make = m.make AND v.model = m.model
        JOIN safety s     ON v.year = s.year AND v.make = s.make AND v.model = s.model
        GROUP BY v.year, v.make, v.model
    """).fetchall()


def percentile_ranks(values):
    """Map each value to 0-1, where 1 = lowest value (best). Ties share a rank."""
    ordered = sorted(set(values))
    if len(ordered) == 1:
        return {ordered[0]: 0.5}
    return {v: 1 - (i / (len(ordered) - 1)) for i, v in enumerate(ordered)}


def score_all(conn):
    rows = fetch_rows(conn)
    cars = [dict(zip(
        ["year", "make", "model", "body", "seats", "recalls",
         "complaints", "investigations", "rollover", "stars"], r)) for r in rows]

    # Complaints pile up the longer a car has been on the road, so a 2016
    # has had years more exposure than a 2019. Compare per year, not totals.
    CURRENT_YEAR = 2026
    for c in cars:
        exposure = max(CURRENT_YEAR - c["year"], 1)
        c["complaints_per_year"] = c["complaints"] / exposure

    # Rank within comparison groups, not raw body type: a class holding one
    # model (minivan, offroad) would only ever rank that model against itself,
    # which guarantees it a top score it hasn't earned.
    GROUPS = {
        "sedan": "car", "compact_suv": "small_suv", "midsize_suv": "small_suv",
        "large_suv": "family_hauler", "minivan": "family_hauler",
        "offroad": "small_suv",
    }
    for c in cars:
        c["group"] = GROUPS[c["body"]]

    for group in {c["group"] for c in cars}:
        peers = [c for c in cars if c["group"] == group]
        for field in ["recalls", "complaints_per_year", "investigations", "rollover"]:
            ranks = percentile_ranks([p[field] or 0 for p in peers])
            for p in peers:
                p[f"{field}_rank"] = ranks[p[field] or 0]

    for c in cars:
        c["reliability"] = round(100 * (
            0.45 * c["investigations_rank"] +
            0.30 * c["recalls_rank"] +
            0.25 * c["complaints_per_year_rank"]
        ))
        # Stars are what NHTSA actually certifies. Rollover possibility varies
        # so little within a body class that percentile-ranking it invents
        # differences that aren't real, so it only breaks ties.
        c["safety"] = round(100 * (
            0.9 * ((c["stars"] if c["stars"] is not None else 3) / 5) +
            0.1 * c["rollover_rank"]
        ))
        c["stars_tested"] = c["stars"] is not None
    return cars


if __name__ == "__main__":
    conn = sqlite3.connect("cars.db")
    cars = score_all(conn)

    for body in ["large_suv", "sedan", "compact_suv"]:
        peers = sorted([c for c in cars if c["body"] == body],
                       key=lambda c: -c["reliability"])
        print(f"\n=== {body} — most to least reliable ===")
        for c in peers[:5]:
            print(f"  {c['reliability']:3d} rel {c['safety']:3d} saf  "
                  f"{c['year']} {c['make']} {c['model']:15s} "
                  f"inv={c['investigations']:.1f} rec={c['recalls']:2d} comp={c['complaints']}")
        print("  ...")
        for c in peers[-3:]:
            print(f"  {c['reliability']:3d} rel {c['safety']:3d} saf  "
                  f"{c['year']} {c['make']} {c['model']:15s} "
                  f"inv={c['investigations']:.1f} rec={c['recalls']:2d} comp={c['complaints']}")
    conn.close()
