"""TheMealDB's public educational V1 API. No account, paid key, or cloud AI."""

from copy import deepcopy
import re
from threading import Lock
import time
from urllib.parse import urlparse

import httpx

BASE = "https://www.themealdb.com/api/json/v1/1"
CACHE_SECONDS = 900
_cache = {}
_lock = Lock()


class LibraryError(Exception):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


def _fetch(endpoint, params):
    key = (endpoint, tuple(sorted(params.items())))
    with _lock:
        cached = _cache.get(key)
        if cached and cached[0] > time.monotonic():
            return deepcopy(cached[1]), True
    try:
        response = httpx.get(
            f"{BASE}/{endpoint}",
            params=params,
            timeout=12,
            trust_env=False,
            follow_redirects=False,
        )
        response.raise_for_status()
        if len(response.content) > 2_000_000:
            raise ValueError("Recipe response is too large.")
        data = response.json()
        if not isinstance(data, dict) or not isinstance(
            data.get("meals"), (list, type(None))
        ):
            raise ValueError("Unexpected recipe data.")
    except (httpx.HTTPError, ValueError) as exc:
        raise LibraryError(
            "The recipe library is unavailable. Try again shortly; your pantry and saved ideas are unchanged."
        ) from exc
    with _lock:
        if len(_cache) >= 64:
            _cache.pop(next(iter(_cache)))
        _cache[key] = (time.monotonic() + CACHE_SECONDS, deepcopy(data))
    return data, False


def _summary(meal):
    identifier = str(meal.get("idMeal", ""))
    if not re.fullmatch(r"\d{1,12}", identifier):
        raise ValueError("Invalid meal identifier.")
    name = str(meal.get("strMeal") or "").strip()[:160]
    if not name:
        raise ValueError("Missing recipe name.")
    image = str(meal.get("strMealThumb") or "")
    url = urlparse(image)
    if not (
        url.scheme == "https"
        and url.netloc == "www.themealdb.com"
        and url.path.startswith("/images/media/meals/")
        and re.search(r"\.(jpg|jpeg|png)$", url.path, re.I)
        and not url.query
    ):
        image = None
    return {
        "id": identifier,
        "name": name,
        "image_url": image + "/small" if image else None,
        "source": "TheMealDB",
        "source_url": f"https://www.themealdb.com/meal/{identifier}",
        "category": str(meal.get("strCategory") or "")[:80],
        "cuisine": str(meal.get("strArea") or "")[:80],
    }


def search(query, by="ingredient"):
    query = " ".join(query.strip().split())
    if not 2 <= len(query) <= 60 or by not in ("ingredient", "name"):
        raise LibraryError(
            "Enter an ingredient or meal name between 2 and 60 characters.", 422
        )
    endpoint, params = (
        ("filter.php", {"i": query.replace(" ", "_")})
        if by == "ingredient"
        else ("search.php", {"s": query})
    )
    data, cached = _fetch(endpoint, params)
    recipes = []
    for meal in (data.get("meals") or [])[:12]:
        try:
            recipes.append(_summary(meal))
        except (AttributeError, ValueError, TypeError):
            continue
    return {
        "recipes": recipes,
        "provider": "TheMealDB",
        "cached": cached,
        "query": query,
    }


def detail(identifier):
    if not re.fullmatch(r"\d{1,12}", str(identifier)):
        raise LibraryError("Recipe not found.", 404)
    data, cached = _fetch("lookup.php", {"i": str(identifier)})
    meal = next(
        (
            m
            for m in data.get("meals") or []
            if isinstance(m, dict) and str(m.get("idMeal")) == str(identifier)
        ),
        None,
    )
    if not meal:
        raise LibraryError("Recipe not found.", 404)
    try:
        recipe = _summary(meal)
    except (AttributeError, ValueError, TypeError) as exc:
        raise LibraryError("This library recipe could not be read.") from exc
    recipe.update(
        ingredients=[
            {
                "name": str(meal[f"strIngredient{i}"]).strip()[:120],
                "measure": str(meal.get(f"strMeasure{i}") or "").strip()[:120],
            }
            for i in range(1, 21)
            if str(meal.get(f"strIngredient{i}") or "").strip()
        ],
        instructions=str(meal.get("strInstructions") or "").strip()[:12000],
        cached=cached,
    )
    return recipe
