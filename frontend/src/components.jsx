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
export function Modal({ title, subtitle, onClose, children, wide = false }) {
  const dialog = useRef();
  useEffect(() => {
    const prior = document.activeElement;
    dialog.current.showModal();
    return () => {
      prior?.focus?.();
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      className={`modal ${wide ? "wide" : ""}`}
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-heading">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        <button
          className="icon-btn"
          onClick={onClose}
          aria-label="Close dialog"
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}

export function Empty({ icon: Icon, title, text, action, onClick }) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon size={28} strokeWidth={1.4} />
      </span>
      <h3>{title}</h3>
      <p>{text}</p>
      {action && (
        <button className="button secondary" onClick={onClick}>
          {action}
          <ArrowRight size={15} />
        </button>
      )}
    </div>
  );
}

export function PantryForm({ item, units, busy, close, save, remove }) {
  const [form, setForm] = useState(
      item
        ? {
            name: item.name,
            quantity: item.quantity,
            unit: item.unit,
            stored_on: item.stored_on,
            location: item.location,
          }
        : {
            name: "",
            quantity: 1,
            unit: "g",
            stored_on: localDate(),
            location: "Fridge",
          },
    ),
    [err, setErr] = useState(""),
    [confirm, setConfirm] = useState(false);
  const field = (key, value) => setForm({ ...form, [key]: value });
  return (
    <Modal
      title={item ? "A little pantry update" : "Make room for good things"}
      subtitle={
        item
          ? "Keep your groceries up to date."
          : "Add an ingredient you already have."
      }
      onClose={close}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setErr("");
          save({ ...form, quantity: Number(form.quantity) }).catch((e) =>
            setErr(e.message),
          );
        }}
      >
        <label className="field">
          Ingredient
          <input
            list="ingredients"
            autoFocus
            required
            maxLength={60}
            value={form.name}
            placeholder="e.g. tomatoes"
            onChange={(e) => field("name", e.target.value)}
          />
          <datalist id="ingredients">
            {CATALOG.map((n) => (
              <option key={n} value={n} />
            ))}
          </datalist>
        </label>
        <div className="form-row">
          <label className="field">
            Quantity
            <input
              type="number"
              required
              min="0.001"
              step="any"
              max="100000"
              value={form.quantity}
              onChange={(e) => field("quantity", e.target.value)}
            />
          </label>
          <label className="field">
            Unit
            <select
              value={form.unit}
              onChange={(e) => field("unit", e.target.value)}
            >
              {units.map((u) => (
                <option key={u}>{u}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="form-row">
          <label className="field">
            Stored on
            <input
              type="date"
              required
              min="2000-01-01"
              max={localDate()}
              value={form.stored_on}
              onChange={(e) => field("stored_on", e.target.value)}
            />
          </label>
          <label className="field">
            Where it lives
            <select
              value={form.location}
              onChange={(e) => field("location", e.target.value)}
            >
              {["Fridge", "Pantry", "Freezer", "Counter"].map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
          </label>
        </div>
        <p className="fine-print">
          Use grams or milliliters for reliable recipe matching. Count units
          like cloves and slices match only the same unit.
        </p>
        {err && (
          <p className="form-error" role="alert">
            {err}
          </p>
        )}
        <div className="modal-bottom">
          {item && (
            <button
              type="button"
              className="button danger ghost"
              onClick={() => setConfirm(true)}
            >
              <Trash2 size={15} />
              Remove
            </button>
          )}
          <button className="button primary" disabled={busy}>
            {busy ? "Saving…" : item ? "Save changes" : "Add to pantry"}
            <Check size={16} />
          </button>
        </div>
      </form>
      {confirm && (
        <div className="inline-confirm">
          <p>
            Remove {pretty(item.name)} from your pantry? This removes only this
            entry.
          </p>
          <button
            className="button danger small"
            disabled={busy}
            onClick={() => remove().catch((e) => setErr(e.message))}
          >
            Remove item
          </button>
          <button
            className="button ghost small"
            onClick={() => setConfirm(false)}
          >
            Keep it
          </button>
        </div>
      )}
    </Modal>
  );
}

export function RequestForm({ state, ingredient, recipe, busy, close, save }) {
  const [name, setName] = useState(ingredient?.name || ""),
    [amount, setAmount] = useState(ingredient?.quantity || 1),
    [unit, setUnit] = useState(ingredient?.unit || "clove"),
    [target, setTarget] = useState(
      state.communities[0]
        ? `c:${state.communities[0].id}`
        : state.friends[0]
          ? `f:${state.friends[0].id}`
          : "",
    ),
    [minutes, setMinutes] = useState(30),
    [note, setNote] = useState(""),
    [err, setErr] = useState("");
  return (
    <Modal
      title="A little help with dinner?"
      subtitle={
        recipe
          ? `For your ${recipe.name.toLowerCase()}.`
          : "Ask for exactly what you need."
      }
      onClose={close}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setErr("");
          const [kind, id] = target.split(":");
          save({
            name,
            quantity: Number(amount),
            unit,
            minutes: Number(minutes),
            note,
            recipe_id: recipe?.id || null,
            community_id: kind === "c" ? Number(id) : null,
            friend_id: kind === "f" ? Number(id) : null,
          }).catch((e) => setErr(e.message));
        }}
      >
        <label className="field">
          What’s missing?
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. garlic"
            required
            maxLength={60}
            autoFocus
          />
        </label>
        <div className="form-row">
          <label className="field">
            Just this much
            <input
              type="number"
              min="0.001"
              step="any"
              max="100000"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </label>
          <label className="field">
            Unit
            <select value={unit} onChange={(e) => setUnit(e.target.value)}>
              {state.units.map((u) => (
                <option key={u}>{u}</option>
              ))}
            </select>
          </label>
        </div>
        <label className="field">
          Ask your people
          <select
            required
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          >
            <option value="" disabled>
              Choose a community or friend
            </option>
            {state.communities.map((c) => (
              <option key={`c${c.id}`} value={`c:${c.id}`}>
                Community · {c.name}
              </option>
            ))}
            {state.friends.map((f) => (
              <option key={`f${f.id}`} value={`f:${f.id}`}>
                Friend · {f.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          When do you need it?
          <select value={minutes} onChange={(e) => setMinutes(e.target.value)}>
            {[
              [15, "In 15 minutes"],
              [30, "In 30 minutes"],
              [60, "In an hour"],
              [180, "In 3 hours"],
              [1440, "Within 24 hours"],
            ].map(([n, s]) => (
              <option key={n} value={n}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          A note for your neighbor <span className="optional">(optional)</span>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Making pasta tonight. Happy to meet in the lobby!"
            maxLength={400}
          />
        </label>
        <p className="fine-print">
          Only your chosen community or friend can see this request. If no one
          can help, we’ll help you find a pantry-only recipe.
        </p>
        {err && (
          <p className="form-error" role="alert">
            {err}
          </p>
        )}
        <div className="modal-bottom">
          <button type="button" className="button ghost" onClick={close}>
            Maybe later
          </button>
          <button className="button primary" disabled={busy || !target}>
            Send request
            <ArrowUpRight size={17} />
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function CommunityForm({ close, busy, save }) {
  const [mode, setMode] = useState("Create"),
    [value, setValue] = useState(""),
    [err, setErr] = useState("");
  return (
    <Modal
      title="Find your people"
      subtitle="Private communities for the people you know."
      onClose={close}
    >
      <div className="tabs">
        <button
          className={mode === "Create" ? "selected" : ""}
          onClick={() => {
            setMode("Create");
            setValue("");
          }}
        >
          Create
        </button>
        <button
          className={mode === "Join" ? "selected" : ""}
          onClick={() => {
            setMode("Join");
            setValue("");
          }}
        >
          Join with a code
        </button>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          save(
            mode === "Create" ? "/communities" : "/communities/join",
            mode === "Create" ? { name: value } : { code: value },
          ).catch((e) => setErr(e.message));
        }}
      >
        <label className="field">
          {mode === "Create" ? "Community name" : "Invite code"}
          <input
            required
            minLength={mode === "Create" ? 2 : 3}
            maxLength={mode === "Create" ? 50 : 100}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={
              mode === "Create"
                ? "e.g. Our apartment"
                : "Ask a member for their code"
            }
          />
        </label>
        {err && (
          <p className="form-error" role="alert">
            {err}
          </p>
        )}
        <div className="modal-bottom">
          <button className="button primary" disabled={busy}>
            {mode === "Create" ? "Create community" : "Join community"}
            <Users size={16} />
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function FriendsForm({ close, busy, invite, join }) {
  const [code, setCode] = useState(""),
    [value, setValue] = useState(""),
    [err, setErr] = useState("");
  return (
    <Modal
      title="A friend at your table"
      subtitle="Share a one-use code with someone you know."
      onClose={close}
    >
      <button
        className="button secondary"
        onClick={() =>
          invite()
            .then((v) => setCode(v.code))
            .catch((e) => setErr(e.message))
        }
      >
        <UserPlus size={16} />
        Make an invite code
      </button>
      {code && (
        <div className="invite-code">
          <code>{code}</code>
          <button
            className="icon-btn"
            aria-label="Copy friend invite"
            onClick={() =>
              navigator.clipboard
                .writeText(code)
                .catch(() => setErr("Select and copy the code above."))
            }
          >
            <Copy size={16} />
          </button>
          <p>Valid for 24 hours. Switch to Sam to try connecting.</p>
        </div>
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          join({ code: value }).catch((e) => setErr(e.message));
        }}
      >
        <label className="field">
          Have a friend’s code?
          <input
            required
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Paste their invite code"
          />
        </label>
        {err && (
          <p className="form-error" role="alert">
            {err}
          </p>
        )}
        <div className="modal-bottom">
          <button className="button primary" disabled={busy}>
            Connect friend
            <Heart size={16} />
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function ChatModal({ user, community, request, close }) {
  const [messages, setMessages] = useState([]),
    [body, setBody] = useState(""),
    [error, setError] = useState(""),
    [sending, setSending] = useState(false),
    [copied, setCopied] = useState(false);
  const scope = community
    ? { community_id: community.id }
    : { request_id: request.id };
  const query = community
    ? `community_id=${community.id}`
    : `request_id=${request.id}`;
  useEffect(() => {
    let mounted = true;
    const load = () =>
      api(`/messages?${query}`)
        .then((v) => {
          if (mounted) setMessages(v);
        })
        .catch((e) => {
          if (mounted) setError(e.message);
        });
    load();
    const t = setInterval(load, 4000);
    return () => {
      mounted = false;
      clearInterval(t);
    };
  }, [query]);
  return (
    <Modal
      title={community ? community.name : `Pickup · ${pretty(request.name)}`}
      subtitle={
        community
          ? "A private space for your community."
          : "Only you and the accepted provider can see this chat."
      }
      onClose={close}
    >
      {community && (
        <div className="invite-code compact">
          <span>
            Community invite: <code>{community.invite_code}</code>
          </span>
          <button
            className="text-button"
            onClick={() =>
              navigator.clipboard
                .writeText(community.invite_code)
                .then(() => setCopied(true))
                .catch(() => setError("Select and copy the invite code above."))
            }
          >
            {copied ? "Copied" : "Copy"}
            <Copy size={13} />
          </button>
        </div>
      )}
      <div className="messages" aria-live="polite">
        {messages.length ? (
          messages.map((m) => (
            <div
              key={m.id}
              className={`message ${m.user_id === user.id ? "mine" : ""}`}
            >
              <span>
                {m.name} ·{" "}
                {new Date(m.created_at * 1000).toLocaleTimeString([], {
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </span>
              <p>{m.body}</p>
            </div>
          ))
        ) : (
          <p className="muted">Start with a hello. A good meal might follow.</p>
        )}
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <form
        className="message-form"
        onSubmit={async (e) => {
          e.preventDefault();
          setSending(true);
          setError("");
          try {
            await api("/messages", { ...scope, body });
            setBody("");
            setMessages(await api(`/messages?${query}`));
          } catch (e) {
            setError(e.message);
          } finally {
            setSending(false);
          }
        }}
      >
        <input
          required
          maxLength={1000}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Say something good…"
          aria-label="Message"
        />
        <button
          className="button primary"
          disabled={sending || !body.trim()}
          aria-label="Send message"
        >
          <Send size={17} />
        </button>
      </form>
    </Modal>
  );
}

export function SettingsForm({ user, close, busy, save }) {
  const [servings, setServings] = useState(user.servings),
    [diet, setDiet] = useState(user.diet),
    [minutes, setMinutes] = useState(user.max_minutes),
    [err, setErr] = useState("");
  return (
    <Modal
      title="What sounds good?"
      subtitle="Choose your preferences. AI will use them with your pantry."
      onClose={close}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          save({
            servings: Number(servings),
            diet,
            max_minutes: Number(minutes),
          }).catch((e) => setErr(e.message));
        }}
      >
        <label className="field">
          How many at your table?
          <select
            value={servings}
            disabled={busy}
            onChange={(e) => setServings(e.target.value)}
          >
            {Array.from({ length: 8 }, (_, i) => (
              <option key={i} value={i + 1}>
                {i + 1} {i === 0 ? "serving" : "servings"}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          Dietary preference
          <select
            value={diet}
            disabled={busy}
            onChange={(e) => setDiet(e.target.value)}
          >
            {["All", "Vegetarian", "Vegan", "Gluten-free"].map((d) => (
              <option key={d}>{d}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Maximum cooking time
          <select
            value={minutes}
            disabled={busy}
            onChange={(e) => setMinutes(e.target.value)}
          >
            {[10, 15, 20, 30, 45, 60, 90, 120].map((m) => (
              <option key={m} value={m}>
                {m} minutes
              </option>
            ))}
          </select>
        </label>
        <p className="fine-print">
          AI will create an idea for these servings, diet and cooking time. Your
          pantry stays unchanged. Check individual ingredient labels for dietary
          needs.
        </p>
        {err && (
          <p className="form-error" role="alert">
            {err}
          </p>
        )}
        <div className="modal-bottom">
          <button className="button primary" disabled={busy}>
            {busy ? "Saving preferences…" : "Save preferences & generate"}
            <Sprout size={16} />
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function ScanModal({ close, manual, busy, save }) {
  const [key] = useState(() => crypto.randomUUID());
  const [preview, setPreview] = useState(false),
    [rows, setRows] = useState([
      {
        name: "tomatoes",
        quantity: 300,
        unit: "g",
        stored_on: localDate(),
        location: "Fridge",
      },
      {
        name: "garlic",
        quantity: 3,
        unit: "clove",
        stored_on: localDate(),
        location: "Pantry",
      },
    ]),
    [err, setErr] = useState("");
  return (
    <Modal
      title="From receipt to pantry"
      subtitle="AI receipt scanning is not connected in this demo."
      onClose={close}
    >
      <div className="scan-placeholder">
        <Camera size={33} strokeWidth={1.3} />
        <h3>A simpler grocery routine, coming next.</h3>
        <p>
          You can try an editable sample receipt, or add your groceries by hand.
          No receipt is uploaded or scanned.
        </p>
      </div>
      {!preview ? (
        <div className="button-group">
          <button className="button secondary" onClick={() => setPreview(true)}>
            Try sample receipt
          </button>
          <button className="button primary" onClick={manual}>
            Add manually
            <Plus size={16} />
          </button>
        </div>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            save(
              rows.map((r) => ({ ...r, quantity: Number(r.quantity) })),
              key,
            ).catch((e) => setErr(e.message));
          }}
        >
          <p className="sample-label">SAMPLE RECEIPT · REVIEW BEFORE ADDING</p>
          {rows.map((r, i) => (
            <div className="receipt-row" key={i}>
              <label className="field">
                Ingredient
                <input
                  required
                  value={r.name}
                  onChange={(e) =>
                    setRows(
                      rows.map((x, j) =>
                        i === j ? { ...x, name: e.target.value } : x,
                      ),
                    )
                  }
                />
              </label>
              <label className="field">
                Amount
                <input
                  type="number"
                  min="0.001"
                  max="100000"
                  step="any"
                  required
                  value={r.quantity}
                  onChange={(e) =>
                    setRows(
                      rows.map((x, j) =>
                        i === j ? { ...x, quantity: e.target.value } : x,
                      ),
                    )
                  }
                />
              </label>
              <span>{r.unit}</span>
            </div>
          ))}
          {err && (
            <p className="form-error" role="alert">
              {err}
            </p>
          )}
          <div className="modal-bottom">
            <button className="button primary" disabled={busy}>
              Add reviewed sample items
              <Check size={16} />
            </button>
          </div>
        </form>
      )}
    </Modal>
  );
}
