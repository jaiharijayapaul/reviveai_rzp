/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        risk: "#ef4444",
        recovered: "#22c55e",
        pending: "#f59e0b",
        brand: {
          50: "#eef2ff", 100: "#e0e7ff", 500: "#6366f1", 600: "#4f46e5", 700: "#4338ca",
        },
      },
    },
  },
  plugins: [],
};
