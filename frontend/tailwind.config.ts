import type { Config } from 'tailwindcss'

/**
 * Tokens do design system aprovado na Fase 1, extraídos da logo:
 * preto dominante, branco quente, laranja queimado como destaque.
 * O laranja é reservado a número de destaque, ação principal, item ativo,
 * série de gráfico e badge de status — nunca como cor de fundo larga.
 *
 * Tailwind v3 (não v4) porque é o caminho que o shadcn/ui documenta com
 * tailwind.config.ts, e a Fase 5 depende disso.
 */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0A0A0A', // fundo da aplicação
        surface: '#121110', // faixas e barras de navegação
        card: '#1A1715',
        line: '#2E2825',
        fg: '#F6F2ED', // texto principal
        muted: '#9C938B', // texto secundário
        dim: '#6E655D', // texto terciário / desabilitado
        accent: {
          DEFAULT: '#F26B21',
          hi: '#FF9A4D', // laranja para texto pequeno (contraste maior)
          gold: '#F2B33D',
        },
      },
      fontFamily: {
        display: ['"Barlow Condensed"', '"Arial Narrow"', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        // Escala fixa do design system.
        label: ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.1em' }],
      },
      borderRadius: {
        card: '0.5rem',
        control: '0.375rem',
      },
      spacing: {
        // Altura da barra de navegação inferior no celular.
        nav: '4rem',
        'safe-nav': 'calc(4rem + env(safe-area-inset-bottom))',
      },
    },
  },
  plugins: [],
} satisfies Config
