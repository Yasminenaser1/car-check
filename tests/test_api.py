import sqlite3
import pytest
from fastapi.testclient import TestClient

import api
from scoring import score_all
from recommend import recommend

client = TestClient(api.app)


@pytest.fixture(scope="module")
def cars():
    conn = sqlite3.connect("cars.db")
    return score_all(conn)


def test_meta_reports_data():
    r = client.get("/meta")
    assert r.status_code == 200
    assert r.json()["car_count"] > 0


def test_recommend_returns_results():
    r = client.post("/recommend", json={"kids": 2, "priority": "balanced"})
    assert r.status_code == 200
    assert len(r.json()["results"]) > 0


def test_rejects_impossible_input():
    assert client.post("/recommend", json={"kids": 99}).status_code == 422


def test_seat_filter_is_enforced(cars):
    """Four kids means six people, so nothing smaller may be suggested."""
    results, _ = recommend(cars, kids=4)
    assert results, "expected at least one large vehicle"
    assert all(c["seats"] >= 6 for c in results)


def test_priority_changes_the_ranking(cars):
    """The preference has to actually do something, or the app is lying."""
    rel, _ = recommend(cars, kids=3, priority="reliability")
    saf, _ = recommend(cars, kids=3, priority="safety")
    assert [(c["year"], c["model"]) for c in rel] != [(c["year"], c["model"]) for c in saf]


def test_investigations_hurt_the_score(cars):
    """Within a comparison group, more investigations should not score better."""
    group = [c for c in cars if c["group"] == "small_suv"]
    clean = [c for c in group if c["investigations"] == 0]
    dirty = [c for c in group if c["investigations"] >= 3]
    assert clean and dirty
    assert max(c["reliability"] for c in clean) > max(c["reliability"] for c in dirty)


def test_five_seaters_are_flagged_for_three_kids(cars):
    results, notes = recommend(cars, kids=3)
    assert notes
    for c in results:
        if c["seats"] <= 5:
            assert c["caveats"], f"{c['model']} seats 5 but carries no warning"


def test_unrated_cars_are_not_scored_as_zero(cars):
    """'Not Rated' must not be cast to 0 stars and look like a failure."""
    assert all(c["safety"] > 40 for c in cars)
