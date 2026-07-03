'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { Plus, ChevronRight } from 'lucide-react'
import { toast } from 'sonner'
import type { ColumnDef } from '@tanstack/react-table'
import { PageHeader } from '@/components/shared/page-header'
import DataTable from '@/components/shared/data-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ClientForm } from '@/features/clients/components/client-form'
import { useClients, useCreateClient } from '@/hooks/use-clients'
import type { ClientEntity } from '@/types'
import type { CreateClientInput } from '@/services/clients'

const REGIME_LABELS: Record<ClientEntity['fiscal_regime'], string> = {
  ordinario: 'Ordinario',
  semplificato: 'Semplificato',
  forfettario: 'Forfettario',
}

export default function ClientsPage() {
  const [dialogOpen, setDialogOpen] = useState(false)

  const { data: clients = [], isLoading } = useClients()
  const createClient = useCreateClient()

  const columns = useMemo<ColumnDef<ClientEntity>[]>(
    () => [
      {
        accessorKey: 'ragione_sociale',
        header: 'Ragione Sociale',
        cell: ({ row }) => (
          <Link
            href={`/clients/${row.original.id}`}
            className="font-medium hover:underline underline-offset-2"
          >
            {row.original.ragione_sociale}
          </Link>
        ),
      },
      {
        accessorKey: 'codice_fiscale',
        header: 'Codice Fiscale',
        cell: ({ row }) => (
          <span className="font-mono text-xs tabular-nums">
            {row.original.codice_fiscale}
          </span>
        ),
      },
      {
        accessorKey: 'partita_iva',
        header: 'P.IVA',
        cell: ({ row }) => (
          <span className="font-mono text-xs tabular-nums">
            {row.original.partita_iva}
          </span>
        ),
      },
      {
        accessorKey: 'fiscal_regime',
        header: 'Regime Fiscale',
        cell: ({ row }) => (
          <Badge variant="outline">
            {REGIME_LABELS[row.original.fiscal_regime]}
          </Badge>
        ),
      },
      {
        accessorKey: 'is_active',
        header: 'Stato',
        cell: ({ row }) =>
          row.original.is_active ? (
            <Badge variant="success">Attivo</Badge>
          ) : (
            <Badge variant="secondary">Inattivo</Badge>
          ),
      },
      {
        id: 'azioni',
        header: '',
        cell: ({ row }) => (
          <Link
            href={`/clients/${row.original.id}`}
            aria-label={`Apri ${row.original.ragione_sociale}`}
          >
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          </Link>
        ),
      },
    ],
    [],
  )

  async function handleCreate(data: CreateClientInput) {
    await createClient.mutateAsync(data)
    setDialogOpen(false)
    toast.success('Cliente creato con successo')
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Clienti"
        actions={
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Nuovo Cliente
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={clients}
        isLoading={isLoading}
        searchPlaceholder="Cerca per ragione sociale, CF, P.IVA..."
      />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Nuovo Cliente</DialogTitle>
          </DialogHeader>
          <ClientForm
            onSubmit={handleCreate}
            isLoading={createClient.isPending}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}
