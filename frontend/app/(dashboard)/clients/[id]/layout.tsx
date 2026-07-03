'use client'

import { useParams, usePathname } from 'next/navigation'
import Link from 'next/link'
import { Loader2, Building2 } from 'lucide-react'
import { useClient } from '@/hooks/use-clients'
import { cn } from '@/lib/utils'

const TABS = [
  { label: 'Anagrafica', href: '' },
  { label: 'Prima Nota', href: '/journal' },
  { label: 'IVA', href: '/vat' },
  { label: 'Bilancio', href: '/balance' },
  { label: 'Banca', href: '/bank' },
  { label: 'Conservazione', href: '/conservatore' },
]

export default function ClientDetailLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const params = useParams<{ id: string }>()
  const pathname = usePathname()
  const { data: client, isLoading } = useClient(params.id)

  return (
    <div className="flex flex-col h-full">
      {/* Sub-header */}
      <div className="border-b bg-card px-6 py-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10">
            <Building2 className="h-4 w-4 text-primary" />
          </div>
          {isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Caricamento...</span>
            </div>
          ) : (
            <div>
              <h2 className="text-lg font-semibold leading-none">
                {client?.ragione_sociale ?? '—'}
              </h2>
              {client?.partita_iva && (
                <p className="text-xs text-muted-foreground mt-0.5">
                  P.IVA {client.partita_iva}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Tab navigation */}
        <nav className="flex gap-1 -mb-px" aria-label="Sezioni cliente">
          {TABS.map((tab) => {
            const href = `/clients/${params.id}${tab.href}`
            const isActive = tab.href === ''
              ? pathname === `/clients/${params.id}`
              : pathname.startsWith(`/clients/${params.id}${tab.href}`)

            return (
              <Link
                key={tab.label}
                href={href}
                className={cn(
                  'px-3 py-2 text-sm font-medium border-b-2 transition-colors',
                  isActive
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                )}
              >
                {tab.label}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Page content */}
      <div className="flex-1 overflow-y-auto">{children}</div>
    </div>
  )
}
