"""Curated demonstration recipes. Coverage is quantity-aware, not AI-generated."""

RECIPES = [
    {
        "id": "tomato-pasta",
        "name": "Sunday tomato pasta",
        "subtitle": "A little comfort, already in your pantry.",
        "category": "THE EVERYDAY FAVORITE",
        "minutes": 20,
        "servings": 2,
        "image": "pasta",
        "tags": ["Vegetarian"],
        "ingredients": [
            {"name": "pasta", "quantity": 200, "unit": "g"},
            {"name": "tomatoes", "quantity": 300, "unit": "g"},
            {"name": "olive oil", "quantity": 20, "unit": "ml"},
            {"name": "basil", "quantity": 5, "unit": "g"},
            {"name": "garlic", "quantity": 1, "unit": "clove"},
        ],
        "steps": [
            "Bring a large pot of salted water to a boil. Cook the pasta according to the packet, reserving a cup of cooking water.",
            "Warm the olive oil in a pan. Add the finely sliced garlic and stir gently for a minute.",
            "Add chopped tomatoes. Simmer for 10 minutes until soft and saucy.",
            "Toss in the pasta with a splash of cooking water. Tear over the basil and serve.",
        ],
    },
    {
        "id": "tomato-toast",
        "name": "Garden tomato toast",
        "subtitle": "Five ingredients. One very good lunch.",
        "category": "READY WHEN YOU ARE",
        "minutes": 10,
        "servings": 2,
        "image": "toast",
        "tags": ["Vegan"],
        "ingredients": [
            {"name": "bread", "quantity": 2, "unit": "slice"},
            {"name": "tomatoes", "quantity": 150, "unit": "g"},
            {"name": "olive oil", "quantity": 10, "unit": "ml"},
            {"name": "basil", "quantity": 3, "unit": "g"},
            {"name": "lemon", "quantity": 0.5, "unit": "each"},
        ],
        "steps": [
            "Toast the bread until crisp and golden.",
            "Chop the tomatoes and toss with olive oil, torn basil and lemon juice.",
            "Spoon over the toast and enjoy straight away.",
        ],
    },
    {
        "id": "green-bowl",
        "name": "The feel-good green bowl",
        "subtitle": "Fresh greens, warm rice, a bright finish.",
        "category": "A FRESH START",
        "minutes": 25,
        "servings": 2,
        "image": "bowl",
        "tags": ["Vegan", "Gluten-free"],
        "ingredients": [
            {"name": "rice", "quantity": 150, "unit": "g"},
            {"name": "spinach", "quantity": 100, "unit": "g"},
            {"name": "lemon", "quantity": 0.5, "unit": "each"},
            {"name": "olive oil", "quantity": 15, "unit": "ml"},
            {"name": "chickpeas", "quantity": 150, "unit": "g"},
        ],
        "steps": [
            "Rinse rice, then cook using the packet's water ratio.",
            "Drain chickpeas and warm them in a pan with olive oil.",
            "Fold in spinach until just wilted.",
            "Serve over rice with a squeeze of lemon.",
        ],
    },
    {
        "id": "spinach-pasta",
        "name": "Lemony spinach pasta",
        "subtitle": "Your greens get their moment.",
        "category": "WEEKNIGHT HERO",
        "minutes": 15,
        "servings": 2,
        "image": "greens",
        "tags": ["Vegan"],
        "ingredients": [
            {"name": "pasta", "quantity": 200, "unit": "g"},
            {"name": "spinach", "quantity": 100, "unit": "g"},
            {"name": "olive oil", "quantity": 15, "unit": "ml"},
            {"name": "lemon", "quantity": 0.5, "unit": "each"},
            {"name": "garlic", "quantity": 1, "unit": "clove"},
        ],
        "steps": [
            "Cook pasta according to the packet and save some cooking water.",
            "Warm the oil and sliced garlic. Add spinach and let it wilt.",
            "Toss pasta with the greens, lemon juice and a little pasta water.",
        ],
    },
]

# No implicit count-to-weight conversions: one tomato is not a known number of grams.
UNITS = {
    "g": ("mass", 1),
    "kg": ("mass", 1000),
    "oz": ("mass", 28.349523125),
    "ml": ("volume", 1),
    "l": ("volume", 1000),
    "tsp": ("volume", 5),
    "tbsp": ("volume", 15),
    "each": ("each", 1),
    "clove": ("clove", 1),
    "slice": ("slice", 1),
}


def convert(quantity, source, target):
    if (
        source not in UNITS
        or target not in UNITS
        or UNITS[source][0] != UNITS[target][0]
    ):
        return None
    return quantity * UNITS[source][1] / UNITS[target][1]


def amount_available(items, name, unit):
    return sum(convert(i.quantity, i.unit, unit) or 0 for i in items if i.name == name)


def match_recipe(recipe, items, servings=2):
    lines = []
    for ing in recipe["ingredients"]:
        required = ing["quantity"] * servings / recipe["servings"]
        available = amount_available(items, ing["name"], ing["unit"])
        lines.append(
            {
                **ing,
                "quantity": round(required, 4),
                "available": round(available, 4),
                "missing": round(max(0, required - available), 4),
                "owned": available + 1e-8 >= required,
            }
        )
    covered = sum(i["owned"] for i in lines)
    return {
        **recipe,
        "servings": servings,
        "ingredients": lines,
        "coverage": round(100 * covered / len(lines)),
        "covered": covered,
        "total": len(lines),
        "ready": covered == len(lines),
    }
