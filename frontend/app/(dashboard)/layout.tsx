'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { useAuth } from '@/providers/auth-provider'
import { Sidebar } from '@/components/layout/sidebar'
import { Topbar } from '@/components/layout/topbar'
import { CommandPalette } from '@/components/command-palette'
import { FloatingAIButton } from '@/features/ai-assistant/components/floating-button'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()
  const isAuthenticated = user !== null
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login')
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Caricamento...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Fixed sidebar */}
      <Sidebar />

      {/* Main area: topbar + content */}
      <div className="flex flex-col flex-1 min-w-0 ml-[260px]">
        <Topbar />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>

      {/* Global overlays */}
      <CommandPalette />
      <FloatingAIButton />
    </div>
  )
}
