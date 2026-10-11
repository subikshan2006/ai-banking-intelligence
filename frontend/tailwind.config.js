/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#070D19',
          900: '#0B1528',
          800: '#112240',
          700: '#1D3557',
          600: '#2A4D7A',
        },
        teal: {
          400: '#2DD4BF',
          500: '#14B8A6',
          600: '#0D9488',
        },
        slate: {
          850: '#151F30',
        }
      }
    },
  },
  plugins: [],
}
