// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html', // Project-level templates
    './predictor_app/templates/**/*.html', // App-level templates
    './predictor_app/forms.py', // If you add CSS classes directly in forms
    // Add any other paths where you use Tailwind classes (e.g., JavaScript files that manipulate DOM)
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}