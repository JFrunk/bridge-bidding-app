/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Clubhouse Theme - UI_UX_CONSTITUTION.md
        'clubhouse-green': '#1B4D3E',      // Primary Game Surface
        'clubhouse-green-dark': '#143D31', // Darker variant
        'clubhouse-green-light': '#245E4D',// Lighter variant
        'clubhouse-beige': '#FDFBF7',      // Primary Canvas
        'clubhouse-beige-dark': '#F5F2EC', // Darker beige
        'accent-gold': '#EAB308',          // Your Turn highlights

        // Bridge-specific colors
        'success': '#4caf50',
        'danger': '#f44336',
        'info': '#61dafb',
        'suit-red': '#dc2626',  // text-red-600 equivalent
        'suit-black': '#111827', // text-gray-900 equivalent

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
