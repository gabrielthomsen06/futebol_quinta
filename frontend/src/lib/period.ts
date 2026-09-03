import type { PeriodSelection } from '@/types/api'

/**
 * Recorte de período, compartilhado por Rankings e Histórico.
 *
 * Nenhuma aritmética de calendário acontece aqui: quem converte temporada e mês
 * em datas é o servidor, com `resolver_periodo()`. Isto só repassa a escolha.
 */
export function parametrosDoPeriodo(periodo: PeriodSelection): string[] {
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

/**
 * Assinatura estável do período, para compor chave de cache.
 *
 * É o que garante que "Realizadas de agosto" e "Todas de 2026" nunca
 * compartilhem páginas: chaves diferentes, queries diferentes.
 */
export function chaveDoPeriodo(periodo: PeriodSelection): string {
  switch (periodo.mode) {
    case 'season':
      return `season:${periodo.season ?? ''}`
    case 'month':
      return `month:${periodo.month ?? ''}`
    case 'range':
      return `range:${periodo.dateFrom ?? ''}:${periodo.dateTo ?? ''}`
    case 'all':
      return 'all'
  }
}
