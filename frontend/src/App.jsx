import React, { useEffect, useRef, useState } from "react";
import {
  Leaf,
  LayoutDashboard,
  ShoppingBasket,
  Users,
  Activity,
  Settings,
  Plus,
  ArrowUpRight,
  ArrowRight,
  Clock,
  ChevronRight,
  Check,
  Search,
  X,
  Trash2,
  Camera,
  MessageCircle,
  Send,
  CheckCircle2,
  ArrowLeft,
  Heart,
  BookOpen,
  Sprout,
  RefreshCw,
  SlidersHorizontal,
  Copy,
  Info,
  LogIn,
  UserPlus,
  Trophy,
  PackageCheck,
} from "lucide-react";
import FoodArt from "./FoodArt";
import { api } from "./api";

import { NAMES, CATALOG, EMOJI, pretty, qty, localDate, timeLeft } from "./ui";
import {
  Modal,
  Empty,
  PantryForm,
  RequestForm,
  CommunityForm,
  FriendsForm,
  ChatModal,
  SettingsForm,
  ScanModal,
} from "./components";
function App() {
  const [state, setState] = useState(null),
    [page, setPage] = useState("dashboard"),
    [modal, setModal] = useState(null),
    [error, setError] = useState(""),
    [toast, setToast] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true),
    [filter, setFilter] = useState(""),
    [pantryLoc, setPantryLoc] = useState("All"),
    [recipeFilter, setRecipeFilter] = useState("Recommended"),
    [communityTab, setCommunityTab] = useState("Requests");
  const active = useRef(true),
    loadingAccount = useRef(false),
    generation = useRef(0);
  const refresh = async () => {
    const gen = generation.current;
    const s = await api("/state");
    if (active.current && gen === generation.current) setState(s);
  };
  useEffect(() => {
    active.current = true;
    (async () => {
      try {
        await refresh();
      } catch (e) {
        if (e.status === 401) {
          try {
            await api("/demo/session", { user_id: 1 });
            await refresh();
          } catch (x) {
            setError(x.message);
          }
        } else setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
    const timer = setInterval(() => {
      if (!loadingAccount.current) refresh().catch((e) => setError(e.message));
    }, 8000);
    return () => {
      active.current = false;
      clearInterval(timer);
    };
  }, []);
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(""), 4500);
      return () => clearTimeout(t);
    }
  }, [toast]);
  const act = async (fn, message) => {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await fn();
      await refresh();
      if (message) setToast(message);
      return result;
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setBusy(false);
    }
  };
  const safe = (fn, message) => act(fn, message).catch(() => {});
  const switchAccount = async (id) => {
    generation.current++;
    loadingAccount.current = true;
    setModal(null);
    setCommunityTab("Requests");
    try {
      await act(
        () => api("/demo/session", { user_id: id }),
        "Sample account changed",
      );
    } catch {
    } finally {
      loadingAccount.current = false;
    }
  };
  const navigate = (p) => {
    setPage(p);
    setFilter("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  if (loading)
    return (
      <div className="loading-screen">
        <Leaf size={36} />
        <h1>
          savor<span>®</span>
        </h1>
        <p>Finding a little possibility in your pantry…</p>
      </div>
    );
  if (!state)
    return (
      <div className="loading-screen">
        <Leaf size={36} />
        <h1>Let’s get Savor running.</h1>
        <p role="alert">{error}</p>
        <button className="button primary" onClick={() => location.reload()}>
          Try again
        </button>
      </div>
    );
  const user = state.user,
    recommended = state.recipes.filter((r) => r.coverage >= 80),
    ready = state.recipes.filter((r) => r.ready),
    pending = state.requests.filter((r) => r.status === "pending"),
    incoming = pending.filter(
      (r) => r.user_id !== user.id && !r.declined_by_me,
    );
  const showRecipe = (r) =>
    setModal({ type: "recipe", recipe: r, key: crypto.randomUUID() });
  const showRequest = (ingredient = null, recipe = null) =>
    setModal({ type: "request", ingredient, recipe });
  const currentRecipe =
    modal?.type === "recipe"
      ? state.recipes.find((r) => r.id === modal.recipe.id) || modal.recipe
      : null;
  const pantryList = state.pantry.filter(
    (i) =>
      i.name.includes(filter.toLowerCase()) &&
      (pantryLoc === "All" || i.location === pantryLoc),
  );
  const requestAction = (r, action, msg) =>
    safe(() => api(`/requests/${r.id}/${action}`, {}), msg);

  const RecipeCard = ({ recipe: r }) => (
    <button className="recipe-card" onClick={() => showRecipe(r)}>
      <div className="recipe-picture">
        <FoodArt kind={r.image} id={r.id} />
        <span className={`coverage ${r.ready ? "complete" : ""}`}>
          <span className="coverage-dot" />
          {r.coverage}% in your pantry
        </span>
      </div>
      <div className="recipe-copy">
        <span className="eyebrow">{r.category}</span>
        <h3>{r.name}</h3>
        <p>{r.subtitle}</p>
        <div className="recipe-meta">
          <span>
            <Clock size={14} />
            {r.minutes} min
          </span>
          <span>
            <Users size={14} />
            {r.servings} servings
          </span>
          <span className="card-arrow">
            <ArrowUpRight size={19} />
          </span>
        </div>
      </div>
    </button>
  );

  const RequestCard = ({ r }) => (
    <article className="request-card">
      <div className="request-top">
        <div className="ingredient-icon">{EMOJI[r.name] || "🌱"}</div>
        <div className="request-name">
          <h3>
            {qty(r.quantity)} {r.unit} {r.name}
          </h3>
          <p>
            {r.user_id === user.id
              ? "You’re looking for a little"
              : `${r.requester} could use a little help`}
          </p>
        </div>
        <span className={`status ${r.status}`}>
          {r.status === "pending" ? timeLeft(r) : pretty(r.status)}
        </span>
      </div>
      <div className="request-tags">
        <span
          className={`tag ${r.community_id ? "community-tag" : "friend-tag"}`}
        >
          {r.community_id ? <Users size={12} /> : <Heart size={12} />}{" "}
          {r.community || `Friend · ${r.friend}`}
        </span>
        {r.recipe_id && (
          <span className="tag">
            For{" "}
            {state.recipes.find((x) => x.id === r.recipe_id)?.name || "a meal"}
          </span>
        )}
      </div>
      {r.note && <p className="request-note">“{r.note}”</p>}
      {r.provider && (
        <p className="request-note">
          <CheckCircle2 size={14} /> {r.provider}{" "}
          {r.status === "completed" ? "shared" : "has reserved"} this
          ingredient.
        </p>
      )}
      <div className="request-actions">
        {r.status === "pending" &&
          r.user_id !== user.id &&
          !r.declined_by_me && (
            <>
              <button
                className="button primary small"
                disabled={busy}
                onClick={() =>
                  requestAction(
                    r,
                    "accept",
                    "Ingredient reserved. Open pickup chat to coordinate.",
                  )
                }
              >
                <Heart size={14} />I can share
              </button>
              <button
                className="button ghost small"
                disabled={busy}
                onClick={() =>
                  requestAction(r, "decline", "Passed on this request")
                }
              >
                Pass
              </button>
            </>
          )}
        {r.status === "pending" && r.declined_by_me && (
          <span className="muted small-text">
            You passed. Other community members can still help.
          </span>
        )}
        {r.status === "accepted" &&
          [r.user_id, r.provider_id].includes(user.id) && (
            <>
              <button
                className="button secondary small"
                onClick={() => setModal({ type: "chat", request: r })}
              >
                <MessageCircle size={14} />
                Pickup chat
              </button>
              {r.user_id === user.id && (
                <button
                  className="button primary small"
                  disabled={busy}
                  onClick={() =>
                    requestAction(
                      r,
                      "complete",
                      "Pickup confirmed. Your pantry is updated.",
                    )
                  }
                >
                  <PackageCheck size={14} />
                  Confirm pickup
                </button>
              )}
            </>
          )}
        {["pending", "accepted"].includes(r.status) &&
          [r.user_id, r.provider_id].includes(user.id) && (
            <button
              className="button ghost small"
              disabled={busy}
              onClick={() =>
                requestAction(
                  r,
                  "cancel",
                  "Request cancelled. Reserved ingredients returned.",
                )
              }
            >
              Cancel
            </button>
          )}
        {r.user_id === user.id &&
          ["expired", "declined", "cancelled"].includes(r.status) && (
            <button
              className="button secondary small"
              onClick={() => {
                setRecipeFilter("Ready to cook");
                navigate("recipes");
              }}
            >
              Find a pantry-only recipe <ArrowRight size={14} />
            </button>
          )}
        {r.status === "completed" && (
          <span className="success-note">
            <CheckCircle2 size={15} /> A little shared, a meal made possible.
          </span>
        )}
      </div>
    </article>
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            navigate("dashboard");
          }}
        >
          <span className="brand-mark">
            <Leaf size={29} strokeWidth={1.7} />
          </span>
          savor<span className="registered">®</span>
        </a>
        <p className="brand-caption">GOOD FOOD. SHARED.</p>
        <nav aria-label="Main navigation">
          {[
            ["dashboard", LayoutDashboard, "Overview"],
            ["pantry", ShoppingBasket, "My pantry"],
            ["recipes", BookOpen, "Recipe ideas"],
            ["community", Users, "My community"],
            ["activity", Activity, "Our impact"],
          ].map(([key, Icon, label]) => (
            <button
              key={key}
              className={`nav-item ${page === key ? "active" : ""}`}
              onClick={() => navigate(key)}
            >
              <Icon size={19} strokeWidth={1.7} />
              {label}
              {key === "community" && incoming.length > 0 && (
                <span className="nav-count">{incoming.length}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="side-note">
            <Sprout size={25} strokeWidth={1.3} />
            <h4>
              Small shares.
              <br />
              Good things.
            </h4>
            <p>One ingredient can make someone’s whole meal.</p>
            <button onClick={() => showRequest()}>
              Ask your community <ArrowUpRight size={15} />
            </button>
          </div>
          <button
            className="nav-item"
            onClick={() => setModal({ type: "settings" })}
          >
            <Settings size={18} />
            Preferences
          </button>
          <div className="account">
            <span className="avatar" style={{ background: user.color }}>
              {user.name[0]}
            </span>
            <div>
              <strong>{user.name}</strong>
              <span>Sample account</span>
            </div>
            <select
              aria-label="Switch sample account"
              value={user.id}
              disabled={busy}
              onChange={(e) => switchAccount(Number(e.target.value))}
            >
              {NAMES.map((n, i) => (
                <option key={n} value={i + 1}>
                  {n}
                </option>
              ))}
            </select>
          </div>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div className="breadcrumbs">
            Your space <ChevronRight size={13} />
            <span>
              {
                {
                  dashboard: "Overview",
                  pantry: "My pantry",
                  recipes: "Recipe ideas",
                  community: "My community",
                  activity: "Our impact",
                }[page]
              }
            </span>
          </div>
          <div className="top-actions">
            <span className="demo-pill">
              <span />
              Local demo · sample data
            </span>
            <button
              className="notification-button"
              aria-label="Show request updates"
              onClick={() => {
                navigate("community");
                setCommunityTab("Requests");
              }}
            >
              <MessageCircle size={18} />
              {incoming.length > 0 && <i />}
            </button>
            <button
              className="top-avatar"
              aria-label="Sample accounts and preferences"
              style={{ background: user.color }}
              onClick={() => setModal({ type: "accounts" })}
            >
              {user.name[0]}
            </button>
          </div>
        </header>
        {error && (
          <div className="error-banner" role="alert">
            <Info size={18} />
            <span>{error}</span>
            <button onClick={() => setError("")} aria-label="Dismiss error">
              <X size={16} />
            </button>
          </div>
        )}
        <div className="page-content">
          {page === "dashboard" && (
            <>
              <div className="section-heading greeting">
                <div>
                  <p className="eyebrow">A GOOD DAY TO MAKE SOMETHING GOOD</p>
                  <h1>
                    Hello, {user.name}
                    <span className="heading-sprig"> ✳</span>
                  </h1>
                  <p>Good things start with what you already have.</p>
                </div>
                <button
                  className="button primary"
                  onClick={() => setModal({ type: "pantry" })}
                >
                  <Plus size={17} />
                  Add groceries
                </button>
              </div>
              <section className="hero">
                <div className="hero-copy">
                  <span className="pill-light">
                    <span />
                    YOUR PANTRY HAS POTENTIAL
                  </span>
                  <h2>
                    A little less waste.
                    <br />A lot more <em>possibility.</em>
                  </h2>
                  <p>
                    Turn what’s on hand into something delicious.
                    <br />
                    And borrow a little inspiration from your community.
                  </p>
                  <button
                    className="button cream"
                    onClick={() => navigate("recipes")}
                  >
                    Find tonight’s dinner <ArrowUpRight size={17} />
                  </button>
                </div>
                <div className="hero-art" aria-hidden="true">
                  <div className="hero-orbit" />
                  <div className="hero-plate">
                    <FoodArt kind="pasta" id="hero" />
                  </div>
                  <div className="hero-note">
                    <span>🌿</span>
                    <div>
                      Already in your pantry.
                      <br />
                      <strong>Ready for something good.</strong>
                    </div>
                  </div>
                  <span className="hero-spark one">✳</span>
                  <span className="hero-spark two">✳</span>
                  <span className="hero-spark three">·</span>
                </div>
              </section>
              <div className="stats-strip">
                <div>
                  <ShoppingBasket size={22} />
                  <span>
                    <strong>{state.pantry.length}</strong> ingredients on hand
                  </span>
                </div>
                <div>
                  <BookOpen size={22} />
                  <span>
                    <strong>{ready.length}</strong> recipes ready to cook
                  </span>
                </div>
                <div>
                  <Users size={22} />
                  <span>
                    <strong>{state.communities.length}</strong> communities to
                    lean on
                  </span>
                </div>
              </div>
              <section>
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">LESS “WHAT’S FOR DINNER?”</p>
                    <h2>Made for your pantry</h2>
                    <p>
                      Curated recipe ideas matched to your ingredients and
                      quantities.
                    </p>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => navigate("recipes")}
                  >
                    Explore recipes <ArrowRight size={16} />
                  </button>
                </div>
                {recommended.length ? (
                  <div className="recipe-grid">
                    {recommended.slice(0, 3).map((r) => (
                      <RecipeCard key={r.id} recipe={r} />
                    ))}
                  </div>
                ) : (
                  <Empty
                    icon={BookOpen}
                    title="A few ingredients go a long way."
                    text="Add pantry items or adjust your preferences to find a recipe that matches at least 80%."
                    action="Add an ingredient"
                    onClick={() => setModal({ type: "pantry" })}
                  />
                )}
              </section>
              <div className="bottom-grid">
                <section className="pantry-peek panel">
                  <div className="section-heading compact">
                    <div>
                      <p className="eyebrow">GIVE THESE A LITTLE LOVE</p>
                      <h2>First in, first cooked</h2>
                    </div>
                    <button
                      className="icon-btn"
                      aria-label="Open pantry"
                      onClick={() => navigate("pantry")}
                    >
                      <ArrowUpRight size={20} />
                    </button>
                  </div>
                  <p className="muted intro">
                    Your older groceries, ready for their next chapter.
                  </p>
                  {[...state.pantry]
                    .sort((a, b) => b.days_stored - a.days_stored)
                    .filter((i) => i.location === "Fridge")
                    .slice(0, 3)
                    .map((i) => (
                      <button
                        className="pantry-preview-row"
                        key={i.id}
                        onClick={() => setModal({ type: "pantry", item: i })}
                      >
                        <span className="ingredient-icon small">
                          {EMOJI[i.name] || "🌱"}
                        </span>
                        <span>
                          <strong>{pretty(i.name)}</strong>
                          <small>
                            {qty(i.quantity)} {i.unit} · {i.location}
                          </small>
                        </span>
                        <span className="age">Stored {i.days_stored}d</span>
                        <ChevronRight size={15} />
                      </button>
                    ))}
                  {!state.pantry.some((i) => i.location === "Fridge") && (
                    <p className="muted">
                      Add something to your fridge to see it here.
                    </p>
                  )}
                  <p className="fine-print">
                    <Info size={12} />
                    Storage age is not a freshness or food-safety estimate.
                  </p>
                </section>
                <section className="community-callout">
                  <div className="community-art" aria-hidden="true">
                    <div>🧄</div>
                    <span>+</span>
                    <div>🍅</div>
                    <span>=</span>
                    <div>🍝</div>
                  </div>
                  <p className="eyebrow">GOOD NEIGHBORS. GREAT DINNERS.</p>
                  <h2>Missing one little thing?</h2>
                  <p>
                    Someone nearby might have just enough.
                    <br />
                    Ask for a pinch. Share a little back.
                  </p>
                  <button
                    className="button secondary"
                    onClick={() => showRequest()}
                  >
                    Ask your community <ArrowUpRight size={16} />
                  </button>
                  <span className="callout-foot">
                    <span className="mini-avatars">
                      <i>A</i>
                      <i>J</i>
                      <i>S</i>
                    </span>
                    Your sample community is here to help
                  </span>
                </section>
              </div>
            </>
          )}

          {page === "pantry" && (
            <>
              <div className="section-heading">
                <div>
                  <p className="eyebrow">
                    A LITTLE ORGANIZATION. A LOT OF POSSIBILITY.
                  </p>
                  <h1>My pantry</h1>
                  <p>Know what you have. Make something good with it.</p>
                </div>
                <div className="button-group">
                  <button
                    className="button secondary"
                    onClick={() => setModal({ type: "scan" })}
                  >
                    <Camera size={17} />
                    Receipt scan
                  </button>
                  <button
                    className="button primary"
                    onClick={() => setModal({ type: "pantry" })}
                  >
                    <Plus size={17} />
                    Add groceries
                  </button>
                </div>
              </div>
              <div className="toolbar">
                <label className="search">
                  <Search size={17} />
                  <input
                    placeholder="Find an ingredient…"
                    aria-label="Search pantry"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                  />
                </label>
                <div className="tabs">
                  {["All", "Fridge", "Pantry", "Freezer", "Counter"].map(
                    (l) => (
                      <button
                        key={l}
                        onClick={() => setPantryLoc(l)}
                        className={pantryLoc === l ? "selected" : ""}
                      >
                        {l}
                      </button>
                    ),
                  )}
                </div>
              </div>
              <div className="pantry-grid">
                {pantryList.map((i) => (
                  <button
                    key={i.id}
                    className="pantry-item"
                    onClick={() => setModal({ type: "pantry", item: i })}
                  >
                    <div className="ingredient-large">
                      {EMOJI[i.name] || "🌱"}
                    </div>
                    <span className="location-label">{i.location}</span>
                    <h3>{pretty(i.name)}</h3>
                    <p>
                      {qty(i.quantity)} {i.unit}
                    </p>
                    <div className="pantry-item-foot">
                      <span>
                        Stored {i.days_stored}{" "}
                        {i.days_stored === 1 ? "day" : "days"}
                      </span>
                      <ArrowUpRight size={16} />
                    </div>
                  </button>
                ))}
              </div>
              {!pantryList.length && (
                <Empty
                  icon={ShoppingBasket}
                  title="Room for something good."
                  text="No ingredients match this view. Add groceries or try another search."
                  action="Add groceries"
                  onClick={() => setModal({ type: "pantry" })}
                />
              )}
              <p className="fine-print">
                <Info size={13} />
                We show how long food has been stored, not predicted expiration
                dates. Use your own judgment about food quality.
              </p>
            </>
          )}

          {page === "recipes" && (
            <>
              <div className="section-heading">
                <div>
                  <p className="eyebrow">MAKE MORE OF WHAT YOU HAVE</p>
                  <h1>Something delicious awaits.</h1>
                  <p>
                    Cook for {user.servings}. Start with your ingredients, then
                    add a little inspiration.
                  </p>
                </div>
                <button
                  className="button secondary"
                  onClick={() => setModal({ type: "settings" })}
                >
                  <SlidersHorizontal size={17} />
                  Preferences
                </button>
              </div>
              <div className="recipe-banner">
                <span>🌤️</span>
                <div>
                  <strong>Eats of the Day</strong>
                  <p>
                    Today’s curated ideas. Live AI generation and morning push
                    delivery are not connected.
                  </p>
                </div>
              </div>
              <div className="tabs recipe-tabs">
                {["Recommended", "Ready to cook", "All ideas"].map((t) => (
                  <button
                    key={t}
                    className={recipeFilter === t ? "selected" : ""}
                    onClick={() => setRecipeFilter(t)}
                  >
                    {t}
                    {t === "Ready to cook" && <span>{ready.length}</span>}
                  </button>
                ))}
              </div>
              <div className="recipe-grid">
                {(recipeFilter === "Recommended"
                  ? recommended
                  : recipeFilter === "Ready to cook"
                    ? ready
                    : state.recipes
                ).map((r) => (
                  <RecipeCard key={r.id} recipe={r} />
                ))}
              </div>
              {(recipeFilter === "Recommended"
                ? recommended
                : recipeFilter === "Ready to cook"
                  ? ready
                  : state.recipes
              ).length === 0 && (
                <Empty
                  icon={BookOpen}
                  title="Let’s find your next meal."
                  text="Try adding groceries or changing your serving size and dietary preferences."
                  action="Open preferences"
                  onClick={() => setModal({ type: "settings" })}
                />
              )}
              <p className="fine-print">
                Coverage = ingredient lines fully covered by compatible pantry
                quantities ÷ all ingredient lines. Recommended ideas start at
                80%. Recipes are curated demo data.
              </p>
            </>
          )}

          {page === "community" && (
            <>
              <div className="section-heading">
                <div>
                  <p className="eyebrow">A LITTLE HELP GOES A LONG WAY</p>
                  <h1>Better together.</h1>
                  <p>Share an ingredient. Make someone’s dinner.</p>
                </div>
                <button
                  className="button primary"
                  onClick={() => showRequest()}
                >
                  <Plus size={17} />
                  Request an ingredient
                </button>
              </div>
              <div className="communities-row">
                {state.communities.map((c) => (
                  <button
                    className={`community-card ${c.color}`}
                    key={c.id}
                    onClick={() => setModal({ type: "chat", community: c })}
                  >
                    <span className="community-symbol">
                      <Users size={23} />
                    </span>
                    <div>
                      <h3>{c.name}</h3>
                      <p>
                        {c.members} sample{" "}
                        {c.members === 1 ? "member" : "members"} · Private group
                      </p>
                    </div>
                    <MessageCircle size={19} />
                  </button>
                ))}
                <button
                  className="community-add"
                  onClick={() => setModal({ type: "community" })}
                >
                  <Plus size={22} />
                  <span>Create or join a community</span>
                </button>
              </div>
              <div className="friends-strip">
                <span>
                  <Heart size={15} /> Friends:{" "}
                  {state.friends.map((f) => f.name).join(", ") ||
                    "Your next good neighbor awaits"}
                </span>
                <button
                  className="text-button"
                  onClick={() => setModal({ type: "friends" })}
                >
                  <UserPlus size={15} />
                  Connect a friend
                </button>
              </div>
              <div className="tabs request-tabs">
                {["Requests", "My requests", "Completed"].map((t) => (
                  <button
                    key={t}
                    className={communityTab === t ? "selected" : ""}
                    onClick={() => setCommunityTab(t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <div className="request-grid">
                {state.requests
                  .filter((r) =>
                    communityTab === "My requests"
                      ? r.user_id === user.id
                      : communityTab === "Completed"
                        ? r.status === "completed"
                        : !["completed", "cancelled"].includes(r.status),
                  )
                  .map((r) => (
                    <RequestCard key={r.id} r={r} />
                  ))}
              </div>
              {state.requests.filter((r) =>
                communityTab === "My requests"
                  ? r.user_id === user.id
                  : communityTab === "Completed"
                    ? r.status === "completed"
                    : !["completed", "cancelled"].includes(r.status),
              ).length === 0 && (
                <Empty
                  icon={Users}
                  title={
                    communityTab === "Completed"
                      ? "Your next shared moment starts here."
                      : "A quiet pantry is a happy pantry."
                  }
                  text="Missing a clove of garlic? Ask for exactly what you need, from the people you know."
                  action="Make a request"
                  onClick={() => showRequest()}
                />
              )}
              <p className="fine-print">
                <Info size={13} />
                Accepted ingredients are reserved until pickup or cancellation.
                Open a community card for group chat.
              </p>
            </>
          )}

          {page === "activity" && (
            <>
              <div className="section-heading">
                <div>
                  <p className="eyebrow">SMALL ACTIONS ADD UP</p>
                  <h1>A little good, together.</h1>
                  <p>
                    Real actions inside this local demo. No invented savings.
                  </p>
                </div>
                <span className="demo-pill">Sample accounts only</span>
              </div>
              <div className="impact-grid">
                <div className="impact-card">
                  <BookOpen size={25} />
                  <strong>{state.meals_cooked}</strong>
                  <h3>Meals you’ve cooked</h3>
                  <p>Confirmed with ingredients deducted.</p>
                </div>
                <div className="impact-card">
                  <Heart size={25} />
                  <strong>{state.shared_count}</strong>
                  <h3>Times you’ve shared</h3>
                  <p>Confirmed pickups in your visible communities.</p>
                </div>
                <div className="impact-card">
                  <Sprout size={25} />
                  <strong>9,000</strong>
                  <h3>The team’s request goal</h3>
                  <p>
                    Aspirational: 100 people × 3 shares × 30 days. Not achieved
                    impact.
                  </p>
                </div>
              </div>
              <section className="panel leaderboard">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">A LITTLE COMMUNITY LOVE</p>
                    <h2>The sharing table</h2>
                  </div>
                  <Trophy size={26} />
                </div>
                <p className="muted">
                  Completed shares visible to you. A thank-you, not a
                  food-savings estimate.
                </p>
                {state.leaderboard.map((l, i) => (
                  <div className="leaderboard-row" key={l.id}>
                    <span className="rank">{i + 1}</span>
                    <span className="avatar">{l.name[0]}</span>
                    <strong>
                      {l.name}
                      {l.id === user.id ? " (you)" : ""}
                    </strong>
                    <span>
                      {l.count} {l.count === 1 ? "share" : "shares"}
                    </span>
                  </div>
                ))}
              </section>
              <p className="fine-print">
                Food weight and money saved are not calculated. Accurate impact
                estimates require measured quantities, costs and a documented
                comparison method.
              </p>
            </>
          )}
          <footer>
            <span className="footer-brand">
              <Leaf size={15} /> savor
            </span>
            <span>Good food deserves good company.</span>
            <button onClick={() => setModal({ type: "about" })}>
              About this demo <ArrowUpRight size={13} />
            </button>
          </footer>
        </div>
      </main>
      {toast && (
        <div className="toast" role="status">
          <CheckCircle2 size={18} />
          {toast}
        </div>
      )}
      {modal?.type === "pantry" && (
        <PantryForm
          item={modal.item}
          units={state.units}
          busy={busy}
          close={() => setModal(null)}
          save={(v) =>
            act(
              () =>
                api(
                  modal.item ? `/pantry/${modal.item.id}` : "/pantry",
                  v,
                  modal.item ? "PATCH" : "POST",
                ),
              "Pantry updated",
            ).then(() => setModal(null))
          }
          remove={() =>
            act(
              () => api(`/pantry/${modal.item.id}`, {}, "DELETE"),
              "Ingredient removed",
            ).then(() => setModal(null))
          }
        />
      )}
      {modal?.type === "recipe" && (
        <Modal
          title={currentRecipe.name}
          subtitle={`${currentRecipe.minutes} minutes · Cook ${currentRecipe.servings} servings · Curated demo recipe`}
          onClose={() => setModal(null)}
          wide
        >
          <div className="recipe-detail">
            <div className="detail-picture">
              <FoodArt
                kind={currentRecipe.image}
                id={`detail-${currentRecipe.id}`}
              />
            </div>
            <div>
              <div className="detail-coverage">
                <strong>{currentRecipe.coverage}%</strong>
                <span>
                  in your pantry
                  <br />
                  <small>
                    {currentRecipe.covered} of {currentRecipe.total} ingredient
                    lines fully covered
                  </small>
                </span>
              </div>
              <h3>Here’s what you’ll need</h3>
              {currentRecipe.ingredients.map((i) => (
                <div
                  className={`ingredient-line ${i.owned ? "owned" : "missing"}`}
                  key={i.name}
                >
                  <span>
                    {i.owned ? <Check size={16} /> : <Plus size={16} />}
                  </span>
                  <div>
                    <strong>{pretty(i.name)}</strong>
                    <small>
                      {qty(i.quantity)} {i.unit} needed
                      {i.missing > 0
                        ? ` · missing ${qty(i.missing)} ${i.unit}`
                        : ""}
                    </small>
                  </div>
                  {!i.owned && (
                    <button
                      className="text-button"
                      onClick={() =>
                        showRequest(
                          { ...i, quantity: i.missing },
                          currentRecipe,
                        )
                      }
                    >
                      Ask <ArrowUpRight size={13} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
          <div className="method">
            <h3>Make something good</h3>
            <ol>
              {currentRecipe.steps.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ol>
          </div>
          <div className="modal-bottom">
            <span className="muted small-text">
              {currentRecipe.ready
                ? "All the ingredients are ready. Confirm after cooking."
                : "Collect missing ingredients before confirming this meal."}
            </span>
            <button
              className="button primary"
              disabled={busy || !currentRecipe.ready}
              onClick={() =>
                act(
                  () =>
                    api(`/recipes/${currentRecipe.id}/cook`, {
                      request_key: modal.key,
                    }),
                  "Meal recorded. Your pantry is updated.",
                )
                  .then(() => setModal(null))
                  .catch(() => {})
              }
            >
              <CheckCircle2 size={17} />I cooked this
            </button>
          </div>
        </Modal>
      )}
      {modal?.type === "request" && (
        <RequestForm
          state={state}
          ingredient={modal.ingredient}
          recipe={modal.recipe}
          busy={busy}
          close={() => setModal(null)}
          save={(v) =>
            act(
              () => api("/requests", v),
              "Request sent to your community",
            ).then(() => {
              setModal(null);
              navigate("community");
              setCommunityTab("My requests");
            })
          }
        />
      )}
      {modal?.type === "community" && (
        <CommunityForm
          close={() => setModal(null)}
          busy={busy}
          save={(path, v) =>
            act(() => api(path, v), "Community updated").then(() =>
              setModal(null),
            )
          }
        />
      )}
      {modal?.type === "friends" && (
        <FriendsForm
          close={() => setModal(null)}
          busy={busy}
          invite={() => api("/friends/invite", {})}
          join={(v) =>
            act(() => api("/friends/join", v), "Friend connected").then(() =>
              setModal(null),
            )
          }
        />
      )}
      {modal?.type === "chat" && (
        <ChatModal
          user={user}
          community={modal.community}
          request={modal.request}
          close={() => setModal(null)}
        />
      )}
      {modal?.type === "settings" && (
        <SettingsForm
          user={user}
          close={() => setModal(null)}
          busy={busy}
          save={(v) =>
            act(() => api("/settings", v, "PATCH"), "Preferences saved").then(
              () => setModal(null),
            )
          }
        />
      )}
      {modal?.type === "scan" && (
        <ScanModal
          close={() => setModal(null)}
          manual={() => setModal({ type: "pantry" })}
          busy={busy}
          save={async (rows, key) => {
            await act(
              () => api("/pantry/batch", { rows, request_key: key }),
              "Reviewed sample items added",
            );
            setModal(null);
          }}
        />
      )}
      {modal?.type === "accounts" && (
        <Modal
          title="Your sample table"
          subtitle="Switch accounts to try both sides of an exchange."
          onClose={() => setModal(null)}
        >
          <div className="sample-accounts">
            {NAMES.map((name, i) => (
              <button
                key={name}
                className={`button ${user.id === i + 1 ? "primary" : "secondary"}`}
                disabled={busy}
                onClick={() => switchAccount(i + 1)}
              >
                {name}
                {user.id === i + 1 && <Check size={16} />}
              </button>
            ))}
          </div>
          <div className="modal-bottom">
            <button
              className="button secondary"
              onClick={() => setModal({ type: "settings" })}
            >
              <Settings size={16} />
              Preferences
            </button>
          </div>
        </Modal>
      )}
      {modal?.type === "about" && (
        <Modal title="A little about this demo" onClose={() => setModal(null)}>
          <div className="about-copy">
            <p>
              Savor is a local prototype for the CO × TC case competition, built
              around your team’s updated product requirements.
            </p>
            <p>
              <strong>Working here:</strong> persistent pantry, quantity-aware
              curated recipes, communities, friend invites, timed requests,
              ingredient reservations, pickup chat, exchanges and cooking
              records.
            </p>
            <p>
              <strong>Sample data:</strong> Alex, Jamie, Sam, initial groceries,
              messages and recipes. Switch sample accounts from the sidebar to
              try both sides of an exchange.
            </p>
            <p>
              <strong>Still to connect:</strong> Google sign-in, live AI receipt
              scanning and recipe generation, external push notifications and
              scheduled morning delivery. This local demo is not production
              authentication.
            </p>
            <p>
              We track storage age, not expiration. Payments, buying/selling,
              deliveries and public posts are outside the product scope.
            </p>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default App;
