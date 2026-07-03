'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  Users,
  BookOpen,
  Receipt,
  BarChart3,
  Landmark,
  Building2,
  Settings,
} from 'lucide-react'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

interface Command {
  id: string
  label: string
  description?: string
  icon: React.ReactNode
  href: string
}

const commands: Command[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    description: 'Panoramica generale',
    icon: <LayoutDashboard className="h-4 w-4" />,
    href: '/dashboard',
  },
  {
    id: 'clienti',
    label: 'Clienti',
    description: 'Gestione clienti e fornitori',
    icon: <Users className="h-4 w-4" />,
    href: '/clienti',
  },
  {
    id: 'prima-nota',
    label: 'Prima Nota',
    description: 'Registro movimenti contabili',
    icon: <BookOpen className="h-4 w-4" />,
    href: '/prima-nota',
  },
  {
    id: 'iva',
    label: 'IVA',
    description: 'Liquidazione e registri IVA',
    icon: <Receipt className="h-4 w-4" />,
    href: '/iva',
  },
  {
    id: 'bilancio',
    label: 'Bilancio',
    description: 'Bilancio e situazione patrimoniale',
    icon: <BarChart3 className="h-4 w-4" />,
    href: '/bilancio',
  },
  {
    id: 'banca',
    label: 'Banca',
    description: 'Movimenti bancari e riconciliazione',
    icon: <Landmark className="h-4 w-4" />,
    href: '/banca',
  },
  {
    id: 'studio',
    label: 'Studio',
    description: 'Gestione studio professionale',
    icon: <Building2 className="h-4 w-4" />,
    href: '/studio',
  },
  {
    id: 'impostazioni',
    label: 'Impostazioni',
    description: 'Configurazione e preferenze',
    icon: <Settings className="h-4 w-4" />,
    href: '/impostazioni',
  },
]

function fuzzyMatch(query: string, text: string): boolean {
  if (!query) return true
  const q = query.toLowerCase()
  const t = text.toLowerCase()
  let qi = 0
  for (let i = 0; i < t.length && qi < q.length; i++) {
    if (t[i] === q[qi]) qi++
  }
  return qi === q.length
}

export function CommandPalette() {
  const [open, setOpen] = React.useState(false)
  const [query, setQuery] = React.useState('')
  const [activeIndex, setActiveIndex] = React.useState(0)
  const router = useRouter()
  const inputRef = React.useRef<HTMLInputElement>(null)

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  React.useEffect(() => {
    if (open) {
      setQuery('')
      setActiveIndex(0)
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [open])

  const filtered = commands.filter(
    (cmd) =>
      fuzzyMatch(query, cmd.label) ||
      (cmd.description && fuzzyMatch(query, cmd.description))
  )

  React.useEffect(() => {
    setActiveIndex(0)
  }, [query])

  const handleSelect = (cmd: Command) => {
    setOpen(false)
    router.push(cmd.href)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      if (filtered[activeIndex]) {
        handleSelect(filtered[activeIndex])
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="p-0 gap-0 max-w-lg overflow-hidden">
        <div className="flex items-center border-b px-3">
          <svg
            className="mr-2 h-4 w-4 shrink-0 opacity-50"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Cerca comandi..."
            className="flex h-12 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
          />
          <kbd className="pointer-events-none ml-2 hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100 sm:flex">
            ESC
          </kbd>
        </div>

        <div className="max-h-80 overflow-y-auto p-1">
          {filtered.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted-foreground">
              Nessun risultato trovato.
            </div>
          ) : (
            <div>
              <p className="px-2 py-1.5 text-xs font-medium text-muted-foreground">
                Naviga
              </p>
              {filtered.map((cmd, index) => (
                <button
                  key={cmd.id}
                  className={cn(
                    'flex w-full items-center gap-3 rounded-sm px-2 py-2 text-sm outline-none transition-colors',
                    index === activeIndex
                      ? 'bg-accent text-accent-foreground'
                      : 'hover:bg-accent hover:text-accent-foreground'
                  )}
                  onMouseEnter={() => setActiveIndex(index)}
                  onClick={() => handleSelect(cmd)}
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border bg-background text-muted-foreground">
                    {cmd.icon}
                  </span>
                  <div className="flex flex-col items-start">
                    <span className="font-medium">{cmd.label}</span>
                    {cmd.description && (
                      <span className="text-xs text-muted-foreground">
                        {cmd.description}
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 border-t px-3 py-2">
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <kbd className="pointer-events-none inline-flex h-5 select-none items-center rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
              ↑↓
            </kbd>
            naviga
          </span>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <kbd className="pointer-events-none inline-flex h-5 select-none items-center rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
              ↵
            </kbd>
            seleziona
          </span>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <kbd className="pointer-events-none inline-flex h-5 select-none items-center rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
              ESC
            </kbd>
            chiudi
          </span>
        </div>
      </DialogContent>
    </Dialog>
  )
}
