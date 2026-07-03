'use client'

import * as React from 'react'
import { AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface ErrorStateProps {
  title?: string
  description?: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({
  title = 'Si è verificato un errore',
  description = 'Impossibile caricare i dati. Riprova più tardi.',
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-4 py-16 text-center',
        className
      )}
    >
      <AlertCircle className="h-12 w-12 text-destructive" />
      <div className="space-y-1.5">
        <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground max-w-sm">{description}</p>
        )}
      </div>
      {onRetry && (
        <Button variant="outline" onClick={onRetry} className="mt-2">
          Riprova
        </Button>
      )}
    </div>
  )
}
