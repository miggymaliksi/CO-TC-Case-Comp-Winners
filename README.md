# Savor

Good food. Shared. A local case-competition demo for pantry tracking, quantity-aware recipes, and private ingredient sharing.

## Run in VS Code

You need Python 3.9 or later (3.11+ recommended) and Node.js 22.12+ or 24+. Install them if missing, then reopen VS Code so it can find them.

1. Open this repository folder in VS Code using **File → Open Folder**.
2. Choose **Terminal → Run Task → Savor: Start local app**. Alternatively, open **Terminal → New Terminal** and enter:

   ```sh
   python3 run.py
   ```

   On Windows, use `python run.py`.
3. First launch installs the pinned Python packages, installs the locked interface packages, builds the interface, and opens **http://127.0.0.1:8000**. Internet access is needed for this first setup. Later launches reuse the local setup.
4. Keep the terminal open. Press **Ctrl+C** in it to stop Savor.

The first run creates `savor.db` in this folder. It stores only the local demo's records and is ignored by Git. Browser storage is not the database.

If port 8000 is already in use, stop the other Savor terminal, or copy `.env.example` to `.env` and set `SAVOR_PORT=8001`. Never commit `.env`.

## Try the complete demo

The app starts as **Alex**, with sample groceries. The top-right account button and the sidebar account selector switch between Alex, Jamie, and Sam. These are sample identities, not real logins.

1. Open **Recipe ideas → Sunday tomato pasta**. Alex has 80% of the ingredient lines in sufficient quantities; one clove of garlic is missing.
2. Click **Ask** next to garlic. Send the one-clove request to **PBL** with a 30-minute deadline.
3. Switch to **Jamie**. Open **My community → Requests → I can share**. The clove is reserved and removed from Jamie's available pantry.
4. Open **Pickup chat** to coordinate. Only the requester and accepted provider can read it.
5. Switch to **Alex** and click **Confirm pickup**. The reserved ingredient is transferred once, retaining its original storage date.
6. Open the pasta recipe again. It now shows 100%. After cooking, click **I cooked this**. Quantities are deducted once and **Our impact** records the meal.

For the fallback, make a direct request to Jamie and decline it as Jamie. Alex can then choose **Find a pantry-only recipe**. A pending request also expires at its real deadline; it cannot be accepted after that time. A community member passing leaves the request open for others. Accepted reservations stay held until pickup or cancellation, even after the original deadline, so food is not silently returned while people arrange pickup. Either participant can cancel before completion and return the reserved stock.

Community chat is available by clicking a community card. Create a private group or join using an invite code. A community's invite code is shown only to its members. Connect sample friends using one-use 24-hour invite codes. In-app updates refresh every eight seconds and an open chat every four seconds.

## What works and what is still a demo

| Working locally | Still needs integration or later work |
| --- | --- |
| Pantry add/edit/remove, storage age, durable database | Production identity / Google sign-in |
| Four curated recipes, quantity/unit matching, scaled servings and dietary/time filters | Live AI recipe generation |
| Private communities, friend invites, exact-quantity requests, accept/pass/cancel | Contacts or proximity discovery |
| Inventory reservation, confirmed pickup, cooking records and duplicate protection | Live AI receipt extraction |
| Private pickup and community chat; in-app request status updates | Scheduled morning delivery and external push notifications |
| Leaderboard based on confirmed visible demo exchanges | Shared calendar, games and prizes |
| Editable sample receipt with atomic import | Measured food-weight or dollar-savings estimates |

All recipes, illustrations, initial messages, accounts, and initial groceries are sample content. The receipt screen explicitly labels its editable sample and does not upload or scan an image. “Eats of the Day” shows current curated matches; there is no background scheduler. No savings or user-adoption claims are fabricated. The 9,000-request figure is the team's aspiration, not achieved impact.

**Scope:** storage age instead of predicted expiration. No food-safety classification, payments, buying/selling, deliveries, or public social feed.

## Technology and data

- **Frontend:** React + Vite, with original vector food illustrations and responsive navigation. Google Fonts is optional; system fonts work offline.
- **Backend:** FastAPI + SQLAlchemy, with input validation and authorization on the server.
- **Database:** SQLite by default, so local setup needs no database account. PostgreSQL can be selected with `SAVOR_DATABASE_URL=postgresql+psycopg://…`. That configuration is supported by the models but has not been tested against a running PostgreSQL instance.
- **Schema:** version 1 initializes new databases and seeds three sample accounts. There is no automatic upgrade system for later schema changes; add an explicit migration before evolving an existing database.
- **Sessions:** random, expiring server-side session cookies, HttpOnly and SameSite=Strict. Mutations reject foreign browser origins; host checks and the launcher limit this sample-account build to local use. Demo identity switching intentionally allows access to all three *sample* accounts. Do not use real personal data or deploy this build as production authentication.
- **Consistency:** SQLite serializes write transactions. PostgreSQL paths use row locks. Acceptance reserves existing quantities; completion/cancellation are repeat-safe, and cooking/import requests use idempotency keys. Confirmed transfers keep original storage dates and units.
- **Coverage:** number of ingredient lines with sufficient compatible quantities divided by all ingredient lines. Recommended recipes require at least 80%; pantry-only recipes require 100%. Mass converts between grams/kg/oz, volume between ml/l/tsp/tbsp; count units match themselves. The app never guesses the weight of “one tomato.”

The API contract, source precedence, proposed choices, and build sequence are in [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md). Collaboration rules remain in [COxTC agent.md](COxTC%20agent.md).

## Checks and development

After first launch has prepared the environment:

```sh
.venv/bin/python -m pytest backend/test_api.py -q
cd frontend
npm run build
```

On Windows, use `.venv\Scripts\python.exe` for the test command.

To develop with live interface updates, run the API in one terminal and the interface in another:

```sh
# Repository root
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Second terminal
cd frontend
npm run dev
```

Use the Vite URL printed by the second terminal. For a custom API port, update the development proxy in `frontend/vite.config.js`.

The focused tests cover persistence, ownership/privacy, quantities and units, serving scaling, missing ingredients, concurrent acceptance, expiry/decline fallback, reservation return, atomic receipt import, friend invites, private pickup chat, and duplicate pickup/cooking.

## Share changes safely

Use a feature branch, push it, and open a pull request. Another teammate must review before merging, per the repository instructions. A push does not deploy this local app. Do not commit `.env`, database files, `.venv`, `node_modules`, or generated builds.

## Product sources

- [TEAM 2 NEW PRD, October 29](https://drive.google.com/file/d/18ur-S052I7z5poal1AYf3mKzd3Dqa37Z/view)
- [Savor case notes, latest October 31 decisions](https://docs.google.com/document/d/1QhIG_b4e-CjrfGD__gl35DrTMzZUfslswP6zDRAVLYA/edit)
- [Earlier technical plan](https://docs.google.com/document/d/1gKUdYAZpKu_ehvpsNAcMWzh6NwebzQ006EDT5gBr5-o/edit)

Latest scope decisions override older expiration-focused drafts. Source documents remain unchanged.
