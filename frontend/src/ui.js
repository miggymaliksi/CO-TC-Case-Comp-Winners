export const NAMES = ["Alex", "Jamie", "Sam"];
export const CATALOG = [
  "tomatoes",
  "spinach",
  "basil",
  "pasta",
  "olive oil",
  "bread",
  "lemon",
  "rice",
  "garlic",
  "chickpeas",
  "carrots",
  "potatoes",
  "broccoli",
  "onion",
  "milk",
  "eggs",
  "apple",
  "banana",
  "yogurt",
  "cheese",
];
export const EMOJI = {
  tomatoes: "🍅",
  spinach: "🥬",
  basil: "🌿",
  pasta: "🍝",
  "olive oil": "🫒",
  bread: "🍞",
  lemon: "🍋",
  rice: "🍚",
  garlic: "🧄",
  chickpeas: "🫘",
  carrots: "🥕",
  potatoes: "🥔",
  broccoli: "🥦",
  onion: "🧅",
  milk: "🥛",
  eggs: "🥚",
  apple: "🍎",
  banana: "🍌",
  cheese: "🧀",
};
export const pretty = (s) => s.charAt(0).toUpperCase() + s.slice(1);
export const qty = (n) => Number(Number(n).toFixed(2)).toLocaleString();
export const localDate = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
export const timeLeft = (r) => {
  const m = Math.max(0, Math.ceil((r.deadline * 1000 - Date.now()) / 60000));
  return m >= 60 ? `${Math.ceil(m / 60)}h left` : `${m}m left`;
};
