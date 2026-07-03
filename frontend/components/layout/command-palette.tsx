'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Search, LayoutDashboard, Users, BookOpen, Receipt, BarChart3, Package, CreditCard, Archive, CheckSquare2, Building2, Settings } from 'lucide-react'

const COMMANDS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { id: 'clients', label: 'Clienti', icon: Users, href: '/clients' },
  { id: 'journal', label: 'Prima Nota', icon: BookOpen, href: '/clients' },
  { id: 'vat', label: 'IVA', icon: Receipt, href: '/clients' },
  { id: 'balance', label: 'Bilancio', icon: BarChart3, href: '/clients' },
  { id: 'assets', label: 'Cespiti', icon: Package, href: '/clients' },
  { id: 'bank', label: 'Riconciliazione Bancaria', icon: CreditCard, href: '/clients' },
  { id: 'archive', label: 'Conservazione Documenti', icon: Archive, href: '/clients' },
  { id: 'tasks', label: 'Task Studio', icon: CheckSquare2, href: '/studio' },
  { id: 'studio', label: 'Dashboard Studio', icon: Building2, href: '/studio' },
  { id: 'settings', label: 'Impostazioni', icon: Settings, href: '/settings' },
]

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const router = useRouter()

  const filtered = query.trim()
    ? COMMANDS.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()))
    : COMMANDS

  const handleOpen = useCallback(() => {
    setOpen(true)
    setQuery('')
  }, [])

  const handleClose = useCallback(() => {
    setOpen(false)
    setQuery('')
  }, [])

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
        setQuery('')
      }
      if (e.key === 'Escape') {
        handleClose()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [handleClose])

  function navigate(href: string) {
    router.push(href)
    handleClose()
  }

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
      onClick={handleClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 dark:bg-black/60" />

      {/* Panel */}
      <div
        className="relative w-full max-w-lg mx-4 bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-100 dark:border-slate-800">
          <Search className="w-4 h-4 text-slate-400 flex-shrink-0" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Cerca pagine e azioni..."
            className="flex-1 bg-transparent text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none"
          />
          <kbd className="text-xs text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
            Esc
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-72 overflow-y-auto py-2">
          {filtered.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-6">Nessun risultato trovato</p>
          ) : (
            filtered.map((cmd) => (
              <button
                key={cmd.id}
                onClick={() => navigate(cmd.href)}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                <cmd.icon className="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span className="text-sm text-slate-700 dark:text-slate-300">{cmd.label}</span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export function CommandPaletteButton() {
  function trigger() {
    window.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true })
    )
  }

  return (
    <button
      onClick={trigger}
      className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-xs"
      aria-label="Apri command palette"
    >
      <Search className="w-3.5 h-3.5" />
      <span>Cerca</span>
      <kbd className="font-mono bg-slate-100 dark:bg-slate-800 px-1 rounded text-[10px]">
        Ctrl+K
      </kbd>
    </button>
  )
}
