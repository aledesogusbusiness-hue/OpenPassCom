import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }

export function formatCurrency(value: string | number | undefined | null): string {
  if (value === undefined || value === null || value === '') return '—'
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '—'
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(num)
}

export function formatDate(dateStr: string | undefined | null): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function formatDateTime(dateStr: string | undefined | null): string {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  return d.toLocaleString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export function getRegimeFiscaleLabel(regime: string): string {
  const map: Record<string, string> = { ordinario: 'Ordinario', semplificato: 'Semplificato', forfettario: 'Forfettario' }
  return map[regime] ?? regime
}

export function getStatoJournalBadge(stato: string): { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' } {
  if (stato === 'posted') return { label: 'Contabilizzata', variant: 'default' }
  if (stato === 'reversed') return { label: 'Stornata', variant: 'destructive' }
  return { label: 'Bozza', variant: 'secondary' }
}

export function getPrioritaClass(priorita: string): string {
  if (priorita === 'urgente') return 'text-red-600 bg-red-50 dark:bg-red-950 dark:text-red-400'
  if (priorita === 'alta') return 'text-orange-600 bg-orange-50 dark:bg-orange-950 dark:text-orange-400'
  if (priorita === 'bassa') return 'text-slate-500 bg-slate-50 dark:bg-slate-900 dark:text-slate-400'
  return 'text-blue-600 bg-blue-50 dark:bg-blue-950 dark:text-blue-400'
}
