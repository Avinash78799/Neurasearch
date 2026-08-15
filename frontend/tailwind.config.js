/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Celadon Sage Background
        sage: {
          50: "#F4F7F2",
          100: "#EBF0E6",
          200: "#DEE7D7",
          300: "#CCDBC2",
          800: "#242E2B",
          900: "#1A221F",
          950: "#121816",
        },
        // Slate Navy / Charcoal Indigo Container
        slateNavy: {
          400: "#54647C",
          500: "#46546A",
          600: "#3D4A5E", // Exact image primary card color
          700: "#343F50",
          800: "#2B3442",
          900: "#202732",
          950: "#161B23",
        },
        // Ice Blue / Periwinkle Pill & Secondary Panel
        iceBlue: {
          50: "#F5F7FC",
          100: "#EBF0FA",
          200: "#DCE2F0", // Exact image secondary panel #DCE2F0
          300: "#C7D1E8",
          400: "#B0BFDE",
          500: "#98ACD4",
          600: "#7E94C2",
        },
        // Dark Slate text for on-ice-blue components
        slateInk: {
          900: "#1C2430",
          800: "#263140",
          700: "#364559",
        },
      },
      fontFamily: {
        inter: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out forwards",
        "slide-up": "slideUp 0.25s ease-out forwards",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
