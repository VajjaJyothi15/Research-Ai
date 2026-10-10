/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        theme: {
          page: '#EDE9FE',
          secondary: '#DBEAFE',
          content: '#E5E7F9',
          sidebar: '#DCD6FA',
          cardLavender: '#E9E4FF',
          cardBlue: '#DCEBFF',
          cardMint: '#DDF7F0',
          border: '#C4B5FD',
          indigo: '#635BFF',
          indigoHover: '#4F46E5',
          teal: '#0F9D91',
          tealHover: '#0D887E',
          heading: '#312E81',
          body: '#334155',
        },
      },
    },
  },
  plugins: [],
}
