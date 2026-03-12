import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["system-ui", "Segoe UI", "Roboto", "sans-serif"],
        display: ["system-ui", "Segoe UI", "Roboto", "sans-serif"],
      },
      spacing: {
        18: "4.5rem",
        22: "5.5rem",
        30: "7.5rem",
      },
      borderRadius: {
        card: "1rem",
        button: "0.75rem",
      },
      boxShadow: {
        card: "0 4px 6px -1px rgb(0 0 0 / 0.15), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
        cardHover: "0 10px 15px -3px rgb(0 0 0 / 0.15), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
      },
      colors: {
        surface: {
          DEFAULT: "rgb(30 41 59)",
          elevated: "rgb(51 65 85)",
        },
        accent: {
          DEFAULT: "rgb(245 158 11)",
          hover: "rgb(217 119 6)",
          muted: "rgb(251 191 36 / 0.2)",
        },
      },
    },
  },
  plugins: [],
};
export default config;
