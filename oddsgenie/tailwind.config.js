/** @type {import('tailwindcss').Config} */
module.exports = {
   content: [
     "./src/**/*.{js,jsx,ts,tsx}",
   ],
   theme: {
     extend: {
        backgroundImage: {
            'homepage_background': "url('/public/homepage_background.jpg')",
        }
     },
   },
   plugins: [],
 }