import forms from "@tailwindcss/forms";

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        /* Near-black foundation + emerald; steel blue for AI/info */
        background: "#050505",
        surface: "#0E0E10",
        "surface-dim": "#050505",
        "surface-bright": "#2A2A32",
        "surface-container-lowest": "#050505",
        "surface-container-low": "#0E0E10",
        "surface-container": "#16161A",
        "surface-container-high": "#1C1C22",
        "surface-container-highest": "#2A2A32",
        "surface-variant": "#2A2A32",
        "surface-tint": "#18B981",

        primary: "#18B981",
        "primary-container": "#22C995",
        "primary-fixed": "#22C995",
        "primary-fixed-dim": "#18B981",
        "on-primary": "#050505",
        "on-primary-container": "#050505",
        "on-primary-fixed": "#050505",
        "on-primary-fixed-variant": "#050505",
        "inverse-primary": "#18B981",

        /* Muted steel blue — AI / informational */
        tertiary: "#6B9BCF",
        "tertiary-container": "#6B9BCF",
        "tertiary-fixed": "#6B9BCF",
        "tertiary-fixed-dim": "#5A88B8",
        "on-tertiary": "#050505",
        "on-tertiary-container": "#F4F7FB",
        "on-tertiary-fixed": "#050505",
        "on-tertiary-fixed-variant": "#050505",

        secondary: "#9AA8BC",
        "secondary-container": "#16161A",
        "secondary-fixed": "#9AA8BC",
        "secondary-fixed-dim": "#9AA8BC",
        "on-secondary": "#050505",
        "on-secondary-container": "#F4F7FB",
        "on-secondary-fixed": "#050505",
        "on-secondary-fixed-variant": "#9AA8BC",

        "on-surface": "#F4F7FB",
        "on-surface-variant": "#9AA8BC",
        "on-background": "#F4F7FB",
        "inverse-surface": "#F4F7FB",
        "inverse-on-surface": "#050505",

        outline: "#2A2A32",
        "outline-variant": "#2A2A32",

        error: "#F06A6A",
        "error-container": "#3A1A1A",
        "on-error": "#050505",
        "on-error-container": "#F06A6A",

        warning: "#F4B740",
        premium: "#D6B56A",
        info: "#6B9BCF",
      },
      borderRadius: {
        DEFAULT: "0.375rem",
        lg: "0.5rem",
        xl: "0.75rem",
        "2xl": "1rem",
        full: "9999px",
      },
      spacing: {
        xs: "4px",
        sm: "8px",
        base: "4px",
        md: "16px",
        gutter: "20px",
        lg: "24px",
        xl: "32px",
        "2xl": "40px",
        "container-max": "1180px",
      },
      maxWidth: {
        "container-max": "1180px",
      },
      fontFamily: {
        "body-lg": ["Inter", "system-ui", "sans-serif"],
        "label-sm": ["Inter", "system-ui", "sans-serif"],
        "body-md": ["Inter", "system-ui", "sans-serif"],
        "headline-lg": ["Manrope", "Inter", "sans-serif"],
        "headline-md": ["Manrope", "Inter", "sans-serif"],
        "currency-xl": ["Manrope", "Inter", "sans-serif"],
        "display-lg": ["Manrope", "Inter", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Manrope", "Inter", "sans-serif"],
      },
      fontSize: {
        "label-sm": ["11px", { lineHeight: "16px", letterSpacing: "0.04em", fontWeight: "500" }],
        "body-md": ["14px", { lineHeight: "22px", fontWeight: "400" }],
        "body-lg": ["15px", { lineHeight: "24px", fontWeight: "400" }],
        "headline-md": ["18px", { lineHeight: "26px", fontWeight: "600" }],
        "headline-lg": ["24px", { lineHeight: "32px", fontWeight: "700" }],
        "currency-xl": ["28px", { lineHeight: "34px", fontWeight: "700" }],
        "display-lg": ["32px", { lineHeight: "40px", letterSpacing: "-0.02em", fontWeight: "700" }],
      },
      keyframes: {
        fadeUp: {
          from: { transform: "translateY(8px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        slideInRight: {
          from: { transform: "translateX(16px)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
      },
      animation: {
        fadeUp: "fadeUp 0.28s cubic-bezier(0.16,1,0.3,1)",
        slideInRight: "slideInRight 0.25s cubic-bezier(0.16,1,0.3,1)",
      },
      boxShadow: {
        panel: "0 1px 0 rgba(244,247,251,0.04), 0 8px 24px rgba(0,0,0,0.45)",
        glow: "0 0 0 1px rgba(24,185,129,0.25), 0 8px 24px rgba(24,185,129,0.12)",
      },
    },
  },
  plugins: [forms],
};
