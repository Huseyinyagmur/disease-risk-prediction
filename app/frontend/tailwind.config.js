/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        // Yerel sistem yazı tipleri: harici yazı tipi isteği yok (localhost dışına çıkış yok)
        sans: ['"Segoe UI"', 'system-ui', '-apple-system', 'Roboto', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
