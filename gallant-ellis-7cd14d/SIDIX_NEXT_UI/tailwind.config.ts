import type { Config } from "tailwindcss";

// SIDIX brand tokens — locked 2026-04-30 (FOUNDER_JOURNAL line 1041+)
// Source brand kit: image 3 dari bos (Bogor neon palette)
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // SIDIX brand palette (#7C5CFF #00D2FF #FF6EC7 #0B0F2A #FFFFFF)
        sidix: {
          purple: "#7C5CFF",
          cyan: "#00D2FF",
          pink: "#FF6EC7",
          dark: "#0B0F2A",
          darker: "#080F1A",  // dari Home.tsx scaffolding
          surface: "#151A2E", // dari LeftSidebar.tsx scaffolding
        },
      },
      fontFamily: {
        grotesk: ['"Space Grotesk"', "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        float: "float 3s ease-in-out infinite",
      },
      keyframes: {
        "pulse-glow": {
          "0%, 100%": { opacity: "1", filter: "drop-shadow(0 0 8px currentColor)" },
          "50%": { opacity: "0.7", filter: "drop-shadow(0 0 16px currentColor)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
