'use client'

import { useRouter } from 'next/navigation'
import { LogOut, ChevronDown, User } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/providers/auth-provider'
import { Breadcrumb } from './breadcrumb'
import { CommandPaletteButton } from './command-palette'
import { ThemeToggle } from '@/components/theme-toggle'

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [open])

  const initials = user
    ? `${user.nome?.[0] ?? ''}${user.cognome?.[0] ?? ''}`.toUpperCase() || user.email[0].toUpperCase()
    : '?'

  const displayName = user ? `${user.nome ?? ''} ${user.cognome ?? ''}`.trim() || user.email : ''

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 h-8 px-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        aria-expanded={open}
        aria-haspopup="true"
      >
        {/* Avatar */}
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-semibold flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #7c3aed 100%)' }}
        >
          {initials}
        </div>
        <span className="hidden md:block text-sm font-medium text-slate-700 dark:text-slate-300 max-w-[140px] truncate">
          {displayName}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
      </button>

      {open && (
        <div className="absolute right-0 mt-1 w-52 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-lg py-1 z-50">
          <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800">
            <p className="text-xs font-medium text-slate-900 dark:text-slate-100 truncate">{displayName}</p>
            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          </div>
          <button
            onClick={() => { setOpen(false); logout() }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Disconnetti
          </button>
        </div>
      )}
    </div>
  )
}

export function Topbar() {
  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-30 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      {/* Left: breadcrumb */}
      <div className="flex-1 min-w-0 mr-4">
        <Breadcrumb />
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <CommandPaletteButton />
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  )
}
