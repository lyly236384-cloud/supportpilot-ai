/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#EFF6FF",
          100: "#DBEAFE",
          200: "#BFDBFE",
          300: "#93C5FD",
          400: "#60A5FA",
          500: "#3B82F6",
          600: "#2563EB",
          700: "#1D4ED8",
          800: "#1E40AF",
          900: "#1E3A8A",
          950: "#172554",
        },
        ink: "#0F172A",
        muted: "#64748B",
        line: "#DCE4EF",
        page: "#F6F8FB",
        surface: "#FFFFFF",
        // Semantic colors
        success: {
          light: "#ECFDF5",
          DEFAULT: "#059669",
          dark: "#065F46",
        },
        warning: {
          light: "#FFFBEB",
          DEFAULT: "#D97706",
          dark: "#92400E",
        },
        danger: {
          light: "#FEF2F2",
          DEFAULT: "#DC2626",
          dark: "#991B1B",
        },
      },
      boxShadow: {
        // Layered elevation system (0 = lowest, 100 = highest)
        xs: "0 1px 2px rgba(15, 23, 42, 0.04)",
        sm: "0 2px 8px rgba(15, 23, 42, 0.06)",
        card: "0 16px 40px rgba(15, 23, 42, 0.08)",
        "card-hover": "0 24px 60px rgba(15, 23, 42, 0.12)",
        "button-primary": "0 10px 24px rgba(37, 99, 235, 0.24)",
        "button-primary-hover": "0 12px 30px rgba(37, 99, 235, 0.32)",
        modal: "0 24px 64px rgba(15, 23, 42, 0.16)",
        nav: "0 1px 3px rgba(15, 23, 42, 0.04), 0 4px 12px rgba(15, 23, 42, 0.04)",
        // Soft glow for accent elements
        glow: "0 0 24px rgba(37, 99, 235, 0.12)",
        "glow-lg": "0 0 48px rgba(37, 99, 235, 0.16)",
      },
      borderRadius: {
        "2.5xl": "1.25rem",
        "4xl": "2rem",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "fade-in-up": "fadeInUp 0.4s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "slide-in-left": "slideInLeft 0.3s ease-out",
        "scale-in": "scaleIn 0.2s ease-out",
        "shimmer": "shimmer 1.5s infinite",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        slideInLeft: {
          "0%": { opacity: "0", transform: "translateX(-16px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
      },
      transitionDuration: {
        DEFAULT: "200ms",
      },
    },
  },
  plugins: [],
};
