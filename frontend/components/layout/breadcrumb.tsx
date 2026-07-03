'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { ChevronRight, Home } from 'lucide-react'

const SEGMENT_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  clients: 'Clienti',
  studio: 'Studio',
  settings: 'Impostazioni',
  journal: 'Prima Nota',
  vat: 'IVA',
  balance: 'Bilancio',
  bank: 'Banca',
  conservatore: 'Conservazione',
  'new': 'Nuovo',
}

function labelForSegment(segment: string): string {
  const known = SEGMENT_LABELS[segment.toLowerCase()]
  if (known) return known
  // UUID-like or long IDs → "Dettaglio"
  if (segment.length > 20 || /^[0-9a-f-]{8,}$/i.test(segment)) return 'Dettaglio'
  // Capitalize first letter otherwise
  return segment.charAt(0).toUpperCase() + segment.slice(1)
}

export function Breadcrumb() {
  const pathname = usePathname()

  const segments = pathname.split('/').filter(Boolean)

  if (segments.length === 0) {
    return (
      <nav aria-label="breadcrumb" className="flex items-center gap-1 text-sm">
        <span className="flex items-center gap-1 text-slate-900 dark:text-slate-100 font-medium">
          <Home className="w-3.5 h-3.5" />
          Home
        </span>
      </nav>
    )
  }

  type Crumb = { label: string; href: string; isLast: boolean }

  const crumbs: Crumb[] = segments.map((seg, idx) => ({
    label: labelForSegment(seg),
    href: '/' + segments.slice(0, idx + 1).join('/'),
    isLast: idx === segments.length - 1,
  }))

  return (
    <nav aria-label="breadcrumb" className="flex items-center gap-1 text-sm overflow-hidden">
      <Link
        href="/"
        className="flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors flex-shrink-0"
        aria-label="Home"
      >
        <Home className="w-3.5 h-3.5" />
      </Link>

      {crumbs.map((crumb) => (
        <span key={crumb.href} className="flex items-center gap-1 min-w-0">
          <ChevronRight className="w-3.5 h-3.5 text-slate-300 dark:text-slate-600 flex-shrink-0" />
          {crumb.isLast ? (
            <span className="font-medium text-slate-900 dark:text-slate-100 truncate">
              {crumb.label}
            </span>
          ) : (
            <Link
              href={crumb.href}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors truncate"
            >
              {crumb.label}
            </Link>
          )}
        </span>
      ))}
    </nav>
  )
}
