/**
 * Formatação brasileira.
 *
 * Média sai com vírgula (1,31) e percentual com uma casa (56,3%), como manda
 * a convenção daqui — e como estava no desenho aprovado.
 */

const MEDIA = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const PERCENTUAL = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})

export function formatarMedia(valor: number): string {
  return MEDIA.format(valor)
}

export function formatarPercentual(valor: number): string {
  return `${PERCENTUAL.format(valor)}%`
}

/**
 * Data da partida, sempre dd/mm/aaaa.
 *
 * A API manda `2026-09-04` puro, sem hora. Montar com `new Date(iso)` faria o
 * navegador interpretar como UTC e, num fuso negativo como o nosso, exibir o
 * dia anterior — a partida de quinta viraria quarta.
 */
export function formatarData(iso: string): string {
  const [ano, mes, dia] = iso.slice(0, 10).split('-')
  return `${dia}/${mes}/${ano}`
}

/** "12 gols" / "1 gol" — plural sem gambiarra de concatenar "(s)". */
export function pluralizar(quantidade: number, singular: string, plural: string): string {
  return `${quantidade} ${quantidade === 1 ? singular : plural}`
}
