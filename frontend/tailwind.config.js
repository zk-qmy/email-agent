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
          DEFAULT: '#e84b5a',
          hover: '#d03a48',
          light: '#fff0f1',
        },
        success: {
          DEFAULT: '#10b981',
          light: '#ecfdf5',
        },
        danger: {
          DEFAULT: '#e84b5a',
          light: '#fff0f1',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: '#fffbeb',
        },
        bg: '#f4f5f9',
        card: '#ffffff',
        border: '#e8e8f0',
        'border-input': '#e0e1eb',
        'border-focus': '#e84b5a',
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