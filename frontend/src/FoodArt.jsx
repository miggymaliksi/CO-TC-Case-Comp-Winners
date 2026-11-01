import React from "react";

// Original vector illustrations keep the demo self-contained and usable offline.
export default function FoodArt({ kind = "pasta", id = "food" }) {
  const colors = {
    pasta: "#dfb17f",
    toast: "#d6c29b",
    bowl: "#a8baa0",
    greens: "#b1be8a",
  };
  const seed = [...id].reduce((a, c) => a + c.charCodeAt(0), 0);
  const rand = (n) => {
    const v = Math.sin(n * 127.1 + seed) * 43758.5453;
    return v - Math.floor(v);
  };
  const leaves = Array.from({ length: kind === "bowl" ? 32 : 12 }, (_, i) => ({
    x: 90 + rand(i + 1) * 140,
    y: 50 + rand(i + 40) * 130,
    r: rand(i + 70) * 360,
  }));
  return (
    <svg
      viewBox="0 0 320 230"
      role="img"
      aria-label={`${kind === "toast" ? "Tomato toast" : kind === "bowl" ? "Rice and greens bowl" : kind === "greens" ? "Spinach pasta" : "Tomato and basil pasta"} illustration`}
      className="food-art"
    >
      <defs>
        <filter id={`shadow-${id}`}>
          <feDropShadow dx="0" dy="8" stdDeviation="8" floodOpacity=".14" />
        </filter>
        <pattern
          id={`grain-${id}`}
          width="6"
          height="6"
          patternUnits="userSpaceOnUse"
        >
          <circle cx="2" cy="1" r=".45" fill="#fff" opacity=".17" />
        </pattern>
      </defs>
      <rect width="320" height="230" fill={colors[kind]} />
      <path d="M-10 190L70 0H135L50 230Z" fill="#fff" opacity=".11" />
      <path d="M285 0L320 13V230H253Z" fill="#eee5d1" opacity=".7" />
      <ellipse
        cx="159"
        cy="118"
        rx="112"
        ry="96"
        fill="#f9f5e9"
        filter={`url(#shadow-${id})`}
      />
      <ellipse cx="159" cy="118" rx="92" ry="79" fill="#e9e4d5" />
      {kind === "toast" ? (
        <g transform="rotate(-12 160 115)">
          <rect x="85" y="60" width="145" height="108" rx="20" fill="#926334" />
          <rect x="91" y="65" width="133" height="97" rx="18" fill="#dba868" />
          {Array.from({ length: 16 }, (_, i) => (
            <ellipse
              key={i}
              cx={105 + rand(i) * 103}
              cy={82 + rand(i + 22) * 63}
              rx="12"
              ry="9"
              fill={i % 3 ? "#c7482c" : "#e56f43"}
              transform={`rotate(${i * 40} 160 115)`}
            />
          ))}
        </g>
      ) : (
        <g>
          {kind === "bowl" ? (
            <>
              {Array.from({ length: 100 }, (_, i) => (
                <ellipse
                  key={i}
                  cx={90 + rand(i) * 137}
                  cy={65 + rand(i + 52) * 105}
                  rx="4"
                  ry="1.6"
                  fill={i % 3 ? "#f3e6c7" : "#d9c7a2"}
                  transform={`rotate(${i * 31} 160 115)`}
                />
              ))}
              {Array.from({ length: 20 }, (_, i) => (
                <circle
                  key={i}
                  cx={100 + rand(i + 120) * 120}
                  cy={80 + rand(i + 180) * 80}
                  r="5"
                  fill="#d4ae68"
                />
              ))}
            </>
          ) : (
            Array.from({ length: 48 }, (_, i) => (
              <path
                key={i}
                d={`M${96 + rand(i) * 123},${65 + rand(i + 30) * 100}q${rand(i + 10) * 45 - 20},-18 25,12t-15,15`}
                fill="none"
                stroke={
                  kind === "greens"
                    ? i % 3
                      ? "#d2ba69"
                      : "#8a9c4e"
                    : i % 3
                      ? "#dfa65a"
                      : "#c36336"
                }
                strokeWidth="5"
                strokeLinecap="round"
              />
            ))
          )}
        </g>
      )}
      {kind === "pasta" &&
        Array.from({ length: 8 }, (_, i) => (
          <ellipse
            key={i}
            cx={100 + rand(i + 200) * 120}
            cy={70 + rand(i + 251) * 95}
            rx="11"
            ry="8"
            fill="#b84329"
          />
        ))}
      {leaves.map((l, i) => (
        <g key={i} transform={`translate(${l.x} ${l.y}) rotate(${l.r})`}>
          <path
            d="M0 0Q-16-19 0-25Q16-15 0 0"
            fill={i % 2 ? "#315c36" : "#54844a"}
          />
          <path d="M0-2V-22" stroke="#91a867" strokeWidth=".8" />
        </g>
      ))}
      {kind === "bowl" && (
        <g transform="translate(204 136) rotate(22)">
          <path d="M-25 0A25 25 0 0 1 25 0Z" fill="#e9cc57" />
          <path d="M-21-2A21 21 0 0 1 21-2Z" fill="#f8e8a3" />
          <path
            d="M0-2L-13-16M0-2V-22M0-2L13-16"
            stroke="#fef6dc"
            strokeWidth="2"
          />
        </g>
      )}
      <rect width="320" height="230" fill={`url(#grain-${id})`} />
      <path
        d="M23 181l11-53m-6 22l-8-4m10-4l-7-4m13-3l-7-4"
        stroke="#65774c"
        strokeWidth="2"
        fill="none"
      />
    </svg>
  );
}
