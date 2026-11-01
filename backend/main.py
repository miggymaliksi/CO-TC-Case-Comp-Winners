"""Savor's local, sample-account API. Run from the repository root."""

import hashlib
import json
import math
import os
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import create_engine, event, select, text, func, or_
from sqlalchemy.orm import Session

from .models import (
    Base,
    SchemaVersion,
    User,
    SessionToken,
    PantryItem,
    Community,
    Membership,
    Friend,
    FriendInvite,
    IngredientRequest,
    Decline,
    Message,
    Cook,
    PantryImport,
    GeneratedRecipe,
    GenerationBudget,
)
from .recipes import RECIPES, UNITS, convert, amount_available, match_recipe
from .migrations import migrate
from . import local_ai, recipe_library

DATABASE = os.getenv("SAVOR_DATABASE_URL", "sqlite:///./savor.db")
DEMO = os.getenv("SAVOR_DEMO_MODE", "true").lower() == "true"
engine = create_engine(
    DATABASE,
    connect_args=(
        {"check_same_thread": False, "timeout": 20}
        if DATABASE.startswith("sqlite")
        else {}
    ),
)
if DATABASE.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def sqlite_config(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")


def now():
    return time.time()


def seed():
    migrate(engine)
    with Session(engine) as db, db.begin():
        if not db.get(SchemaVersion, 1):
            db.add(SchemaVersion(version=1))
        if db.get(User, 1):
            return
        db.add_all(
            [
                User(id=1, name="Alex", color="#315a40"),
                User(id=2, name="Jamie", color="#b66340"),
                User(id=3, name="Sam", color="#706393"),
            ]
        )
        db.flush()
        db.add_all(
            [
                Community(id=1, name="PBL", invite_code="PBL-DEMO", color="green"),
                Community(
                    id=2,
                    name="The Standard",
                    invite_code="STANDARD-DEMO",
                    color="orange",
                ),
            ]
        )
        db.flush()
        db.add_all(
            [
                Membership(user_id=u, community_id=c)
                for u, c in [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1)]
            ]
        )
        db.add_all([Friend(user_id=1, friend_id=2), Friend(user_id=2, friend_id=1)])
        today = date.today()
        stock = {
            1: [
                ("tomatoes", 700, "g", 5, "Fridge"),
                ("spinach", 150, "g", 4, "Fridge"),
                ("basil", 20, "g", 3, "Fridge"),
                ("pasta", 600, "g", 7, "Pantry"),
                ("olive oil", 250, "ml", 10, "Pantry"),
                ("bread", 6, "slice", 2, "Pantry"),
                ("lemon", 2, "each", 4, "Fridge"),
                ("rice", 500, "g", 9, "Pantry"),
            ],
            2: [
                ("garlic", 8, "clove", 5, "Pantry"),
                ("chickpeas", 400, "g", 2, "Pantry"),
                ("tomatoes", 500, "g", 2, "Fridge"),
            ],
            3: [("lemon", 4, "each", 1, "Fridge"), ("bread", 8, "slice", 1, "Pantry")],
        }
        for uid, items in stock.items():
            for name, qty, unit, age, loc in items:
                db.add(
                    PantryItem(
                        user_id=uid,
                        name=name,
                        quantity=qty,
                        unit=unit,
                        stored_on=str(today - timedelta(days=age)),
                        location=loc,
                    )
                )
        db.add_all(
            [
                Message(
                    user_id=2,
                    community_id=1,
                    body="A little garlic goes a long way. Happy to share a few cloves if anyone needs them!",
                    created_at=now() - 3600,
                ),
                Message(
                    user_id=3,
                    community_id=1,
                    body="Love this. I'll bring the lemons 🍋",
                    created_at=now() - 1800,
                ),
            ]
        )


@asynccontextmanager
async def lifespan(app):
    seed()
    yield


app = FastAPI(title="Savor local demo", lifespan=lifespan)


