/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Outfit", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        surface: {
          DEFAULT: "#0b1120",
          light: "#f8fafc",
        },
        signal: {
          50: "#ecfdf5",
          300: "#7dd8bb",
          400: "#3fceA0",
          500: "#22b788",
          600: "#189a71",
          800: "#0f5e46",
          950: "#062019",
        },
      },
      boxShadow: {
        panel: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 12px 32px -16px rgba(0,0,0,0.65)",
        "panel-hover": "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 16px 40px -14px rgba(0,0,0,0.7)",
        glow: "0 0 0 1px rgba(63,206,160,0.25), 0 0 24px -4px rgba(63,206,160,0.35)",
      },
      letterSpacing: {
        tightest: "-0.03em",
      },
    },
  },
  plugins: [],
};
