/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        crimsonBlack: {
          950: "#09070a",
          900: "#120c13",
          850: "#170f1a",
          800: "#1e1421",
          700: "#291b2e",
          600: "#3d2844",
        },
        turquoise: {
          50: "#f0fdfa",
          100: "#ccfbf1",
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#134e4a",
        },
        brand: {
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
        },
      },
      fontFamily: {
        inter: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.25s ease-out forwards",
        "slide-up": "slideUp 0.3s ease-out forwards",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
