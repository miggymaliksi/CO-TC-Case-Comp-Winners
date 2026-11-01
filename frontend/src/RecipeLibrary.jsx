import React, { useEffect, useRef, useState } from "react";
import { ArrowUpRight, BookOpen, Search, Sprout } from "lucide-react";
import { api } from "./api";
import { Empty, Modal } from "./components";

export default function RecipeLibrary({ pantry, busy, onAdapt }) {
  const initial = pantry.some((i) => i.name === "tomatoes")
    ? "tomatoes"
    : pantry[0]?.name || "tomatoes";
  const [query, setQuery] = useState(initial);
  const [by, setBy] = useState("ingredient");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const active = useRef(true);
  const request = useRef(0);

  async function search(value = query, mode = by) {
    const id = ++request.current;
    setLoading(true);
    setError("");
    try {
      const result = await api(
        `/recipes/library/search?${new URLSearchParams({ query: value, by: mode })}`,
      );
      if (active.current && id === request.current) setResults(result);
    } catch (e) {
      if (active.current && id === request.current) setError(e.message);
    } finally {
      if (active.current && id === request.current) setLoading(false);
    }
  }

  async function open(recipe) {
    const id = ++request.current;
    setLoading(true);
    setError("");
    try {
      const full = await api(`/recipes/library/${recipe.id}`);
      if (active.current && id === request.current) setSelected(full);
    } catch (e) {
      if (active.current && id === request.current) setError(e.message);
    } finally {
      if (active.current && id === request.current) setLoading(false);
    }
  }

  useEffect(() => {
    active.current = true;
    search(initial, "ingredient");
    return () => {
      active.current = false;
      request.current++;
    };
  }, []);

  return (
    <section className="recipe-library">
      <div className="library-intro">
        <p className="eyebrow">RECIPES FROM THEMEALDB</p>
        <h2>A little outside inspiration.</h2>
        <p>
          Browse real recipes, then let local AI adapt an idea to your
          preferences and pantry.
        </p>
        <small>Free educational API · internet needed · no paid account</small>
      </div>
      <form
        className="library-search"
        onSubmit={(e) => {
          e.preventDefault();
          search();
        }}
      >
        <label className="field">
          Search by
          <select value={by} onChange={(e) => setBy(e.target.value)}>
            <option value="ingredient">Ingredient</option>
            <option value="name">Meal name</option>
          </select>
        </label>
        <label className="field">
          {by === "ingredient" ? "Ingredient" : "Meal name"}
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            minLength={2}
            maxLength={60}
            required
            placeholder={
              by === "ingredient" ? "e.g. tomatoes" : "e.g. Arrabiata"
            }
          />
        </label>
        <button className="button primary" disabled={loading}>
          <Search size={16} />
          Search recipes
        </button>
      </form>
      {loading && (
        <p className="generation-note" role="status">
          Loading from TheMealDB…
        </p>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {results && (
        <p className="library-source">
          {results.cached ? "Saved library results" : "Results from TheMealDB"}{" "}
          for “{results.query}” · up to 12 recipes
        </p>
      )}
      <div className="recipe-grid">
        {results?.recipes.map((recipe) => (
          <button
            key={recipe.id}
            className="recipe-card"
            disabled={loading}
            onClick={() => open(recipe)}
          >
            <div className="recipe-picture">
              {recipe.image_url ? (
                <img
                  className="library-photo"
                  src={recipe.image_url}
                  alt={`${recipe.name} from TheMealDB`}
                  loading="lazy"
                />
              ) : (
                <BookOpen size={40} />
              )}
              <span className="coverage">TheMealDB recipe</span>
            </div>
            <div className="recipe-copy">
              <span className="eyebrow">THEMEALDB</span>
              <h3>{recipe.name}</h3>
              <p>
                {[recipe.category, recipe.cuisine]
                  .filter(Boolean)
                  .join(" · ") || "View ingredients and method"}
              </p>
              <div className="recipe-meta">
                View recipe{" "}
                <span className="card-arrow">
                  <ArrowUpRight size={19} />
                </span>
              </div>
            </div>
          </button>
        ))}
      </div>
      {results?.recipes.length === 0 && !loading && (
        <Empty
          icon={BookOpen}
          title="Try another ingredient or meal name."
          text="The library uses its own ingredient names. You can also search by a recipe's title."
        />
      )}
      <p className="fine-print">
        Library recipes show the publisher's original measures. Cooking time,
        servings and dietary suitability are not verified here. AI adaptations
        get their own pantry and preference checks.
      </p>
      {selected && (
        <Modal
          title={selected.name}
          subtitle={`Original recipe from TheMealDB${selected.cuisine ? ` · ${selected.cuisine}` : ""}`}
          onClose={() => setSelected(null)}
          wide
        >
          <div className="recipe-detail">
            <div className="detail-picture">
              {selected.image_url && (
                <img
                  className="library-photo"
                  src={selected.image_url}
                  alt={selected.name}
                />
              )}
            </div>
            <div>
              <h3>Original ingredients</h3>
              {selected.ingredients.map((ingredient, index) => (
                <div className="ingredient-line" key={index}>
                  <div>
                    <strong>{ingredient.name}</strong>
                    <small>{ingredient.measure || "Amount not supplied"}</small>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="method">
            <h3>Original method</h3>
            {selected.instructions
              .split(/\r?\n+/)
              .filter(Boolean)
              .map((text, i) => (
                <p key={i}>{text}</p>
              ))}
          </div>
          <p className="library-source">
            Source: TheMealDB. Original measures have not been converted into
            Savor pantry quantities.
          </p>
          <div className="modal-bottom">
            <a
              className="button secondary"
              href={selected.source_url}
              target="_blank"
              rel="noreferrer"
            >
              View original <ArrowUpRight size={15} />
            </a>
            <button
              className="button primary"
              disabled={busy}
              onClick={() => {
                const recipe = selected;
                setSelected(null);
                onAdapt(recipe);
              }}
            >
              <Sprout size={16} />
              Set preferences & adapt
            </button>
          </div>
        </Modal>
      )}
    </section>
  );
}
