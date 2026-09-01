import { BarChart3, CalendarDays, Home, Users, type LucideIcon } from 'lucide-react'

export interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  end?: boolean
}

/** Fonte única das quatro áreas — consumida pela navbar e pela barra inferior. */
export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Início', icon: Home, end: true },
  { to: '/rankings', label: 'Rankings', icon: BarChart3 },
  { to: '/historico', label: 'Histórico', icon: CalendarDays },
  { to: '/jogadores', label: 'Jogadores', icon: Users },
]
