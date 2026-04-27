import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef7ff",
          100: "#d9edff",
          200: "#bce1ff",
          300: "#90ceff",
          400: "#5ab2ff",
          500: "#2b91ff",
          600: "#1572f5",
          700: "#115be0",
          800: "#144bb5",
          900: "#16428f"
        }
      },
      boxShadow: {
        soft: "0 8px 30px rgba(21, 114, 245, 0.12)"
      }
    }
  },
  plugins: []
};

export default config;

