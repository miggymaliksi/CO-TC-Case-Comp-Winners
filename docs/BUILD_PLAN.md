# Savor demo build plan

## Sources and scope

The October 29 NEW PRD and the latest October 31 Savor case notes take precedence over earlier expiration-focused drafts. Core flow: pantry → recipe → exact missing quantity → private community request → accept → exchange → cook. Track days stored; do not predict expiration or food safety.

This branch starts from a repository containing only `COxTC agent.md`. No open PRs or issues were found during the initial check. Shared setup, routing, schema, and dependencies are necessary coordination points because there is no application yet. No teammate was messaged and no changes were pushed, merged, or deployed.

## Proposed implementation

- React/Vite frontend with a warm cream, forest green, and citrus visual system. Pantry, daily recipes, community requests/chat, and activity.
- FastAPI service using SQLAlchemy. SQLite makes the local demo self-contained; the same models support PostgreSQL through `SAVOR_DATABASE_URL`. Schema versioning records the initial schema and the additive version 2 local-AI tables. Future schema changes need explicit migrations.
- Sample accounts only, random server-side session cookies, local-only demo mode. No passwords, contact import, or location collection. Production Google sign-in is a future integration, not a working feature of this demo.
- Curated, clearly labeled recipes with deterministic ingredient/quantity matching. Receipt-image extraction and scheduled external notifications remain unconfigured. Optional live recipe generation now uses a downloaded Ollama/Qwen3 model on this computer, with no cloud API requests. Manual grocery entry always works.

## Data and contract

Users own pantry records; communities have memberships and private invite codes. Requests reference a requester and a community or friend, ingredient, amount/unit, deadline, status, and optional provider. Messages belong to a community or a request. Session records expire. Exchange and cooking records make inventory updates idempotent. Activity records drive in-app notifications and the demo leaderboard.

`POST /api/demo/session` chooses a sample account; `GET /api/state` returns only that account's visible data. Pantry uses `POST/PATCH/DELETE /api/pantry`. Recipes use `GET /api/recipes` and `POST /api/recipes/{id}/cook`. Requests use `POST /api/requests` plus `accept`, `decline`, `complete`, and `cancel` actions. Community create/join and messages are separate endpoints. All mutations validate input and membership on the server. State-changing requests reject foreign browser origins and use same-site cookies.

Coverage counts fully available ingredient lines divided by recipe ingredient lines, using compatible mass/volume/count units and current quantities. A partial quantity is missing its exact shortfall. Recommendations start at 80% coverage; a separate pantry-only fallback requires 100%. Storage age is a ranking tie-breaker, not a safety claim.

## Slices and checks

1. Persistent pantry CRUD, ownership checks, positive quantities and date/unit validation.
2. Quantity-aware recipe cards/detail, 80% recommendation threshold, 100% fallback, transactional cook deduction with idempotency keys.
3. Private requests and chat, deadline/eligibility checks, serialized acceptance and exchange updates, duplicate completion protection.
4. Community create/join, friend connections, settings, activity and leaderboard based on confirmed demo exchanges.
5. Responsive interface, empty/error states, seeded walkthrough, focused API tests, production build and browser checks.

Sample walkthrough: Alex has pasta, tomatoes, olive oil and basil; Jamie can supply one clove garlic. Alex requests it from PBL, Jamie accepts, Alex confirms pickup and cooks. A declined/expired request offers tomato toast using pantry-only ingredients. All sample accounts and records are labeled.

Excluded: buying/selling, payments, deliveries, public posts, predicted expiration, invented impact statistics. Shared calendars, games/prizes, production identity, AI services and scheduled delivery need later configuration and review.

## Local AI addition

The user chose free on-device generation instead of a paid API. New generated-recipe and generation-budget tables are added through migration 2. The backend sends only pantry quantities/age and preferences to a fixed loopback Ollama endpoint, validates structured output, computes coverage independently, caches matching results for 15 minutes, and isolates generated history by user. No OpenAI key is loaded by the app. The launcher runs a local-only service when the runtime is available; downloading the model is a separate explicit setup task. See `TECHNICAL_RUNDOWN.md` for a presentation explanation.
