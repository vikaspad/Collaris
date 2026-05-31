/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"IBM Plex Mono"', '"Courier New"', 'monospace']
      },
      colors: {
        bg: {
          base: '#0a0c10',
          surface: 'rgba(255,255,255,0.03)',
          elevated: 'rgba(255,255,255,0.06)'
        },
        status: {
          breach: '#ff4444',
          warning: '#f5a623',
          normal: '#00c97d',
          info: '#0097ff'
        }
      }
    }
  },
  plugins: []
}
