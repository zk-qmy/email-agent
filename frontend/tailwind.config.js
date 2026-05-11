/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1d7c93',
          hover: '#15803d',
          light: '#d9f99d',
        },
        success: {
          DEFAULT: '#10b981',
          light: '#ecfdf5',
        },
        danger: {
          DEFAULT: '#a1a932',
          light: '#dcfce7',
        },
        warning: {
          DEFAULT: '#9e1d2c',
          light: '#dcfce7',
        },
        bg: '#f4f5f9',
        card: '#ffffff',
        border: '#e8e8f0',
        'border-input': '#e0e1eb',
        'border-focus': '#16a34a',
        text: '#111827',
        'text-secondary': '#6b7280',
        'text-muted': '#9ca3af',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}