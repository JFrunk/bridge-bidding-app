/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Bridge-specific colors
        'success': '#4caf50',
        'danger': '#f44336',
        'info': '#61dafb',
        'suit-red': '#d32f2f',
        'suit-black': '#000000',

        // Partnership colors
        'partnership-ns': '#4caf50',
        'partnership-ew': '#ff9800',

        // Backgrounds
        'bg-primary': '#1a1a1a',
        'bg-secondary': '#2a2a2a',
        'bg-tertiary': '#3a3a3a',

        // Special states
        'highlight-current': '#61dafb',
        'highlight-winner': '#ffd700',
      },
      spacing: {
        // Add custom spacing to match existing design
        '15': '3.75rem',
      },
      borderRadius: {
        'card': '6px',
      },
    },
  },
  plugins: [],
}
