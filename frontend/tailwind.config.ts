import type { Config } from 'tailwindcss'

/**
 * Design system do SÓ NO MIGUÉ FC, extraído da logo: preto dominante, branco
 * quente e o laranja queimado como destaque. O laranja é reservado a número de
 * destaque, ação principal, item ativo, série de gráfico e badge de status —
 * nunca como cor de fundo larga.
 *
 * Os nomes seguem o vocabulário do shadcn/ui (background, foreground, primary,
 * muted-foreground...) para que `npx shadcn add <componente>` funcione sem
 * edição manual. Os valores vêm das variáveis CSS de src/styles/index.css.
 *
 * Tailwind v3 (não v4) porque é o caminho que o shadcn/ui documenta com
 * tailwind.config.ts.
 */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        // Texto terciário. Corrigido para #8A8078 na Fase 5: o valor anterior
        // media 3,47 de contraste e reprovava para texto pequeno.
        subtle: {
          foreground: 'hsl(var(--subtle-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          hi: 'hsl(var(--primary-hi))',
        },
        gold: 'hsl(var(--gold))',
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
      },
      fontFamily: {
        display: ['"Barlow Condensed"', '"Arial Narrow"', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        // Escala fixa do design system. Os tamanhos de estatística já vêm com
        // a família condensada e o peso — número de destaque tem sempre a
        // mesma cara, em qualquer tela.
        'stat-xl': ['3.5rem', { lineHeight: '0.9', fontWeight: '800' }],
        stat: ['2rem', { lineHeight: '1', fontWeight: '800' }],
        title: ['1.75rem', { lineHeight: '1.05', fontWeight: '800' }],
        section: ['0.9375rem', { lineHeight: '1.2', letterSpacing: '0.09em', fontWeight: '700' }],
        label: ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.1em' }],
      },
      borderRadius: {
        card: 'var(--radius)',
        control: 'calc(var(--radius) - 0.125rem)',
      },
      spacing: {
        // Altura da barra de navegação inferior no celular.
        nav: '4rem',
        'safe-nav': 'calc(4rem + env(safe-area-inset-bottom))',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'zoom-in': {
          from: { opacity: '0', transform: 'scale(0.97)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 150ms ease-out',
        'zoom-in': 'zoom-in 150ms ease-out',
      },
    },
  },
  plugins: [],
} satisfies Config
