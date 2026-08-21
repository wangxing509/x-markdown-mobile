/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Noto Sans', 'system-ui', 'sans-serif'],
        serif: ['Noto Serif SC', 'Georgia', 'serif'],
      },
      colors: {
        primary: { DEFAULT: '#2563EB', dark: '#1E40AF', light: '#3B82F6' },
        accent: { green: '#10B981', amber: '#F59E0B', red: '#EF4444' },
        surface: { light: '#F8FAFC', white: '#FFFFFF', dark: '#1E293B' },
      },
      boxShadow: {
        soft: '0 2px 12px rgba(0,0,0,0.06)',
        glow: '0 0 24px rgba(37,99,235,0.15)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { transform: 'translateY(8px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
      },
    },
  },
  plugins: [],
}