@app.middleware("http")
async def browser_boundary(request, call_next):
    host = request.url.hostname
    if host not in ("127.0.0.1", "localhost", "::1", "testserver"):
        return JSONResponse(
            {"detail": "This sample-account demo is local only."}, status_code=403
        )
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and urlparse(origin).netloc != request.headers.get("host"):
            return JSONResponse(
                {"detail": "Cross-site changes are not allowed."}, status_code=403
            )
    result = await call_next(request)
    result.headers["X-Content-Type-Options"] = "nosniff"
    result.headers["Referrer-Policy"] = "same-origin"
    result.headers["X-Frame-Options"] = "DENY"
    if request.url.path.startswith("/api"):
        result.headers["Cache-Control"] = "no-store"
    return result


def database(request: Request):
    with Session(engine, expire_on_commit=False) as db:
        try:
            # Serialize SQLite mutations across threads/processes, including read-modify-write flows.
            if DATABASE.startswith("sqlite") and request.method not in ("GET", "HEAD"):
                db.execute(text("BEGIN IMMEDIATE"))
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise


def current_user(request: Request, db: Session = Depends(database)):
    token = request.cookies.get("savor_session", "")
    session = (
        db.get(SessionToken, hashlib.sha256(token.encode()).hexdigest())
        if token
        else None
    )
    if not session or session.expires_at < now():
        raise HTTPException(401, "Choose a sample account to open the local demo.")
    return db.get(User, session.user_id)


class SessionInput(BaseModel):
    user_id: int


@app.post("/api/demo/session")
def sign_in(data: SessionInput, response: Response, db: Session = Depends(database)):
    if not DEMO:
        raise HTTPException(
            403, "Demo sign-in is disabled. Production identity is not configured."
        )
    if data.user_id not in (1, 2, 3) or not db.get(User, data.user_id):
        raise HTTPException(400, "Unknown sample account.")
    db.query(SessionToken).filter(SessionToken.expires_at < now()).delete()
    token = secrets.token_urlsafe(32)
    db.add(
        SessionToken(
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            user_id=data.user_id,
            expires_at=now() + 43200,
        )
    )
    response.set_cookie(
        "savor_session", token, httponly=True, samesite="strict", max_age=43200
    )
    return {"ok": True}


