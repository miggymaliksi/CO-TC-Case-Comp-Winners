import concurrent.futures
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from backend import main
from backend.models import IngredientRequest, PantryItem


@pytest.fixture
def clients(tmp_path, monkeypatch):
    monkeypatch.setattr(
        main.local_ai,
        "status",
        lambda: {
            "provider": "ollama",
            "model": "qwen3:1.7b",
            "ready": True,
            "api_fees": False,
        },
    )
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db",
        connect_args={"check_same_thread": False, "timeout": 20},
    )

    @event.listens_for(engine, "connect")
    def foreign_keys(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    monkeypatch.setattr(main, "engine", engine)
    with TestClient(main.app) as a, TestClient(main.app) as b, TestClient(
        main.app
    ) as c:
        for client, uid in [(a, 1), (b, 2), (c, 3)]:
            assert (
                client.post("/api/demo/session", json={"user_id": uid}).status_code
                == 200
            )
        yield a, b, c
    engine.dispose()


def state(c):
    r = c.get("/api/state")
    assert r.status_code == 200, r.text
    return r.json()


def recipe(c, id="tomato-pasta"):
    return next(r for r in state(c)["recipes"] if r["id"] == id)


def stock(c, name, unit):
    return sum(
        main.convert(i["quantity"], i["unit"], unit) or 0
        for i in state(c)["pantry"]
        if i["name"] == name
    )


def request(c, **overrides):
    data = {
        "name": "garlic",
        "quantity": 1,
        "unit": "clove",
        "community_id": 1,
        "minutes": 30,
        "recipe_id": "tomato-pasta",
    }
    data.update(overrides)
    r = c.post("/api/requests", json=data)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_pantry_persists_and_rejects_invalid_input(clients):
    a, b, _ = clients
    payload = {
        "name": "  Carrots  ",
        "quantity": 2,
        "unit": "kg",
        "stored_on": str(date.today()),
        "location": "Fridge",
    }
    r = a.post("/api/pantry", json=payload)
    assert r.status_code == 201
    id = r.json()["id"]
    assert next(i for i in state(a)["pantry"] if i["id"] == id)["name"] == "carrots"
    with Session(main.engine) as db:
        assert db.get(PantryItem, id).quantity == 2
    assert b.patch(f"/api/pantry/{id}", json=payload).status_code == 404
    assert b.delete(f"/api/pantry/{id}").status_code == 404
    for bad in [
        {"quantity": 0},
        {"quantity": -1},
        {"name": "   "},
        {"unit": "handful"},
        {"stored_on": str(date.today() + timedelta(days=1))},
    ]:
        assert a.post("/api/pantry", json={**payload, **bad}).status_code == 422
    assert (
        a.patch(f"/api/pantry/{id}", json={**payload, "quantity": 1}).status_code == 200
    )
    assert a.delete(f"/api/pantry/{id}").status_code == 200
    assert all(i["id"] != id for i in state(a)["pantry"])


def test_quantity_aware_coverage_scaling_and_unit_conversion(clients):
    a, _, _ = clients
    assert recipe(a)["coverage"] == 80
    assert recipe(a, "tomato-toast")["ready"]
    r = a.post(
        "/api/pantry",
        json={
            "name": "garlic",
            "quantity": 1,
            "unit": "each",
            "stored_on": str(date.today()),
            "location": "Pantry",
        },
    )
    assert r.status_code == 201
    assert recipe(a)["coverage"] == 80  # each cannot silently convert to a clove
    a.post(
        "/api/pantry",
        json={
            "name": "garlic",
            "quantity": 1,
            "unit": "clove",
            "stored_on": str(date.today()),
            "location": "Pantry",
        },
    )
    assert recipe(a)["ready"]
    assert (
        a.patch(
            "/api/settings", json={"servings": 4, "diet": "All", "max_minutes": 60}
        ).status_code
        == 200
    )
    assert recipe(a)["servings"] == 4
    garlic = next(i for i in recipe(a)["ingredients"] if i["name"] == "garlic")
    assert garlic["quantity"] == 2 and garlic["missing"] == 1
    assert main.convert(1, "kg", "g") == 1000
    assert main.convert(1, "each", "g") is None


def test_complete_exchange_and_cooking_are_idempotent(clients):
    a, b, _ = clients
    id = request(a)
    before = stock(b, "garlic", "clove")
    assert b.post(f"/api/requests/{id}/accept").status_code == 200
    assert stock(b, "garlic", "clove") == before - 1
    assert a.post(f"/api/requests/{id}/complete").status_code == 200
    assert a.post(f"/api/requests/{id}/complete").json()["already_recorded"]
    assert stock(a, "garlic", "clove") == 1
    assert recipe(a)["ready"]
    data = {"request_key": "test-meal-0001"}
    assert a.post("/api/recipes/tomato-pasta/cook", json=data).status_code == 200
    assert a.post("/api/recipes/tomato-pasta/cook", json=data).json()[
        "already_recorded"
    ]
    assert stock(a, "garlic", "clove") == 0
    assert state(a)["meals_cooked"] == 1
    assert state(b)["shared_count"] == 1


def test_reservations_return_original_age_on_cancel(clients):
    a, b, _ = clients
    id = request(a)
    before = next(i for i in state(b)["pantry"] if i["name"] == "garlic")
    b.post(f"/api/requests/{id}/accept")
    assert b.post(f"/api/requests/{id}/cancel").status_code == 200
    assert b.post(f"/api/requests/{id}/cancel").status_code == 200
    assert stock(b, "garlic", "clove") == before["quantity"]
    returned = [i for i in state(b)["pantry"] if i["name"] == "garlic"]
    assert all(i["stored_on"] == before["stored_on"] for i in returned)
    assert a.post(f"/api/requests/{id}/complete").status_code == 409


def test_deadline_and_decline_fallback(clients):
    a, b, c = clients
    id = request(a)
    with Session(main.engine) as db, db.begin():
        db.get(IngredientRequest, id).deadline = main.now() - 1
    assert b.post(f"/api/requests/{id}/accept").status_code == 409
    assert next(r for r in state(a)["requests"] if r["id"] == id)["status"] == "expired"
    assert any(r["ready"] for r in state(a)["recipes"])
    direct = request(a, community_id=None, friend_id=2)
    assert b.post(f"/api/requests/{direct}/decline").status_code == 200
    assert (
        next(r for r in state(a)["requests"] if r["id"] == direct)["status"]
        == "declined"
    )
    community = request(a)
    assert c.post(f"/api/requests/{community}/decline").status_code == 200
    assert (
        next(r for r in state(a)["requests"] if r["id"] == community)["status"]
        == "pending"
    )
    assert b.post(f"/api/requests/{community}/accept").status_code == 200


def test_access_boundaries_and_cross_site_mutations(clients):
    a, b, c = clients
    private = a.post("/api/communities", json={"name": "Just Alex"}).json()
    id = request(a, community_id=private["id"])
    assert all(r["id"] != id for r in state(b)["requests"])
    assert b.post(f"/api/requests/{id}/accept").status_code == 404
    assert b.get(f"/api/messages?community_id={private['id']}").status_code == 403
    assert (
        a.post(
            "/api/messages", json={"community_id": private["id"], "body": "private"}
        ).status_code
        == 201
    )
    direct = request(a, community_id=None, friend_id=2)
    assert c.post(f"/api/requests/{direct}/accept").status_code == 404
    assert b.post(f"/api/requests/{direct}/complete").status_code == 403
    assert a.post(f"/api/requests/{direct}/accept").status_code == 403
    assert (
        a.post(
            "/api/demo/session",
            json={"user_id": 1},
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    with TestClient(main.app) as stranger:
        assert stranger.get("/api/state").status_code == 401
    assert (
        a.post(
            "/api/requests",
            json={
                "name": "rice",
                "quantity": 1,
                "unit": "g",
                "community_id": 1,
                "friend_id": 2,
            },
        ).status_code
        == 422
    )


def test_competing_acceptance_and_insufficient_inventory(clients):
    a, b, c = clients
    id = request(a)
    # Two concurrent clicks by an eligible provider must reserve only one clove.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        codes = list(
            pool.map(
                lambda _: b.post(f"/api/requests/{id}/accept").status_code, range(2)
            )
        )
    assert sorted(codes) == [200, 409]
    assert stock(b, "garlic", "clove") == 7
    huge = request(a, quantity=100)
    assert b.post(f"/api/requests/{huge}/accept").status_code == 409
    assert stock(b, "garlic", "clove") == 7


def test_receipt_batch_atomic_and_duplicate_protected(clients):
    a, _, _ = clients
    row = {
        "name": "carrots",
        "quantity": 1,
        "unit": "kg",
        "stored_on": str(date.today()),
        "location": "Fridge",
    }
    data = {"rows": [row], "request_key": "receipt-test-1"}
    assert a.post("/api/pantry/batch", json=data).status_code == 200
    assert a.post("/api/pantry/batch", json=data).json()["already_recorded"]
    assert stock(a, "carrots", "kg") == 1
    bad = {
        "rows": [{**row, "name": "potatoes"}, {**row, "quantity": -1}],
        "request_key": "receipt-test-2",
    }
    assert a.post("/api/pantry/batch", json=bad).status_code == 422
    assert stock(a, "potatoes", "kg") == 0


def test_private_pickup_chat_and_friend_invite(clients):
    a, b, c = clients
    id = request(a)
    assert b.post(f"/api/requests/{id}/accept").status_code == 200
    msg = {"request_id": id, "body": "Meet in the lobby?"}
    assert a.post("/api/messages", json=msg).status_code == 201
    assert b.get(f"/api/messages?request_id={id}").json()[0]["body"] == msg["body"]
    assert c.get(f"/api/messages?request_id={id}").status_code == 403
    invite = a.post("/api/friends/invite").json()
    assert c.post("/api/friends/join", json=invite).status_code == 200
    assert {f["id"] for f in state(a)["friends"]} == {2, 3}
    assert c.post("/api/friends/join", json=invite).status_code == 404


def test_cook_cannot_consume_missing_ingredients(clients):
    a, _, _ = clients
    before = stock(a, "pasta", "g")
    assert (
        a.post(
            "/api/recipes/tomato-pasta/cook", json={"request_key": "missing-garlic"}
        ).status_code
        == 409
    )
    assert stock(a, "pasta", "g") == before


def local_response():
    return {
        "name": "Tomato and spinach salad",
        "subtitle": "A quick pantry lunch.",
        "minutes": 10,
        "servings": 2,
        "tags": ["Vegan", "Gluten-free"],
        "ingredients": [
            {"name": "tomatoes", "quantity": 300, "unit": "g"},
            {"name": "spinach", "quantity": 50, "unit": "g"},
            {"name": "olive oil", "quantity": 20, "unit": "ml"},
        ],
        "steps": [
            "Chop the tomatoes and spinach.",
            "Toss with olive oil and serve.",
        ],
    }


def mock_model(monkeypatch, recipe=None):
    import json, httpx

    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(
            200,
            json={
                "done": True,
                "done_reason": "stop",
                "message": {
                    "content": json.dumps({"recipes": [recipe or local_response()]})
                },
            },
        )

    monkeypatch.setattr(main.local_ai.httpx, "post", post)
    return calls


def test_local_ai_cache_privacy_and_cooking(clients, monkeypatch):
    a, b, _ = clients
    calls = mock_model(monkeypatch)
    before = stock(a, "tomatoes", "g")
    r = a.post("/api/recipes/generate")
    assert r.status_code == 200, r.text
    id = r.json()["ids"][0]
    assert stock(a, "tomatoes", "g") == before  # Generation cannot mutate pantry.
    assert a.post("/api/recipes/generate").json()["cached"]
    assert len(calls) == 1
    url, args = calls[0]
    assert url == "http://127.0.0.1:11434/api/chat"
    assert args["trust_env"] is False and args["json"]["think"] is False
    assert "Authorization" not in args.get("headers", {})
    assert not any(r["id"] == id for r in state(b)["recipes"])
    assert (
        b.post(
            f"/api/recipes/{id}/cook", json={"request_key": "other-user-key"}
        ).status_code
        == 404
    )
    assert (
        b.post(
            "/api/requests",
            json={
                "name": "garlic",
                "quantity": 1,
                "unit": "clove",
                "community_id": 1,
                "recipe_id": id,
            },
        ).status_code
        == 404
    )
    assert (
        a.post(
            f"/api/recipes/{id}/cook", json={"request_key": "local-meal-key"}
        ).status_code
        == 200
    )
    assert stock(a, "tomatoes", "g") == before - 300


def test_local_ai_rejects_bad_coverage_and_duplicate_lines(clients, monkeypatch):
    a, _, _ = clients
    bad = local_response()
    bad["ingredients"] = [
        {"name": "salmon", "quantity": 300, "unit": "g"},
        {"name": "eggs", "quantity": 2, "unit": "each"},
    ]
    mock_model(monkeypatch, bad)
    assert a.post("/api/recipes/generate").status_code == 422
    assert not any(r["source"] == "local_ai" for r in state(a)["recipes"])
    later = main.now() + 11
    monkeypatch.setattr(main, "now", lambda: later)
    duplicate = local_response()
    duplicate["ingredients"].append(duplicate["ingredients"][0])
    mock_model(monkeypatch, duplicate)
    assert a.post("/api/recipes/generate").status_code == 422


def test_local_ai_offline_and_cloud_models_refused(clients, monkeypatch):
    import httpx

    a, _, _ = clients

    def offline(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(main.local_ai.httpx, "post", offline)
    assert a.post("/api/recipes/generate").status_code == 503
    monkeypatch.setenv("SAVOR_LOCAL_MODEL", "qwen3:cloud")
    later = main.now() + 11
    monkeypatch.setattr(main, "now", lambda: later)
    assert a.post("/api/recipes/generate").status_code == 503


def test_local_ai_rejects_wrong_servings_and_preserves_database(clients, monkeypatch):
    from backend.models import SchemaVersion

    a, _, _ = clients
    bad = local_response()
    bad["servings"] = 8
    mock_model(monkeypatch, bad)
    before = state(a)["pantry"]
    assert a.post("/api/recipes/generate").status_code == 422
    assert state(a)["pantry"] == before
    with Session(main.engine) as db:
        assert db.get(SchemaVersion, 2)


def test_local_ai_rejects_excess_oil_and_uncooked_starch(clients, monkeypatch):
    a, _, _ = clients
    bad = local_response()
    bad["ingredients"][2]["quantity"] = 150
    mock_model(monkeypatch, bad)
    assert a.post("/api/recipes/generate").status_code == 422
    later = main.now() + 11
    monkeypatch.setattr(main, "now", lambda: later)
    bad = local_response()
    bad["ingredients"].append({"name": "pasta", "quantity": 100, "unit": "g"})
    mock_model(monkeypatch, bad)
    assert a.post("/api/recipes/generate").status_code == 422


@pytest.mark.parametrize(
    "change", [{"diet": "Vegan"}, {"servings": 4}, {"max_minutes": 10}]
)
def test_changed_preferences_reach_model_and_replace_current_ideas(
    clients, monkeypatch, change
):
    import json

    a, _, _ = clients
    mock_model(monkeypatch)
    first = a.post("/api/recipes/generate").json()["ids"][0]
    before = state(a)
    assert next(r for r in before["recipes"] if r["id"] == first)[
        "matches_current_context"
    ]
    preferences = {
        key: before["user"][key] for key in ("servings", "diet", "max_minutes")
    }
    preferences.update(change)
    assert a.patch("/api/settings", json=preferences).status_code == 200
    assert not next(r for r in state(a)["recipes"] if r["id"] == first)[
        "matches_current_context"
    ]
    proposal = local_response()
    proposal["servings"] = preferences["servings"]
    calls = mock_model(monkeypatch, proposal)
    later = main.now() + 11
    monkeypatch.setattr(main, "now", lambda: later)
    result = a.post("/api/recipes/generate")
    assert result.status_code == 200, result.text
    assert not result.json()["cached"]
    assert len(calls) == 1
    sent = json.loads(calls[0][1]["json"]["messages"][1]["content"])
    assert sent["preferences"] == preferences
    new_id = result.json()["ids"][0]
    current = next(r for r in state(a)["recipes"] if r["id"] == new_id)
    assert current["matches_current_context"]
    assert current["generated_for"] == preferences
    assert state(a)["pantry"] == before["pantry"]
    assert a.post("/api/recipes/generate").json()["cached"]


def test_pantry_change_marks_old_ai_ideas_as_saved(clients, monkeypatch):
    a, _, _ = clients
    mock_model(monkeypatch)
    identifier = a.post("/api/recipes/generate").json()["ids"][0]
    item = next(i for i in state(a)["pantry"] if i["name"] == "tomatoes")
    data = {
        key: item[key] for key in ("name", "quantity", "unit", "stored_on", "location")
    }
    data["quantity"] -= 1
    assert a.patch(f"/api/pantry/{item['id']}", json=data).status_code == 200
    old = next(r for r in state(a)["recipes"] if r["id"] == identifier)
    assert not old["matches_current_context"]


def test_quick_gluten_free_shortlist_uses_compatible_candidates():
    context = {
        "preferences": {"diet": "Gluten-free", "servings": 2, "max_minutes": 10},
        "pantry": [
            {"name": name}
            for name in ("pasta", "rice", "bread", "tomatoes", "spinach", "olive oil")
        ],
    }
    names = {i["name"] for i in main.local_ai.selected_context(context)["pantry"]}
    assert names == {"tomatoes", "spinach", "olive oil"}


def mock_library(monkeypatch):
    import httpx

    monkeypatch.setattr(main.recipe_library, "_cache", {})
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json={
                "meals": [
                    {
                        "idMeal": "52771",
                        "strMeal": "Tomato dinner",
                        "strCategory": "Vegetarian",
                        "strArea": "Italian",
                        "strMealThumb": "https://www.themealdb.com/images/media/meals/example.jpg",
                        "strIngredient1": "tomatoes",
                        "strMeasure1": "1 tin",
                        "strIngredient2": "spinach",
                        "strMeasure2": "a handful",
                        "strInstructions": "Cook the vegetables.\nServe warm.",
                    }
                ]
            },
        )

    monkeypatch.setattr(main.recipe_library.httpx, "get", get)
    return calls


def test_free_library_search_cache_and_original_measures(clients, monkeypatch):
    a, _, _ = clients
    calls = mock_library(monkeypatch)
    r = a.get(
        "/api/recipes/library/search", params={"query": "tomatoes", "by": "ingredient"}
    )
    assert r.status_code == 200, r.text
    assert not r.json()["cached"]
    assert (
        r.json()["recipes"][0]["source_url"] == "https://www.themealdb.com/meal/52771"
    )
    assert a.get("/api/recipes/library/search", params={"query": "tomatoes"}).json()[
        "cached"
    ]
    assert len(calls) == 1
    url, args = calls[0]
    assert url == "https://www.themealdb.com/api/json/v1/1/filter.php"
    assert args["params"] == {"i": "tomatoes"}
    assert args["trust_env"] is False and args["follow_redirects"] is False
    assert "Authorization" not in args.get("headers", {})
    full = a.get("/api/recipes/library/52771").json()
    assert full["ingredients"][0]["measure"] == "1 tin"
    assert full["ingredients"][1]["measure"] == "a handful"
    assert "servings" not in full and "minutes" not in full and "coverage" not in full


def test_library_failure_and_invalid_ids_preserve_pantry(clients, monkeypatch):
    import httpx

    a, _, _ = clients
    before = state(a)["pantry"]
    monkeypatch.setattr(main.recipe_library, "_cache", {})

    def offline(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(main.recipe_library.httpx, "get", offline)
    assert (
        a.get("/api/recipes/library/search", params={"query": "tomatoes"}).status_code
        == 503
    )
    assert a.get("/api/recipes/library/nope").status_code == 404
    assert (
        a.get("/api/recipes/library/search", params={"query": "x"}).status_code == 422
    )
    assert state(a)["pantry"] == before


def test_library_inspiration_is_adapted_by_local_ai_and_attributed(
    clients, monkeypatch
):
    import json

    a, b, _ = clients
    mock_library(monkeypatch)
    calls = mock_model(monkeypatch)
    before = state(a)["pantry"]
    response = a.post("/api/recipes/generate", json={"inspiration_id": "52771"})
    assert response.status_code == 200, response.text
    identifier = response.json()["ids"][0]
    recipe = next(r for r in state(a)["recipes"] if r["id"] == identifier)
    assert recipe["source"] == "local_ai"
    assert recipe["matches_current_context"]
    assert recipe["inspired_by"] == {
        "id": "52771",
        "name": "Tomato dinner",
        "url": "https://www.themealdb.com/meal/52771",
    }
    sent = json.loads(calls[0][1]["json"]["messages"][1]["content"])
    assert sent["inspiration"]["name"] == "Tomato dinner"
    assert a.post("/api/recipes/generate", json={"inspiration_id": "52771"}).json()[
        "cached"
    ]
    assert len(calls) == 1
    assert state(a)["pantry"] == before
    assert not any(r["id"] == identifier for r in state(b)["recipes"])


def test_library_requires_session_and_limits_image_hosts(clients):
    with TestClient(main.app) as anonymous:
        assert (
            anonymous.get(
                "/api/recipes/library/search", params={"query": "tomatoes"}
            ).status_code
            == 401
        )
    recipe = main.recipe_library._summary(
        {
            "idMeal": "52771",
            "strMeal": "Example",
            "strMealThumb": "https://untrusted.example/image.jpg",
        }
    )
    assert recipe["image_url"] is None
    assert recipe["source_url"] == "https://www.themealdb.com/meal/52771"
