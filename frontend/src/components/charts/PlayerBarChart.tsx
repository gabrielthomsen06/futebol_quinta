import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

/**
 * Barras horizontais dos primeiros colocados.
 *
 * Carregado sob demanda, e o Vite reaproveita o mesmo chunk do Recharts criado
 * na Fase 8 — a biblioteca não entra duas vezes no bundle.
 *
 * **Só desenha o que a API mandou.** Nada é somado, ordenado ou derivado aqui:
 * as barras são exatamente as entradas que a lista logo acima já mostra.
 */
export interface BarraDoGrafico {
  nome: string
  valor: number
}

export default function PlayerBarChart({
  dados,
  rotulo,
}: {
  dados: BarraDoGrafico[]
  rotulo: string
}) {
  const primaria = 'hsl(var(--primary))'
  const secundaria = 'hsl(var(--primary) / 0.45)'
  const linhaDeGrade = 'hsl(var(--border))'
  const textoSecundario = 'hsl(var(--muted-foreground))'

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={dados} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke={linhaDeGrade} strokeDasharray="3 3" horizontal={false} />
        <XAxis
          type="number"
          stroke={textoSecundario}
          tickLine={false}
          axisLine={{ stroke: linhaDeGrade }}
          fontSize={12}
          allowDecimals={false}
        />
        <YAxis
          type="category"
          dataKey="nome"
          stroke={textoSecundario}
          tickLine={false}
          axisLine={false}
          fontSize={12}
          width={90}
        />
        <Tooltip
          cursor={{ fill: 'hsl(var(--muted))' }}
          contentStyle={{
            background: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: 8,
            color: 'hsl(var(--foreground))',
          }}
          formatter={(valor: number) => [valor, rotulo]}
        />
        <Bar dataKey="valor" radius={[0, 4, 4, 0]}>
          {/* O líder em laranja cheio; os demais mais apagados, para a
              hierarquia da lista se repetir no gráfico. */}
          {dados.map((barra, indice) => (
            <Cell key={barra.nome} fill={indice === 0 ? primaria : secundaria} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