class PantryInput(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    quantity: float = Field(gt=0, le=100000, allow_inf_nan=False)
    unit: str
    stored_on: date
    location: str

    @field_validator("name")
    @classmethod
    def normalize(cls, v):
        v = " ".join(v.lower().strip().split())
        if not v:
            raise ValueError("Enter an ingredient name.")
        return v

    @field_validator("unit")
    @classmethod
    def valid_unit(cls, v):
        if v not in UNITS:
            raise ValueError("Choose a supported unit.")
        return v

    @field_validator("stored_on")
    @classmethod
    def past_date(cls, v):
        if v > date.today() or v < date(2000, 1, 1):
            raise ValueError("Use a storage date between 2000 and today.")
        return v

    @field_validator("location")
    @classmethod
    def location_value(cls, v):
        if v not in ("Pantry", "Fridge", "Freezer", "Counter"):
            raise ValueError("Choose a storage location.")
        return v


def pantry_dict(i):
    return {
        "id": i.id,
        "name": i.name,
        "quantity": round(i.quantity, 4),
        "unit": i.unit,
        "stored_on": i.stored_on,
        "location": i.location,
        "days_stored": max(0, (date.today() - date.fromisoformat(i.stored_on)).days),
    }


@app.post("/api/pantry", status_code=201)
def add_pantry(
    data: PantryInput,
    user: User = Depends(current_user),
    db: Session = Depends(database),
):
    i = PantryItem(
        user_id=user.id, **{**data.model_dump(), "stored_on": str(data.stored_on)}
    )
    db.add(i)
    db.flush()
    return pantry_dict(i)


class PantryBatch(BaseModel):
    rows: list[PantryInput] = Field(min_length=1, max_length=50)
    request_key: str = Field(min_length=8, max_length=100)


@app.post("/api/pantry/batch")
def add_batch(
    data: PantryBatch,
    user: User = Depends(current_user),
    db: Session = Depends(database),
):
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    if db.scalar(
        select(PantryImport).where(
            PantryImport.user_id == user.id,
            PantryImport.request_key == data.request_key,
        )
    ):
        return {"ok": True, "already_recorded": True}
    for row in data.rows:
        db.add(
            PantryItem(
                user_id=user.id, **{**row.model_dump(), "stored_on": str(row.stored_on)}
            )
        )
    db.add(PantryImport(user_id=user.id, request_key=data.request_key))
    return {"ok": True, "already_recorded": False}


@app.patch("/api/pantry/{item_id}")
def edit_pantry(
    item_id: int,
    data: PantryInput,
    user: User = Depends(current_user),
    db: Session = Depends(database),
):
    i = db.scalar(
        select(PantryItem)
        .where(PantryItem.id == item_id, PantryItem.user_id == user.id)
        .with_for_update()
    )
    if not i:
        raise HTTPException(404, "Pantry item not found.")
    for key, value in data.model_dump().items():
        setattr(i, key, str(value) if key == "stored_on" else value)
    return pantry_dict(i)


@app.delete("/api/pantry/{item_id}")
def delete_pantry(
    item_id: int, user: User = Depends(current_user), db: Session = Depends(database)
):
    i = db.scalar(
        select(PantryItem)
        .where(PantryItem.id == item_id, PantryItem.user_id == user.id)
        .with_for_update()
    )
    if not i:
        raise HTTPException(404, "Pantry item not found.")
    db.delete(i)
    return {"ok": True}


def pantry(db, user_id, lock=False):
    q = (
        select(PantryItem)
        .where(PantryItem.user_id == user_id, PantryItem.quantity > 1e-8)
        .order_by(PantryItem.stored_on, PantryItem.id)
    )
    return list(db.scalars(q.with_for_update() if lock else q))


def find_recipe(db, user_id, recipe_id):
    builtin = next((r for r in RECIPES if r["id"] == recipe_id), None)
    if builtin:
        return {**builtin, "source": "curated"}
    row = db.scalar(
        select(GeneratedRecipe).where(
            GeneratedRecipe.id == recipe_id, GeneratedRecipe.user_id == user_id
        )
    )
    return {**json.loads(row.payload), "id": row.id} if row else None


def recipe_context(user, items):
    return {
        "pantry": [
            {
                "name": i.name,
                "quantity": round(i.quantity, 4),
                "unit": i.unit,
                "days_stored": max(
                    0, (date.today() - date.fromisoformat(i.stored_on)).days
                ),
            }
            for i in items
        ],
        "preferences": {
            "servings": user.servings,
            "diet": user.diet,
            "max_minutes": user.max_minutes,
        },
    }


def recipe_context_hash(context, model):
    return hashlib.sha256(
        json.dumps(
            {"context": context, "model": model, "prompt_version": 3},
            sort_keys=True,
        ).encode()
    ).hexdigest()


def recipes_for(user, items, db):
    try:
        current_hash = recipe_context_hash(
            recipe_context(user, items), local_ai.model_name()
        )
    except local_ai.LocalAIError:
        current_hash = None
    stored = list(
        db.scalars(
            select(GeneratedRecipe)
            .where(GeneratedRecipe.user_id == user.id)
            .order_by(GeneratedRecipe.created_at.desc())
            .limit(12)
        )
    )
    sources = [{**r, "source": "curated"} for r in RECIPES] + [
        {
            **json.loads(r.payload),
            "id": r.id,
            "created_at": r.created_at,
            "matches_current_context": (
                json.loads(r.payload).get("context_key", r.context_hash) == current_hash
            ),
        }
        for r in stored
    ]
    result = [match_recipe(r, items, user.servings) for r in sources]
    result = [
        r
        for r in result
        if r["minutes"] <= user.max_minutes
        and (
            user.diet == "All"
            or user.diet in r["tags"]
            or user.diet == "Vegetarian"
            and "Vegan" in r["tags"]
        )
    ]

    def age(r):
        return max(
            [
                max(0, (date.today() - date.fromisoformat(i.stored_on)).days)
                for i in items
                if any(g["name"] == i.name for g in r["ingredients"])
            ]
            or [0]
        )

    return sorted(result, key=lambda r: (-r["coverage"], -age(r), r["minutes"]))


@app.get("/api/recipes")
def get_recipes(user: User = Depends(current_user), db: Session = Depends(database)):
    return recipes_for(user, pantry(db, user.id), db)


@app.get("/api/recipes/library/search")
def search_library(
    query: str, by: str = "ingredient", user: User = Depends(current_user)
):
    try:
        return recipe_library.search(query, by)
    except recipe_library.LibraryError as exc:
        raise HTTPException(exc.status, str(exc)) from exc


@app.get("/api/recipes/library/{identifier}")
def library_detail(identifier: str, user: User = Depends(current_user)):
    try:
        return recipe_library.detail(identifier)
    except recipe_library.LibraryError as exc:
        raise HTTPException(exc.status, str(exc)) from exc


class GenerationInput(BaseModel):
    inspiration_id: Optional[str] = Field(default=None, pattern=r"^\d{1,12}$")


@app.post("/api/recipes/generate")
def generate_dinner(
    data: Optional[GenerationInput] = None,
    user: User = Depends(current_user),
    db: Session = Depends(database),
):
    inspiration = None
    if data and data.inspiration_id:
        # Release the initial mutation lock while fetching public recipe data.
        db.commit()
        try:
            inspiration = recipe_library.detail(data.inspiration_id)
        except recipe_library.LibraryError as exc:
            raise HTTPException(exc.status, str(exc)) from exc
        if DATABASE.startswith("sqlite"):
            db.execute(text("BEGIN IMMEDIATE"))
        db.refresh(user)
    items = pantry(db, user.id)
    if len(items) < 2:
        raise HTTPException(
            400,
            "Add at least two pantry ingredients before asking local AI for a dinner idea.",
        )
    if len(items) > 80:
        raise HTTPException(
            400, "The local demo supports up to 80 pantry entries for AI generation."
        )
    context = recipe_context(user, items)
    try:
        selected_model = local_ai.model_name()
    except local_ai.LocalAIError as exc:
        raise HTTPException(exc.status, str(exc)) from exc
    base_hash = recipe_context_hash(context, selected_model)
    if inspiration:
        context["inspiration"] = {
            "id": inspiration["id"],
            "name": inspiration["name"],
            "ingredients": inspiration["ingredients"][:12],
            "instructions": inspiration["instructions"][:1000],
        }
    context_hash = recipe_context_hash(context, selected_model)
    cached = list(
        db.scalars(
            select(GeneratedRecipe).where(
                GeneratedRecipe.user_id == user.id,
                GeneratedRecipe.context_hash == context_hash,
                GeneratedRecipe.created_at > now() - 900,
            )
        )
    )
    if cached:
        return {"cached": True, "count": len(cached), "ids": [r.id for r in cached]}
    # Per-account DB lock prevents competing requests from loading the model twice.
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    budget = db.get(GenerationBudget, user.id)
    if budget and (budget.busy_until > now() or budget.last_attempt > now() - 10):
        raise HTTPException(
            429, "Local AI is already working or cooling down. Please wait a moment."
        )
    if not budget:
        budget = GenerationBudget(
            user_id=user.id, last_attempt=now(), busy_until=now() + 200
        )
        db.add(budget)
    else:
        budget.last_attempt = now()
        budget.busy_until = now() + 200
    # Release the database transaction during the slow local model call.
    db.commit()
    try:
        generated = local_ai.generate(context, items)
    except local_ai.LocalAIError as exc:
        budget.busy_until = 0
        db.commit()
        raise HTTPException(exc.status, str(exc)) from exc
    ids = []
    for recipe in generated:
        recipe["generated_for"] = context["preferences"]
        recipe["context_key"] = base_hash
        if inspiration:
            recipe["inspired_by"] = {
                "id": inspiration["id"],
                "name": inspiration["name"],
                "url": inspiration["source_url"],
            }
        recipe_id = "ai-" + uuid.uuid4().hex
        ids.append(recipe_id)
        db.add(
            GeneratedRecipe(
                id=recipe_id,
                user_id=user.id,
                context_hash=context_hash,
                payload=json.dumps(recipe),
                created_at=now(),
            )
        )
    budget.busy_until = 0
    db.flush()
    return {"cached": False, "count": len(ids), "ids": ids}


def take(items, name, quantity, unit):
    if amount_available(items, name, unit) + 1e-8 < quantity:
        raise HTTPException(
            409, f"Not enough {name}. Refresh your pantry and try again."
        )
    reserved = []
    for i in items:
        if i.name != name:
            continue
        avail = convert(i.quantity, i.unit, unit)
        if not avail:
            continue
        used = min(avail, quantity)
        original = convert(used, unit, i.unit)
        if used > 1e-8:
            i.quantity = max(0, i.quantity - original)
            reserved.append(
                {
                    "name": name,
                    "quantity": original,
                    "unit": i.unit,
                    "stored_on": i.stored_on,
                    "location": i.location,
                }
            )
            quantity -= used
        if quantity < 1e-8:
            break
    return reserved


class CookInput(BaseModel):
    request_key: str = Field(min_length=8, max_length=100)


@app.post("/api/recipes/{recipe_id}/cook")
def cook_recipe(
    recipe_id: str,
    data: CookInput,
    user: User = Depends(current_user),
    db: Session = Depends(database),
):
    # Lock account before idempotency lookup, so repeated concurrent clicks cannot double-deduct.
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    existing = db.scalar(
        select(Cook).where(
            Cook.user_id == user.id, Cook.request_key == data.request_key
        )
    )
    if existing:
        if existing.recipe_id != recipe_id:
            raise HTTPException(409, "This action key belongs to another meal.")
        return {"ok": True, "already_recorded": True}
    recipe = find_recipe(db, user.id, recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found.")
    items = pantry(db, user.id, True)
    matched = match_recipe(recipe, items, user.servings)
    if not matched["ready"]:
        raise HTTPException(
            409, "Collect the missing ingredients before marking this meal cooked."
        )
    for ing in matched["ingredients"]:
        take(items, ing["name"], ing["quantity"], ing["unit"])
    db.add(
        Cook(
            user_id=user.id,
            recipe_id=recipe_id,
            request_key=data.request_key,
            created_at=now(),
        )
    )
    return {"ok": True, "already_recorded": False}


class RequestInput(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    quantity: float = Field(gt=0, le=100000, allow_inf_nan=False)
    unit: str
    community_id: Optional[int] = None
    friend_id: Optional[int] = None
    recipe_id: Optional[str] = None
    minutes: int = Field(default=30, ge=5, le=1440)
    note: str = Field(default="", max_length=400)

    @model_validator(mode="after")
    def valid(self):
        self.name = " ".join(self.name.lower().strip().split())
        if not self.name or self.unit not in UNITS:
            raise ValueError("Enter an ingredient and supported unit.")
        if (self.community_id is None) == (self.friend_id is None):
            raise ValueError("Choose one community or friend.")
        return self


def member(db, user_id, community_id):
    return bool(
        db.scalar(
            select(Membership.id).where(
                Membership.user_id == user_id, Membership.community_id == community_id
            )
        )
    )


def is_friend(db, user_id, other):
    return bool(
        db.scalar(
            select(Friend.id).where(
                Friend.user_id == user_id, Friend.friend_id == other
            )
        )
    )


def can_view(db, user, req):
    return (
        user.id in (req.user_id, req.friend_id, req.provider_id)
        or req.community_id
        and member(db, user.id, req.community_id)
    )


def request_visible(db, user, request_id, lock=False):
    q = select(IngredientRequest).where(IngredientRequest.id == request_id)
    req = db.scalar(q.with_for_update() if lock else q)
    if not req or not can_view(db, user, req):
        raise HTTPException(404, "Request not found.")
    return req


def request_status(r):
    return "expired" if r.status == "pending" and r.deadline <= now() else r.status


def request_dict(db, r, user):
    declines = list(
        db.scalars(select(Decline.user_id).where(Decline.request_id == r.id))
    )
    return {
        "id": r.id,
        "name": r.name,
        "quantity": r.quantity,
        "unit": r.unit,
        "user_id": r.user_id,
        "requester": db.get(User, r.user_id).name,
        "community_id": r.community_id,
        "community": db.get(Community, r.community_id).name if r.community_id else None,
        "friend_id": r.friend_id,
        "friend": db.get(User, r.friend_id).name if r.friend_id else None,
        "provider_id": r.provider_id,
        "provider": db.get(User, r.provider_id).name if r.provider_id else None,
        "deadline": r.deadline,
        "created_at": r.created_at,
        "status": request_status(r),
        "note": r.note,
        "recipe_id": r.recipe_id,
        "declined_by_me": user.id in declines,
        "decline_count": len(declines),
    }


@app.post("/api/requests", status_code=201)
def create_request(
    data: RequestInput,
    user: User = Depends(current_user),
    db: Session = Depends(database),
):
    if data.recipe_id and not find_recipe(db, user.id, data.recipe_id):
        raise HTTPException(404, "Recipe not found.")
    if data.community_id and not member(db, user.id, data.community_id):
        raise HTTPException(403, "Join that community first.")
    if data.friend_id and not is_friend(db, user.id, data.friend_id):
        raise HTTPException(403, "Choose a connected friend.")
    req = IngredientRequest(
        user_id=user.id,
        **data.model_dump(exclude={"minutes"}),
        deadline=now() + data.minutes * 60,
        created_at=now(),
    )
    db.add(req)
    db.flush()
    return request_dict(db, req, user)


@app.post("/api/requests/{request_id}/accept")
def accept_request(
    request_id: int, user: User = Depends(current_user), db: Session = Depends(database)
):
    r = request_visible(db, user, request_id, True)
    if r.user_id == user.id:
        raise HTTPException(403, "You cannot fulfill your own request.")
    if request_status(r) != "pending":
        raise HTTPException(409, "This request is no longer open.")
    if r.friend_id and r.friend_id != user.id:
        raise HTTPException(403, "This request is for another friend.")
    items = pantry(db, user.id, True)
    reserved = take(items, r.name, r.quantity, r.unit)
    r.reserved = json.dumps(reserved)
    r.status = "accepted"
    r.provider_id = user.id
    return request_dict(db, r, user)


@app.post("/api/requests/{request_id}/decline")
def decline_request(
    request_id: int, user: User = Depends(current_user), db: Session = Depends(database)
):
    r = request_visible(db, user, request_id, True)
    if r.user_id == user.id:
        raise HTTPException(403, "Cancel your own request instead.")
    if request_status(r) != "pending":
        raise HTTPException(409, "This request is no longer open.")
    if not db.scalar(
        select(Decline.id).where(Decline.request_id == r.id, Decline.user_id == user.id)
    ):
        db.add(Decline(request_id=r.id, user_id=user.id))
    if r.friend_id:
        r.status = "declined"
    db.flush()
    return request_dict(db, r, user)


@app.post("/api/requests/{request_id}/complete")
def complete_request(
    request_id: int, user: User = Depends(current_user), db: Session = Depends(database)
):
    r = request_visible(db, user, request_id, True)
    if user.id != r.user_id:
        raise HTTPException(403, "Only the requester can confirm pickup.")
    if r.status == "completed":
        return {"ok": True, "already_recorded": True}
    if r.status != "accepted":
        raise HTTPException(409, "A provider must accept before you confirm pickup.")
    # Transfer original batches and dates; storage age never resets just because food changed hands.
    for batch in json.loads(r.reserved):
        db.add(PantryItem(user_id=user.id, **batch))
    r.status = "completed"
    r.completed_at = now()
    r.reserved = "[]"
    return {"ok": True, "already_recorded": False}


@app.post("/api/requests/{request_id}/cancel")
def cancel_request(
    request_id: int, user: User = Depends(current_user), db: Session = Depends(database)
):
    r = request_visible(db, user, request_id, True)
    if user.id not in (r.user_id, r.provider_id):
        raise HTTPException(403, "Only the requester or provider can cancel.")
    if r.status == "cancelled":
        return {"ok": True}
    if r.status not in ("pending", "accepted"):
        raise HTTPException(409, "This request is already closed.")
    if r.status == "accepted":
        for batch in json.loads(r.reserved):
            db.add(PantryItem(user_id=r.provider_id, **batch))
    r.status = "cancelled"
    r.reserved = "[]"
    return {"ok": True}


class CommunityInput(BaseModel):
    name: str = Field(min_length=2, max_length=50)

    @field_validator("name")
    @classmethod
    def clean(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Enter at least two characters.")
        return v.strip()


@app.post("/api/communities", status_code=201)
def create_community(
    data: CommunityInput,
    user: User = Depends(current_user),
    db: Session = Depends(database),
):
    c = Community(name=data.name, invite_code=secrets.token_urlsafe(9), color="green")
    db.add(c)
    db.flush()
    db.add(Membership(user_id=user.id, community_id=c.id))
    return {"id": c.id, "invite_code": c.invite_code}


class CodeInput(BaseModel):
    code: str = Field(min_length=3, max_length=100)


@app.post("/api/communities/join")
def join_community(
    data: CodeInput, user: User = Depends(current_user), db: Session = Depends(database)
):
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    c = db.scalar(select(Community).where(Community.invite_code == data.code.strip()))
    if not c:
        raise HTTPException(404, "Invite code not found.")
    if not member(db, user.id, c.id):
        db.add(Membership(user_id=user.id, community_id=c.id))
    return {"ok": True, "id": c.id}


@app.post("/api/friends/invite")
def friend_invite(user: User = Depends(current_user), db: Session = Depends(database)):
    code = secrets.token_urlsafe(12)
    db.add(FriendInvite(code=code, user_id=user.id, expires_at=now() + 86400))
    return {"code": code}


@app.post("/api/friends/join")
def friend_join(
    data: CodeInput, user: User = Depends(current_user), db: Session = Depends(database)
):
    invite = db.scalar(
        select(FriendInvite)
        .where(FriendInvite.code == data.code.strip())
        .with_for_update()
    )
    if not invite or invite.expires_at < now():
        raise HTTPException(404, "Friend invite not found or expired.")
    if invite.user_id == user.id:
        raise HTTPException(400, "Share your invite with another sample account.")
    for a, b in [(user.id, invite.user_id), (invite.user_id, user.id)]:
        if not is_friend(db, a, b):
            db.add(Friend(user_id=a, friend_id=b))
    db.delete(invite)
    return {"ok": True}


class MessageInput(BaseModel):
    body: str = Field(min_length=1, max_length=1000)
    community_id: Optional[int] = None
    request_id: Optional[int] = None

    @model_validator(mode="after")
    def check(self):
        self.body = self.body.strip()
        if not self.body:
            raise ValueError("Write a message first.")
        if (self.community_id is None) == (self.request_id is None):
            raise ValueError("Choose one conversation.")
        return self


def message_permission(db, user, community_id, request_id):
    if community_id and not member(db, user.id, community_id):
        raise HTTPException(403, "This community is private.")
    if request_id:
        r = request_visible(db, user, request_id)
        if r.status not in ("accepted", "completed") or user.id not in (
            r.user_id,
            r.provider_id,
        ):
            raise HTTPException(
                403, "Pickup chat is only for the requester and accepted provider."
            )


@app.post("/api/messages", status_code=201)
def send_message(
    data: MessageInput,
    user: User = Depends(current_user),
    db: Session = Depends(database),
):
    message_permission(db, user, data.community_id, data.request_id)
    db.add(Message(user_id=user.id, **data.model_dump(), created_at=now()))
    return {"ok": True}


@app.get("/api/messages")
def read_messages(
    community_id: Optional[int] = None,
    request_id: Optional[int] = None,
    user: User = Depends(current_user),
    db: Session = Depends(database),
):
    if (community_id is None) == (request_id is None):
        raise HTTPException(400, "Choose one conversation.")
    message_permission(db, user, community_id, request_id)
    q = (
        select(Message).where(Message.community_id == community_id)
        if community_id
        else select(Message).where(Message.request_id == request_id)
    )
    msgs = list(
        db.scalars(q.order_by(Message.created_at.desc(), Message.id.desc()).limit(100))
    )[::-1]
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "name": db.get(User, m.user_id).name,
            "body": m.body,
            "created_at": m.created_at,
        }
        for m in msgs
    ]


class Preferences(BaseModel):
    servings: int = Field(ge=1, le=8)
    diet: str
    max_minutes: int = Field(ge=10, le=120)

    @field_validator("diet")
    @classmethod
    def valid_diet(cls, v):
        if v not in ("All", "Vegetarian", "Vegan", "Gluten-free"):
            raise ValueError("Choose a supported preference.")
        return v


@app.patch("/api/settings")
def settings(
    data: Preferences,
    user: User = Depends(current_user),
    db: Session = Depends(database),
):
    for k, v in data.model_dump().items():
        setattr(user, k, v)
    return {"ok": True}


@app.get("/api/state")
def state(user: User = Depends(current_user), db: Session = Depends(database)):
    ids = list(
        db.scalars(select(Membership.community_id).where(Membership.user_id == user.id))
    )
    cs = list(db.scalars(select(Community).where(Community.id.in_(ids))))
    rs = list(
        db.scalars(
            select(IngredientRequest)
            .where(
                or_(
                    IngredientRequest.user_id == user.id,
                    IngredientRequest.friend_id == user.id,
                    IngredientRequest.provider_id == user.id,
                    IngredientRequest.community_id.in_(ids),
                )
            )
            .order_by(IngredientRequest.created_at.desc())
            .limit(200)
        )
    )
    friend_ids = list(
        db.scalars(select(Friend.friend_id).where(Friend.user_id == user.id))
    )
    peer_ids = (
        set(
            db.scalars(
                select(Membership.user_id).where(Membership.community_id.in_(ids))
            )
        )
        | set(friend_ids)
        | {user.id}
    )
    leaders = []
    for uid in peer_ids:
        visible_completed = [
            r for r in rs if r.status == "completed" and r.provider_id == uid
        ]
        leaders.append(
            {"id": uid, "name": db.get(User, uid).name, "count": len(visible_completed)}
        )
    leaders.sort(key=lambda l: (-l["count"], l["name"]))
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "color": user.color,
            "servings": user.servings,
            "diet": user.diet,
            "max_minutes": user.max_minutes,
        },
        "demo": True,
        "pantry": [pantry_dict(i) for i in pantry(db, user.id)],
        "communities": [
            {
                "id": c.id,
                "name": c.name,
                "invite_code": c.invite_code,
                "color": c.color,
                "members": db.scalar(
                    select(func.count())
                    .select_from(Membership)
                    .where(Membership.community_id == c.id)
                ),
            }
            for c in cs
        ],
        "friends": [{"id": uid, "name": db.get(User, uid).name} for uid in friend_ids],
        "requests": [request_dict(db, r, user) for r in rs],
        "leaderboard": leaders,
        "meals_cooked": db.scalar(
            select(func.count()).select_from(Cook).where(Cook.user_id == user.id)
        ),
        "shared_count": sum(
            r.status == "completed" and r.provider_id == user.id for r in rs
        ),
        "recipes": recipes_for(user, pantry(db, user.id), db),
        "ai": local_ai.status(),
        "units": list(UNITS),
    }


@app.get("/api/health")
def health():
    return {"ok": True, "mode": "local sample accounts", "schema": 2}


DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Unknown API route.")
        return FileResponse(DIST / "index.html")
