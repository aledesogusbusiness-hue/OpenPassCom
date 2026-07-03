'use client'

import * as React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  description?: string
  icon?: React.ReactNode
  className?: string
}

export function StatCard({
  title,
  value,
  description,
  icon,
  className,
}: StatCardProps) {
  return (
    <Card className={cn('', className)}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1 min-w-0">
            <p className="text-sm font-medium text-muted-foreground truncate">
              {title}
            </p>
            <p className="text-2xl font-bold tracking-tight">{value}</p>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
          {icon && (
            <div className="ml-4 shrink-0 text-muted-foreground [&_svg]:h-5 [&_svg]:w-5">
              {icon}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
