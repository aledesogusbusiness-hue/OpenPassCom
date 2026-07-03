'use client'

import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { Loader2, Pencil, Plus, UserX } from 'lucide-react'
import type { ColumnDef } from '@tanstack/react-table'
import { PageHeader } from '@/components/shared/page-header'
import { ErrorState } from '@/components/shared/error-state'
import DataTable from '@/components/shared/data-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useAuth } from '@/providers/auth-provider'
import { useUsers, useCreateUser, useUpdateUser, useDeactivateUser } from '@/hooks/use-users'
import type { User } from '@/types'

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Admin' },
  { value: 'accountant', label: 'Commercialista' },
  { value: 'collaborator', label: 'Collaboratore' },
]

const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin',
  accountant: 'Commercialista',
  collaborator: 'Collaboratore',
}

const createUserSchema = z.object({
  email: z.string().email('Email non valida'),
  password: z.string().min(8, 'Minimo 8 caratteri'),
  full_name: z.string().min(1, 'Nome obbligatorio'),
  role: z.enum(['admin', 'accountant', 'collaborator']),
})

type CreateUserValues = z.infer<typeof createUserSchema>

const editUserSchema = z.object({
  full_name: z.string().min(1, 'Nome obbligatorio'),
  role: z.enum(['admin', 'accountant', 'collaborator']),
})

type EditUserValues = z.infer<typeof editUserSchema>

function CreateUserDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const createUser = useCreateUser()
  const form = useForm<CreateUserValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: { email: '', password: '', full_name: '', role: 'accountant' },
  })

  async function handleSubmit(values: CreateUserValues) {
    try {
      await createUser.mutateAsync(values)
      toast.success('Utente creato con successo')
      onOpenChange(false)
      form.reset()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Errore durante la creazione')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Nuovo Utente</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email *</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="mario@studio.it" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Password *</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="Minimo 8 caratteri" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome Completo *</FormLabel>
                  <FormControl>
                    <Input placeholder="Mario Rossi" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Ruolo *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {ROLE_OPTIONS.map((r) => (
                        <SelectItem key={r.value} value={r.value}>
                          {r.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={createUser.isPending}>
                {createUser.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Crea utente
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

function EditUserDialog({
  user,
  onOpenChange,
}: {
  user: User | null
  onOpenChange: (v: boolean) => void
}) {
  const updateUser = useUpdateUser()
  const form = useForm<EditUserValues>({
    resolver: zodResolver(editUserSchema),
    values: user ? { full_name: user.full_name, role: user.role as EditUserValues['role'] } : undefined,
  })

  async function handleSubmit(values: EditUserValues) {
    if (!user) return
    try {
      await updateUser.mutateAsync({ id: user.id, data: values })
      toast.success('Utente aggiornato')
      onOpenChange(false)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Errore durante l\'aggiornamento')
    }
  }

  return (
    <Dialog open={!!user} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Modifica Utente</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome Completo *</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Ruolo *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {ROLE_OPTIONS.map((r) => (
                        <SelectItem key={r.value} value={r.value}>
                          {r.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={updateUser.isPending}>
                {updateUser.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Salva modifiche
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default function UsersSettingsPage() {
  const { user: currentUser } = useAuth()
  const [createOpen, setCreateOpen] = useState(false)
  const [editUser, setEditUser] = useState<User | null>(null)
  const [deactivateTarget, setDeactivateTarget] = useState<User | null>(null)

  const { data: users = [], isLoading, isError, refetch } = useUsers()
  const deactivateUser = useDeactivateUser()

  async function handleDeactivate() {
    if (!deactivateTarget) return
    try {
      await deactivateUser.mutateAsync(deactivateTarget.id)
      toast.success('Utente disattivato')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Errore durante la disattivazione')
    } finally {
      setDeactivateTarget(null)
    }
  }

  const columns = useMemo<ColumnDef<User>[]>(
    () => [
      {
        accessorKey: 'full_name',
        header: 'Nome',
        cell: ({ row }) => <span className="font-medium">{row.original.full_name}</span>,
      },
      {
        accessorKey: 'email',
        header: 'Email',
        cell: ({ row }) => <span className="text-sm text-muted-foreground">{row.original.email}</span>,
      },
      {
        accessorKey: 'role',
        header: 'Ruolo',
        cell: ({ row }) => <Badge variant="outline">{ROLE_LABELS[row.original.role] ?? row.original.role}</Badge>,
      },
      {
        accessorKey: 'is_active',
        header: 'Stato',
        cell: ({ row }) =>
          row.original.is_active ? (
            <Badge variant="success">Attivo</Badge>
          ) : (
            <Badge variant="secondary">Disattivato</Badge>
          ),
      },
      {
        id: 'azioni',
        header: '',
        cell: ({ row }) => {
          const u = row.original
          const isSelf = u.id === currentUser?.id
          return (
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => setEditUser(u)} title="Modifica">
                <Pencil className="h-4 w-4" />
              </Button>
              {u.is_active && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDeactivateTarget(u)}
                  disabled={isSelf}
                  title={isSelf ? 'Non puoi disattivare te stesso' : 'Disattiva'}
                  className="text-muted-foreground hover:text-destructive"
                >
                  <UserX className="h-4 w-4" />
                </Button>
              )}
            </div>
          )
        },
      },
    ],
    [currentUser?.id],
  )

  if (currentUser && currentUser.role !== 'admin') {
    return (
      <div className="p-6">
        <ErrorState
          title="Accesso negato"
          description="Solo un amministratore può gestire gli utenti dello studio."
        />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-6">
        <ErrorState onRetry={() => refetch()} />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Utenti"
        description="Gestisci gli utenti dello studio e i loro ruoli"
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Nuovo Utente
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={users}
        isLoading={isLoading}
        searchPlaceholder="Cerca per nome o email..."
      />

      <CreateUserDialog open={createOpen} onOpenChange={setCreateOpen} />
      <EditUserDialog user={editUser} onOpenChange={(open) => !open && setEditUser(null)} />

      <Dialog open={!!deactivateTarget} onOpenChange={(open) => !open && setDeactivateTarget(null)}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Disattiva utente</DialogTitle>
            <DialogDescription>
              {deactivateTarget?.full_name} non potrà più accedere alla piattaforma. Potrai
              riattivarlo in seguito modificandone lo stato.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeactivateTarget(null)}>
              Annulla
            </Button>
            <Button variant="destructive" onClick={handleDeactivate} disabled={deactivateUser.isPending}>
              {deactivateUser.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Disattiva
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
