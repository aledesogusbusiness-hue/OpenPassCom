'use client'

import * as React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { Pencil, CheckCheck, Plus } from 'lucide-react'
import type { ColumnDef } from '@tanstack/react-table'
import { useTasks, useCreateTask, useUpdateTask, useCompleteTask } from '@/hooks/use-studio'
import { TASK_TIPO_OPTIONS, TASK_PRIORITA_OPTIONS } from '@/lib/constants'
import { PageHeader } from '@/components/shared/page-header'
import DataTable from '@/components/shared/data-table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import type { StudioTask } from '@/types'

const taskSchema = z.object({
  titolo: z.string().min(1, 'Il titolo è obbligatorio'),
  tipo: z.string().min(1, 'Seleziona un tipo'),
  priorita: z.string().optional(),
  data_scadenza: z.string().optional(),
  descrizione: z.string().optional(),
})

type TaskFormValues = z.infer<typeof taskSchema>

function prioritaBadgeVariant(p: string) {
  if (p === 'urgente') return 'destructive' as const
  if (p === 'alta') return 'warning' as const
  return 'secondary' as const
}

function statoBadgeVariant(s: string) {
  if (s === 'completato') return 'success' as const
  if (s === 'in_corso') return 'default' as const
  return 'outline' as const
}

interface TaskDialogProps {
  task?: StudioTask | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function TaskDialog({ task, open, onOpenChange }: TaskDialogProps) {
  const isEdit = !!task
  const createTask = useCreateTask()
  const updateTask = useUpdateTask()

  const form = useForm<TaskFormValues>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      titolo: '',
      tipo: '',
      priorita: '',
      data_scadenza: '',
      descrizione: '',
    },
  })

  React.useEffect(() => {
    if (open) {
      form.reset({
        titolo: task?.titolo ?? '',
        tipo: task?.tipo ?? '',
        priorita: task?.priorita ?? '',
        data_scadenza: task?.data_scadenza ?? '',
        descrizione: task?.descrizione ?? '',
      })
    }
  }, [open, task, form])

  function onSubmit(values: TaskFormValues) {
    if (isEdit && task) {
      updateTask.mutate(
        {
          id: task.id,
          data: {
            titolo: values.titolo,
            priorita: values.priorita || undefined,
            data_scadenza: values.data_scadenza || undefined,
            descrizione: values.descrizione || undefined,
          },
        },
        {
          onSuccess: () => {
            toast.success('Task aggiornato con successo')
            onOpenChange(false)
          },
          onError: () => toast.error('Errore durante l\'aggiornamento del task'),
        }
      )
    } else {
      createTask.mutate(
        {
          titolo: values.titolo,
          tipo: values.tipo,
          priorita: values.priorita || undefined,
          data_scadenza: values.data_scadenza || undefined,
          descrizione: values.descrizione || undefined,
        },
        {
          onSuccess: () => {
            toast.success('Task creato con successo')
            onOpenChange(false)
          },
          onError: () => toast.error('Errore durante la creazione del task'),
        }
      )
    }
  }

  const isPending = createTask.isPending || updateTask.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Modifica Task' : 'Nuovo Task'}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="titolo"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Titolo *</FormLabel>
                  <FormControl>
                    <Input placeholder="Es. Dichiarazione IVA Q1" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="tipo"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tipo *</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value} disabled={isEdit}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Seleziona tipo" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {TASK_TIPO_OPTIONS.map((t) => (
                          <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="priorita"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Priorità</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value ?? ''}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Seleziona priorità" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {TASK_PRIORITA_OPTIONS.map((p) => (
                          <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="data_scadenza"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Data Scadenza</FormLabel>
                  <FormControl>
                    <Input type="date" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="descrizione"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Descrizione</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Descrizione opzionale..."
                      rows={3}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Annulla
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? 'Salvataggio...' : isEdit ? 'Salva modifiche' : 'Crea task'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default function StudioPage() {
  const [newTaskOpen, setNewTaskOpen] = React.useState(false)
  const [editTask, setEditTask] = React.useState<StudioTask | null>(null)
  const { data: tasks, isLoading } = useTasks()
  const updateTask = useUpdateTask()
  const completeTask = useCompleteTask()

  function markComplete(task: StudioTask) {
    completeTask.mutate(
      { id: task.id, completatoIl: new Date().toISOString().slice(0, 10) },
      {
        onSuccess: () => toast.success(`"${task.titolo}" completato`),
        onError: () => toast.error('Errore durante l\'aggiornamento'),
      }
    )
  }

  const columns: ColumnDef<StudioTask>[] = [
    {
      accessorKey: 'titolo',
      header: 'Titolo',
      cell: ({ row }) => (
        <span className="font-medium">{row.original.titolo}</span>
      ),
    },
    {
      accessorKey: 'tipo',
      header: 'Tipo',
      cell: ({ row }) => (
        <Badge variant="secondary">{row.original.tipo}</Badge>
      ),
    },
    {
      accessorKey: 'priorita',
      header: 'Priorità',
      cell: ({ row }) => (
        <Badge variant={prioritaBadgeVariant(row.original.priorita)}>
          {row.original.priorita}
        </Badge>
      ),
    },
    {
      accessorKey: 'stato',
      header: 'Stato',
      cell: ({ row }) => (
        <Badge variant={statoBadgeVariant(row.original.stato)}>
          {row.original.stato}
        </Badge>
      ),
    },
    {
      accessorKey: 'data_scadenza',
      header: 'Scadenza',
      cell: ({ row }) => (
        <span className="text-muted-foreground">
          {row.original.data_scadenza ?? '—'}
        </span>
      ),
    },
    {
      id: 'azioni',
      header: 'Azioni',
      cell: ({ row }) => {
        const task = row.original
        const isComplete = task.stato === 'completato'
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setEditTask(task)}
              title="Modifica"
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => markComplete(task)}
              disabled={isComplete || completeTask.isPending}
              title="Segna come completato"
            >
              <CheckCheck className="h-4 w-4" />
            </Button>
          </div>
        )
      },
    },
  ]

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Task Studio"
        actions={
          <Button onClick={() => setNewTaskOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Nuovo Task
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={tasks ?? []}
        isLoading={isLoading}
        searchPlaceholder="Cerca task..."
      />

      <TaskDialog
        open={newTaskOpen}
        onOpenChange={setNewTaskOpen}
      />

      <TaskDialog
        task={editTask}
        open={!!editTask}
        onOpenChange={(open) => { if (!open) setEditTask(null) }}
      />
    </div>
  )
}
