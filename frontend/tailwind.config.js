/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#080C14",
          surface: "#0F1626",
          card: "#141D32",
          border: "#1E2C48",
          borderHover: "#2B3F66",
          accent: "#06B6D4",      // Cyan
          accentHover: "#0891B2",
          teal: "#14B8A6",
          purple: "#A855F7",
          crimson: "#F43F5E",
          amber: "#F59E0B",
          emerald: "#10B981",
        }
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      }
    },
  },
  plugins: [],
}
