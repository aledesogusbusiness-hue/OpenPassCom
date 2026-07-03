'use client'

import * as React from 'react'
import { Moon, Sun, Monitor } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'

type ThemeMode = 'light' | 'dark' | 'system'

const themeOrder: ThemeMode[] = ['light', 'dark', 'system']

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" aria-label="Cambia tema">
        <Sun className="h-4 w-4" />
      </Button>
    )
  }

  const currentTheme = (theme as ThemeMode) ?? 'system'
  const currentIndex = themeOrder.indexOf(currentTheme)
  const nextTheme = themeOrder[(currentIndex + 1) % themeOrder.length]

  const handleCycle = () => {
    setTheme(nextTheme)
  }

  const icons: Record<ThemeMode, React.ReactNode> = {
    light: <Sun className="h-4 w-4" />,
    dark: <Moon className="h-4 w-4" />,
    system: <Monitor className="h-4 w-4" />,
  }

  const labels: Record<ThemeMode, string> = {
    light: 'Tema chiaro',
    dark: 'Tema scuro',
    system: 'Tema di sistema',
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={handleCycle}
      aria-label={labels[currentTheme]}
      title={labels[currentTheme]}
    >
      {icons[currentTheme]}
    </Button>
  )
}
