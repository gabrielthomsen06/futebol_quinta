import { api } from '@/api/client'
import type { PeriodSelection, Ranking, RankingMetric, Seasons } from '@/types/api'

/** A lista completa pede 100; não há paginação. */
export const LIMITE_DO_RANKING = 100

/**
 * Traduz a escolha da tela em parâmetros da URL.
 *
 * Nenhuma aritmética de calendário acontece aqui: quem converte temporada e
 * mês em datas é o servidor. Isto só repassa o que a pessoa escolheu.
 */
function parametrosDoPeriodo(periodo: PeriodSelection): string[] {
  switch (periodo.mode) {
    case 'season':
      return periodo.season ? [`season=${periodo.season}`] : []
    case 'month':
      return periodo.month ? [`month=${periodo.month}`] : []
    case 'range':
      return [
        ...(periodo.dateFrom ? [`date_from=${periodo.dateFrom}`] : []),
        ...(periodo.dateTo ? [`date_to=${periodo.dateTo}`] : []),
      ]
    case 'all':
      // "Geral" é a ausência de todos os parâmetros.
      return []
  }
}

export function getRanking(
  metric: RankingMetric,
  periodo: PeriodSelection,
): Promise<Ranking> {
  const parametros = [
    `metric=${metric}`,
    `limit=${LIMITE_DO_RANKING}`,
    ...parametrosDoPeriodo(periodo),
  ]
  return api.get<Ranking>(`/rankings?${parametros.join('&')}`)
}

export function getSeasons(): Promise<Seasons> {
  return api.get<Seasons>('/seasons')
}
