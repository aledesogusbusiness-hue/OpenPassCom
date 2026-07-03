'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import { useAuth } from '@/providers/auth-provider'
import {
  LayoutDashboard,
  Users,
  BookOpen,
  Receipt,
  BarChart3,
  Package,
  CreditCard,
  Archive,
  CheckSquare2,
  Building2,
  Settings,
  ChevronDown,
  ChevronUp,
  LogOut,
} from 'lucide-react'
import { cn } from '@/lib/utils'

type NavItem = {
  label: string
  icon: React.ElementType
  href: string
}

type NavSection = {
  title: string
  items: NavItem[]
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: 'OVERVIEW',
    items: [
      { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
    ],
  },
  {
    title: 'CLIENTI',
    items: [
      { label: 'Clienti', icon: Users, href: '/clients' },
    ],
  },
  {
    title: 'CONTABILITA',
    items: [
      { label: 'Prima Nota', icon: BookOpen, href: '/clients' },
      { label: 'IVA', icon: Receipt, href: '/clients' },
    ],
  },
  {
    title: 'BILANCIO',
    items: [
      { label: 'Bilancio', icon: BarChart3, href: '/clients' },
      { label: 'Cespiti', icon: Package, href: '/clients' },
    ],
  },
  {
    title: 'BANCA',
    items: [
      { label: 'Riconciliazione', icon: CreditCard, href: '/clients' },
    ],
  },
  {
    title: 'DOCUMENTI',
    items: [
      { label: 'Conservazione', icon: Archive, href: '/clients' },
    ],
  },
  {
    title: 'STUDIO',
    items: [
      { label: 'Task', icon: CheckSquare2, href: '/studio' },
      { label: 'Dashboard Studio', icon: Building2, href: '/studio' },
    ],
  },
  {
    title: 'IMPOSTAZIONI',
    items: [
      { label: 'Impostazioni', icon: Settings, href: '/settings' },
    ],
  },
]

function SidebarSection({ section }: { section: NavSection }) {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="mb-1">
      <button
        onClick={() => setCollapsed((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-1 mb-0.5 group"
      >
        <span className="text-[10px] font-semibold tracking-wider text-slate-400 dark:text-slate-500 uppercase group-hover:text-slate-600 dark:group-hover:text-slate-400 transition-colors">
          {section.title}
        </span>
        {collapsed ? (
          <ChevronDown className="w-3 h-3 text-slate-300 dark:text-slate-600" />
        ) : (
          <ChevronUp className="w-3 h-3 text-slate-300 dark:text-slate-600" />
        )}
      </button>

      {!collapsed && (
        <ul>
          {section.items.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
            return (
              <li key={`${section.title}-${item.label}`}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center gap-2.5 px-3 py-2 rounded-lg mx-1 mb-0.5 text-sm transition-colors',
                    isActive
                      ? 'bg-accent text-accent-foreground font-medium'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'
                  )}
                >
                  <item.icon
                    className={cn(
                      'w-4 h-4 flex-shrink-0',
                      isActive ? 'text-primary' : 'text-slate-400 dark:text-slate-500'
                    )}
                  />
                  {item.label}
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

export function Sidebar() {
  const { user, logout } = useAuth()

  const initials = user
    ? `${user.nome?.[0] ?? ''}${user.cognome?.[0] ?? ''}`.toUpperCase() || user.email[0].toUpperCase()
    : '?'

  const displayName = user
    ? `${user.nome ?? ''} ${user.cognome ?? ''}`.trim() || user.email
    : ''

  return (
    <aside className="fixed inset-y-0 left-0 w-[260px] flex flex-col bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 z-40">
      {/* Logo */}
      <div className="h-14 flex items-center gap-3 px-4 border-b border-slate-200 dark:border-slate-800 flex-shrink-0">
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #7c3aed 100%)' }}
        >
          OP
        </div>
        <span className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
          OpenPassCom
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-1">
        {NAV_SECTIONS.map((section) => (
          <SidebarSection key={section.title} section={section} />
        ))}
      </nav>

      {/* User footer */}
      <div className="px-3 py-3 border-t border-slate-200 dark:border-slate-800 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #7c3aed 100%)' }}
          >
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-slate-900 dark:text-slate-100 truncate">
              {displayName}
            </p>
            <p className="text-[11px] text-slate-400 dark:text-slate-500 truncate">
              {user?.email}
            </p>
          </div>
          <button
            onClick={logout}
            className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center text-slate-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
            aria-label="Disconnetti"
            title="Disconnetti"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}
