import { RankingItem } from '@/components/rankings/RankingItem'
import { LIMITE_DO_RANKING } from '@/api/rankings'
import type { RankingEntry, RankingMetric } from '@/types/api'

interface RankingListProps {
  entries: RankingEntry[]
  metric: RankingMetric
}

export function RankingList({ entries, metric }: RankingListProps) {
  return (
    <>
      <ol className="rounded-card border border-border bg-card px-4">
        {entries.map((entrada) => (
          <RankingItem key={entrada.player.id} entrada={entrada} metric={metric} />
        ))}
      </ol>

      {/* Não há paginação, e 100 não é garantia de "todo mundo": se a lista
          encostar no teto, é honesto avisar em vez de dar a entender que
          aquilo é o grupo inteiro. Com ~14 jogadores isso não acontece hoje. */}
      {entries.length >= LIMITE_DO_RANKING && (
        <p className="mt-3 text-sm text-muted-foreground">
          Mostrando os {LIMITE_DO_RANKING} primeiros. Há mais jogadores no período.
        </p>
      )}
    </>
  )
}
