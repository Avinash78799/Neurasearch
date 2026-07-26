/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        lavender: {
          50: "#faf8ff",
          100: "#f3eefd",
          200: "#e4d7fe",
          300: "#cbb2fe",
          400: "#b18bfd",
          500: "#9860f7",
          600: "#813eed",
          700: "#6c29d6",
          800: "#221838",
          900: "#120c24",
          950: "#0b0717",
        },
        dark: {
          900: "#0e091d",
          800: "#16102a",
          700: "#221838",
          600: "#362759",
        },
        neon: {
          cyan: "#7dd3fc",
          emerald: "#6ee7b7",
          violet: "#b8a5fe",
          amber: "#fde047",
          rose: "#f472b6",
          lavender: "#d8b4fe",
        },
      },
      fontFamily: {
        inter: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "slide-up": "slideUp 0.4s ease-out forwards",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 8px rgba(6,182,212,0.3)" },
          "50%": { boxShadow: "0 0 20px rgba(6,182,212,0.6)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};
