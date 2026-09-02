import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { formatarData } from '@/lib/format'
import type { GoalsPoint } from '@/types/api'

/**
 * Evolução dos gols registrados ao longo da temporada.
 *
 * Este módulo é carregado sob demanda (`React.lazy` em Home.tsx): o Recharts é
 * pesado e o dashboard é a primeira tela que abre no celular. O painel pinta
 * primeiro; o gráfico chega logo depois.
 *
 * As cores vêm dos tokens do design system, lidos das variáveis CSS — sem
 * hexadecimal solto que sairia do lugar se a paleta mudasse.
 */
export default function GoalsOverTimeChart({ pontos }: { pontos: GoalsPoint[] }) {
  const dados = pontos.map((p) => ({
    // Rótulo curto no eixo; a data inteira fica no tooltip.
    rotulo: formatarData(p.match_date).slice(0, 5),
    data: p.match_date,
    gols: p.goals,
  }))

  const primaria = 'hsl(var(--primary))'
  const linhaDeGrade = 'hsl(var(--border))'
  const textoSecundario = 'hsl(var(--muted-foreground))'

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={dados} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="gradienteDeGols" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={primaria} stopOpacity={0.45} />
            <stop offset="100%" stopColor={primaria} stopOpacity={0.02} />
          </linearGradient>
        </defs>

        <CartesianGrid stroke={linhaDeGrade} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="rotulo"
          stroke={textoSecundario}
          tickLine={false}
          axisLine={{ stroke: linhaDeGrade }}
          fontSize={12}
        />
        <YAxis
          stroke={textoSecundario}
          tickLine={false}
          axisLine={false}
          fontSize={12}
          allowDecimals={false}
          width={40}
        />
        <Tooltip
          cursor={{ stroke: linhaDeGrade }}
          contentStyle={{
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: 8,
            color: 'hsl(var(--foreground))',
          }}
          labelFormatter={(_, carga) =>
            carga?.[0] ? formatarData(String(carga[0].payload.data)) : ''
          }
          formatter={(valor: number) => [valor, 'Gols registrados']}
        />
        <Area
          type="monotone"
          dataKey="gols"
          stroke={primaria}
          strokeWidth={2}
          fill="url(#gradienteDeGols)"
          dot={{ fill: primaria, r: 3 }}
          activeDot={{ r: 5 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
