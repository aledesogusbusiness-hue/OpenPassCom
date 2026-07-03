'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { Pencil, Plus, BookOpen, Receipt, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import type { ColumnDef } from '@tanstack/react-table'
import { PageHeader } from '@/components/shared/page-header'
import { ErrorState } from '@/components/shared/error-state'
import DataTable from '@/components/shared/data-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ClientForm } from '@/features/clients/components/client-form'
import { FiscalYearForm } from '@/features/clients/components/fiscal-year-form'
import {
  useClient,
  useFiscalYears,
  useUpdateClient,
  useCreateFiscalYear,
  useAccountPlans,
  useAccounts,
} from '@/hooks/use-clients'
import type { FiscalYear, Account } from '@/types'
import type { CreateClientInput } from '@/services/clients'

const REGIME_LABELS = {
  ordinario: 'Ordinario',
  semplificato: 'Semplificato',
  forfettario: 'Forfettario',
} as const

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="py-3 grid grid-cols-3 gap-4 border-b last:border-0">
      <dt className="text-sm font-medium text-muted-foreground">{label}</dt>
      <dd className="text-sm col-span-2">{value || '—'}</dd>
    </div>
  )
}

export default function ClientDetailPage() {
  const { id } = useParams<{ id: string }>()

  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [fyDialogOpen, setFyDialogOpen] = useState(false)
  const [selectedPlanId, setSelectedPlanId] = useState<string>('')

  const { data: client, isLoading, isError } = useClient(id)
  const { data: fiscalYears = [], isLoading: fyLoading } = useFiscalYears(id)
  const { data: accountPlans = [] } = useAccountPlans(id)
  const { data: accounts = [], isLoading: accountsLoading } = useAccounts(
    id,
    selectedPlanId,
  )

  const updateClient = useUpdateClient(id)
  const createFiscalYear = useCreateFiscalYear(id)

  const fyColumns = useMemo<ColumnDef<FiscalYear>[]>(
    () => [
      {
        accessorKey: 'anno',
        header: 'Anno',
        cell: ({ row }) => (
          <span className="font-medium tabular-nums">{row.original.anno}</span>
        ),
      },
      {
        accessorKey: 'data_inizio',
        header: 'Data Inizio',
        cell: ({ row }) => (
          <span className="tabular-nums">
            {new Date(row.original.data_inizio).toLocaleDateString('it-IT')}
          </span>
        ),
      },
      {
        accessorKey: 'data_fine',
        header: 'Data Fine',
        cell: ({ row }) => (
          <span className="tabular-nums">
            {new Date(row.original.data_fine).toLocaleDateString('it-IT')}
          </span>
        ),
      },
      {
        accessorKey: 'stato',
        header: 'Stato',
        cell: ({ row }) => (
          <Badge
            variant={row.original.stato === 'aperto' ? 'success' : 'secondary'}
          >
            {row.original.stato}
          </Badge>
        ),
      },
      {
        id: 'azioni',
        header: '',
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" asChild>
              <Link
                href={`/clients/${id}/journal?fy=${row.original.id}`}
              >
                <BookOpen className="mr-1.5 h-3.5 w-3.5" />
                Prima Nota
              </Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link
                href={`/clients/${id}/vat?fy=${row.original.id}`}
              >
                <Receipt className="mr-1.5 h-3.5 w-3.5" />
                IVA
              </Link>
            </Button>
          </div>
        ),
      },
    ],
    [id],
  )

  const accountColumns = useMemo<ColumnDef<Account>[]>(
    () => [
      {
        accessorKey: 'codice',
        header: 'Codice',
        cell: ({ row }) => (
          <span className="font-mono text-xs tabular-nums">
            {row.original.codice}
          </span>
        ),
      },
      {
        accessorKey: 'nome',
        header: 'Nome',
        cell: ({ row }) => (
          <span className="font-medium">{row.original.nome}</span>
        ),
      },
      {
        accessorKey: 'account_type_id',
        header: 'Tipo',
        cell: ({ row }) => (
          <Badge variant="outline" className="text-xs">
            {row.original.account_type_id}
          </Badge>
        ),
      },
      {
        accessorKey: 'livello',
        header: 'Livello',
        cell: ({ row }) => (
          <span className="tabular-nums text-muted-foreground">
            {row.original.livello}
          </span>
        ),
      },
    ],
    [],
  )

  async function handleUpdate(data: CreateClientInput) {
    await updateClient.mutateAsync(data)
    setEditDialogOpen(false)
    toast.success('Cliente aggiornato con successo')
  }

  async function handleCreateFiscalYear(data: {
    anno: number
    data_inizio: string
    data_fine: string
  }) {
    await createFiscalYear.mutateAsync(data)
    setFyDialogOpen(false)
    toast.success('Esercizio fiscale creato con successo')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (isError || !client) {
    return (
      <div className="p-6">
        <ErrorState
          title="Cliente non trovato"
          description="Il cliente richiesto non esiste o non sei autorizzato a visualizzarlo."
        />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title={client.ragione_sociale}
        description={`P.IVA ${client.partita_iva}`}
        actions={
          <Button variant="outline" onClick={() => setEditDialogOpen(true)}>
            <Pencil className="mr-2 h-4 w-4" />
            Modifica
          </Button>
        }
      />

      <Tabs defaultValue="anagrafica">
        <TabsList>
          <TabsTrigger value="anagrafica">Anagrafica</TabsTrigger>
          <TabsTrigger value="esercizi">Esercizi Fiscali</TabsTrigger>
          <TabsTrigger value="piano">Piano dei Conti</TabsTrigger>
        </TabsList>

        {/* Anagrafica */}
        <TabsContent value="anagrafica" className="mt-4">
          <div className="rounded-lg border bg-card p-6">
            <dl>
              <InfoRow label="Ragione Sociale" value={client.ragione_sociale} />
              <InfoRow label="Codice Fiscale" value={client.codice_fiscale} />
              <InfoRow label="Partita IVA" value={client.partita_iva} />
              <InfoRow
                label="Regime Fiscale"
                value={REGIME_LABELS[client.regime_fiscale]}
              />
              <InfoRow label="Email" value={client.email} />
              <InfoRow label="PEC" value={client.pec} />
              <InfoRow label="Telefono" value={client.telefono} />
              <InfoRow label="Indirizzo" value={client.indirizzo} />
              <InfoRow label="CAP" value={client.cap} />
              <InfoRow label="Città" value={client.citta} />
              <InfoRow label="Provincia" value={client.provincia} />
              <div className="py-3 grid grid-cols-3 gap-4">
                <dt className="text-sm font-medium text-muted-foreground">Stato</dt>
                <dd className="col-span-2">
                  {client.is_active ? (
                    <Badge variant="success">Attivo</Badge>
                  ) : (
                    <Badge variant="secondary">Inattivo</Badge>
                  )}
                </dd>
              </div>
            </dl>
          </div>
        </TabsContent>

        {/* Esercizi Fiscali */}
        <TabsContent value="esercizi" className="mt-4 space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setFyDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Nuovo Esercizio
            </Button>
          </div>
          <DataTable
            columns={fyColumns}
            data={fiscalYears}
            isLoading={fyLoading}
            searchPlaceholder="Cerca per anno o stato..."
          />
        </TabsContent>

        {/* Piano dei Conti */}
        <TabsContent value="piano" className="mt-4 space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-muted-foreground">
              Piano dei conti
            </span>
            <Select value={selectedPlanId} onValueChange={setSelectedPlanId}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Seleziona piano..." />
              </SelectTrigger>
              <SelectContent>
                {accountPlans.map((plan) => (
                  <SelectItem key={plan.id} value={plan.id}>
                    {plan.nome}
                    {plan.is_default && ' (default)'}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedPlanId ? (
            <DataTable
              columns={accountColumns}
              data={accounts}
              isLoading={accountsLoading}
              searchPlaceholder="Cerca per codice o nome..."
            />
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">
              Seleziona un piano dei conti per visualizzare i conti.
            </p>
          )}
        </TabsContent>
      </Tabs>

      {/* Edit dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Modifica Cliente</DialogTitle>
          </DialogHeader>
          <ClientForm
            defaultValues={client}
            onSubmit={handleUpdate}
            isLoading={updateClient.isPending}
          />
        </DialogContent>
      </Dialog>

      {/* New fiscal year dialog */}
      <Dialog open={fyDialogOpen} onOpenChange={setFyDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Nuovo Esercizio Fiscale</DialogTitle>
          </DialogHeader>
          <FiscalYearForm
            onSubmit={handleCreateFiscalYear}
            isLoading={createFiscalYear.isPending}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}
