'use client'

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Users, Calendar, CheckSquare2, AlertCircle } from 'lucide-react'
import { useDashboard, useTasks } from '@/hooks/use-studio'
import { StatCard } from '@/components/shared/stat-card'
import { PageHeader } from '@/components/shared/page-header'
import { ErrorState } from '@/components/shared/error-state'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import type { StudioTask } from '@/types'

const MONTHLY_DATA = [
  { mese: 'Gen', registrazioni: 45 },
  { mese: 'Feb', registrazioni: 52 },
  { mese: 'Mar', registrazioni: 61 },
  { mese: 'Apr', registrazioni: 58 },
  { mese: 'Mag', registrazioni: 73 },
  { mese: 'Giu', registrazioni: 68 },
  { mese: 'Lug', registrazioni: 49 },
  { mese: 'Ago', registrazioni: 31 },
  { mese: 'Set', registrazioni: 65 },
  { mese: 'Ott', registrazioni: 78 },
  { mese: 'Nov', registrazioni: 82 },
  { mese: 'Dic', registrazioni: 70 },
]

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <Skeleton className="h-4 w-24 mb-3" />
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-2">
          <CardHeader>
            <Skeleton className="h-5 w-40" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-56 w-full" />
          </CardContent>
        </Card>
        <Card className="col-span-1">
          <CardHeader>
            <Skeleton className="h-5 w-32" />
          </CardHeader>
          <CardContent className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function prioritaBadgeVariant(priorita: string) {
  if (priorita === 'alta') return 'destructive' as const
  if (priorita === 'media') return 'warning' as const
  return 'secondary' as const
}

function statoBadgeVariant(stato: string) {
  if (stato === 'completato') return 'success' as const
  if (stato === 'in_corso') return 'default' as const
  return 'outline' as const
}

function RecentTasksTable({ tasks }: { tasks: StudioTask[] }) {
  const recent = tasks.slice(0, 5)

  if (recent.length === 0) {
    return <p className="text-sm text-muted-foreground py-4">Nessun task recente.</p>
  }

  return (
    <div className="rounded-md border overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Titolo</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Tipo</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Priorità</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Stato</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Scadenza</th>
          </tr>
        </thead>
        <tbody>
          {recent.map((task) => (
            <tr key={task.id} className="border-b last:border-0 hover:bg-muted/40 transition-colors">
              <td className="px-4 py-3 font-medium">{task.titolo}</td>
              <td className="px-4 py-3">
                <Badge variant="secondary">{task.tipo}</Badge>
              </td>
              <td className="px-4 py-3">
                <Badge variant={prioritaBadgeVariant(task.priorita)}>{task.priorita}</Badge>
              </td>
              <td className="px-4 py-3">
                <Badge variant={statoBadgeVariant(task.stato)}>{task.stato}</Badge>
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {task.data_scadenza ?? '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function DashboardPage() {
  const { data: dashboard, isLoading, isError, refetch } = useDashboard()
  const { data: tasks, isLoading: tasksLoading } = useTasks()

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <PageHeader title="Dashboard" description="Panoramica dello studio" />
        <DashboardSkeleton />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-6">
        <PageHeader title="Dashboard" description="Panoramica dello studio" />
        <ErrorState onRetry={() => refetch()} />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader title="Dashboard" description="Panoramica dello studio" />

      {/* Row 1: 4 stat cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          title="Clienti Attivi"
          value={dashboard?.clienti_attivi ?? 0}
          icon={<Users />}
        />
        <StatCard
          title="Esercizi Aperti"
          value={dashboard?.esercizi_aperti ?? 0}
          icon={<Calendar />}
        />
        <StatCard
          title="Task Aperti"
          value={dashboard?.task_aperti ?? 0}
          icon={<CheckSquare2 />}
        />
        <StatCard
          title="Task Urgenti"
          value={dashboard?.task_urgenti ?? 0}
          icon={<AlertCircle />}
        />
      </div>

      {/* Row 2: chart (2/3) + scadenze card (1/3) */}
      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Registrazioni per mese</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={MONTHLY_DATA} margin={{ top: 4, right: 12, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorReg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="mese" tick={{ fontSize: 12 }} className="text-muted-foreground" />
                <YAxis tick={{ fontSize: 12 }} className="text-muted-foreground" />
                <Tooltip
                  contentStyle={{ fontSize: 13, borderRadius: 8 }}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Area
                  type="monotone"
                  dataKey="registrazioni"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fill="url(#colorReg)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle className="text-base font-semibold">Scadenze Imminenti</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between rounded-lg border p-3">
              <span className="text-sm text-muted-foreground">Task urgenti</span>
              <Badge variant="destructive">{dashboard?.task_urgenti ?? 0}</Badge>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <span className="text-sm text-muted-foreground">Scadenze aperte</span>
              <Badge variant="warning">{dashboard?.scadenze_aperte ?? 0}</Badge>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <span className="text-sm text-muted-foreground">Bozze da postare</span>
              <Badge variant="secondary">{dashboard?.registrazioni_bozza ?? 0}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Row 3: recent tasks table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">Task Recenti</CardTitle>
        </CardHeader>
        <CardContent>
          {tasksLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : (
            <RecentTasksTable tasks={tasks ?? []} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
