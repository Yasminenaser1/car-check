# Car Check

Answer three questions about your life, get a ranked shortlist of used cars —
scored from NHTSA safety ratings, recalls, consumer complaints and open
federal investigations.

**Live demo:** https://car-check-w99m.onrender.com

_Free tier — the first request after 15 minutes idle takes ~30 seconds to wake._

## Why it isn't just a lookup table

Public vehicle data is easy to get and easy to misread. Most of the work here
was in refusing to rank on numbers that look meaningful but aren't:

- **Complaint counts scale with age.** A 2016 model has had years longer for
  owners to file than a 2019. Complaints are normalised per year on the road,
  which moved several older cars up the rankings once the confound was removed.
- **Complaint counts also scale with sales volume**, and sales figures aren't
  publicly free. Cars are therefore ranked against peers in their own class
  rather than against the whole dataset, and the score is presented as a
  relative standing, not an absolute reliability rating.
- **Crash-test stars barely separate modern cars.** Almost every vehicle here
  scores 4 or 5. Safety is weighted 90% on the certified star rating and only
  10% on rollover, because percentile-ranking rollover inside a body class
  manufactured 40-point differences out of a range no buyer would notice.
- **`"Not Rated"` is not zero.** SQLite casts it to 0, which silently made
  untested vehicles look like crash-test failures. Untested variants are
  excluded from the average and flagged in the UI instead.
- **A class with one model always contains its own winner.** Ranking within raw
  body type gave the only minivan and the only off-road SUV top scores by
  default — including recommending a Jeep Wrangler with three open federal
  investigations to a parent of three. Cars are ranked within broader
  comparison groups so family vehicles compete with family vehicles.

Open NHTSA **investigations** carry the most weight in the reliability score.
Anyone can file a complaint; a federal investigation means regulators saw a
pattern worth pursuing, which makes it the least volume-sensitive signal
available for free.

## Preferences change the answer

Priority isn't cosmetic — it reweights the ranking, and the UI says so when it
*doesn't* matter. Ask for safety-first and the app will tell you that every car
in the dataset cleared NHTSA testing, so the preference barely reorders
anything. Recommendations carry caveats rather than silent exclusions: a
five-seater still appears for a parent of three, flagged with the reason it
might not work.

## Data

All from free public APIs, no keys:

- `api.nhtsa.gov` — recalls, consumer complaints, NCAP crash-test ratings
- Body type and seating are hand-coded in `metadata.py` for the 28-model seed list

Coverage is **2016–2019**, 28 models, ~100 model-years. `cars.db` is committed
so the app is reproducible without re-running the ingest.

## Running it

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn api:app --reload
```

Rebuild the database from scratch (~10 minutes of API calls):

```bash
python ingest.py && python metadata.py
```

## Tests

```bash
python -m pytest tests/ -q
```

Eight tests, including behavioural ones: seat filters must hold, changing
priority must change the ranking, more investigations must not score better,
and no car may be scored as if untested means unsafe.

## Limitations

- Four model years and 28 models — a starting set, not the full market
- No pricing or fuel-economy data yet, so "affordable" isn't answerable
- Complaint rates are not volume-normalised; treat scores as relative standing
  within a class, not absolute reliability
- Seating figures are typical maximums and vary by trim
