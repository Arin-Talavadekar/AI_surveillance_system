import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],

  theme: {
    extend: {

      colors: {

        panel: '#0f172a',
        panelHeader: '#020617',
        panelBorder: '#1e293b',

        accent: '#22c55e',
        warning: '#facc15',
        danger: '#ef4444',

        slate: {
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155',
          600: '#475569',
          400: '#cbd5e1',
        },

      },

      boxShadow: {
        panel: '0 4px 20px rgba(0,0,0,0.35)',
      },

      borderRadius: {
        xl: '0.9rem',
      },

    },
  },

  plugins: [],
}

export default config