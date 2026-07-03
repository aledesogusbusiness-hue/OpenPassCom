'use client'

import { useMemo, useState } from 'react'
import { useParams } from 'next/navigation'
import { Plus, Calculator, Lock, Loader2, CheckCircle2, FileDown } from 'lucide-react'
import { toast } from 'sonner'
import type { ColumnDef } from '@tanstack/react-table'
import { PageHeader } from '@/components/shared/page-header'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Skeleton } from '@/components/ui/skeleton'
import { useFiscalYears } from '@/hooks/use-clients'
import {
  useStatoPatrimoniale,
  useContoEconomico,
  useFixedAssets,
  useCreateFixedAsset,
  useComputePlan,
  useCloseYear,
  useExportBilancio,
} from '@/hooks/use-balance'
import { FixedAssetForm } from '@/features/balance/components/fixed-asset-form'
import type { FixedAssetFormValues } from '@/features/balance/components/fixed-asset-form'
import { formatCurrency, cn } from '@/lib/utils'
import type { FixedAsset, YearClosing, VoceBilancio } from '@/types'

function AccountTable({
  rows,
  total,
  totalLabel,
}: {
  rows: VoceBilancio[]
  total: string
  totalLabel: string
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-muted-foreground">
            <th className="py-2 text-left font-medium">Conto</th>
            <th className="py-2 text-right font-medium tabular-nums">Importo</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.codice} className="border-b last:border-0 hover:bg-muted/40">
              <td className="py-2 pr-4">{r.codice} — {r.nome}</td>
              <td className="py-2 text-right tabular-nums font-variant-numeric">
                {formatCurrency(r.saldo)}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t-2">
            <td className="py-2.5 font-semibold">{totalLabel}</td>
            <td className="py-2.5 text-right font-semibold tabular-nums">
              {formatCurrency(total)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  )
}

export default function BalancePage() {
  const { id } = useParams<{ id: string }>()

  const [selectedFyId, setSelectedFyId] = useState<string>('')
  const [assetDialogOpen, setAssetDialogOpen] = useState(false)
  const [closeDialogOpen, setCloseDialogOpen] = useState(false)
  const [yearClosing, setYearClosing] = useState<YearClosing | null>(null)

  const { data: fiscalYears = [], isLoading: fyLoading } = useFiscalYears(id)

  const activeFyId = selectedFyId || fiscalYears.find((y) => y.stato === 'aperto')?.id || fiscalYears[0]?.id || ''
  const activeFy = fiscalYears.find((y) => y.id === activeFyId)

  const spQuery = useStatoPatrimoniale(id, activeFyId)
  const ceQuery = useContoEconomico(id, activeFyId)
  const assetsQuery = useFixedAssets(id)

  const createAsset = useCreateFixedAsset(id)
  const computePlan = useComputePlan(id)
  const closeYear = useCloseYear(id, activeFyId)
  const exportBilancio = useExportBilancio(id, activeFyId)

  const utile = parseFloat(ceQuery.data?.utile_perdita ?? '0')
  const isProfit = utile >= 0

  async function handleCreateAsset(data: FixedAssetFormValues) {
    await createAsset.mutateAsync(data)
    setAssetDialogOpen(false)
    toast.success('Cespite aggiunto con successo')
  }

  async function handleDepreciate(assetId: string) {
    await computePlan.mutateAsync(assetId)
    toast.success('Ammortamento calcolato')
  }

  async function handleCloseYear() {
    const result = await closeYear.mutateAsync()
    setYearClosing(result)
    setCloseDialogOpen(false)
    toast.success('Esercizio chiuso con successo')
  }

  const assetColumns = useMemo<ColumnDef<FixedAsset>[]>(
    () => [
      {
        accessorKey: 'codice',
        header: 'Codice',
        cell: ({ row }) => (
          <span className="font-mono text-xs tabular-nums">{row.original.codice}</span>
        ),
      },
      {
        accessorKey: 'descrizione',
        header: 'Descrizione',
        cell: ({ row }) => <span className="font-medium">{row.original.descrizione}</span>,
      },
      {
        accessorKey: 'categoria',
        header: 'Categoria',
        cell: ({ row }) => (
          <Badge variant="outline" className="text-xs">{row.original.categoria}</Badge>
        ),
      },
      {
        accessorKey: 'costo_storico',
        header: 'Costo Storico',
        cell: ({ row }) => (
          <span className="tabular-nums">{formatCurrency(row.original.costo_storico)}</span>
        ),
      },
      {
        accessorKey: 'aliquota_ammortamento',
        header: 'Aliquota %',
        cell: ({ row }) => (
          <span className="tabular-nums">{row.original.aliquota_ammortamento}%</span>
        ),
      },
      {
        accessorKey: 'metodo',
        header: 'Metodo',
        cell: ({ row }) => (
          <span className="text-muted-foreground text-xs">
            {row.original.metodo === 'quote_costanti' ? 'Quote Costanti' : 'Decrescente'}
          </span>
        ),
      },
      {
        id: 'azioni',
        header: '',
        cell: ({ row }) => (
          <Button
            variant="outline"
            size="sm"
            disabled={computePlan.isPending}
            onClick={() => handleDepreciate(row.original.id)}
          >
            {computePlan.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Calculator className="h-3.5 w-3.5" />
            )}
            Calcola Ammortamento
          </Button>
        ),
      },
    ],
    [computePlan.isPending],
  )

  if (fyLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Bilancio"
        description="Stato patrimoniale, conto economico e cespiti"
        actions={
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" disabled={!activeFyId || exportBilancio.isPending}>
                {exportBilancio.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <FileDown className="mr-2 h-4 w-4" />
                )}
                Esporta
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => exportBilancio.mutate('pdf')}>
                Esporta PDF
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportBilancio.mutate('xlsx')}>
                Esporta Excel
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        }
      />

      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-muted-foreground">Esercizio</span>
        <Select value={activeFyId} onValueChange={setSelectedFyId}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Seleziona esercizio..." />
          </SelectTrigger>
          <SelectContent>
            {fiscalYears.map((fy) => (
              <SelectItem key={fy.id} value={fy.id}>
                {fy.anno}
                {fy.stato === 'aperto' ? ' (aperto)' : ' (chiuso)'}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="patrimoniale">
        <TabsList>
          <TabsTrigger value="patrimoniale">Stato Patrimoniale</TabsTrigger>
          <TabsTrigger value="economico">Conto Economico</TabsTrigger>
          <TabsTrigger value="cespiti">Cespiti</TabsTrigger>
          <TabsTrigger value="chiusura">Chiusura Esercizio</TabsTrigger>
        </TabsList>

        {/* Stato Patrimoniale */}
        <TabsContent value="patrimoniale" className="mt-4">
          {spQuery.isLoading ? (
            <div className="grid grid-cols-2 gap-6">
              <Skeleton className="h-48" />
              <Skeleton className="h-48" />
            </div>
          ) : spQuery.data ? (
            <div className="grid grid-cols-2 gap-6">
              <div className="rounded-lg border bg-card p-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
                  Attivo
                </h3>
                <AccountTable
                  rows={spQuery.data.attivo.voci}
                  total={spQuery.data.totale_attivo}
                  totalLabel="Totale Attivo"
                />
              </div>
              <div className="rounded-lg border bg-card p-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
                  Passivo
                </h3>
                <AccountTable
                  rows={spQuery.data.passivo.voci}
                  total={spQuery.data.totale_passivo}
                  totalLabel="Totale Passivo"
                />
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">
              Seleziona un esercizio per visualizzare lo stato patrimoniale.
            </p>
          )}
        </TabsContent>

        {/* Conto Economico */}
        <TabsContent value="economico" className="mt-4 space-y-6">
          {ceQuery.isLoading ? (
            <div className="grid grid-cols-2 gap-6">
              <Skeleton className="h-48" />
              <Skeleton className="h-48" />
            </div>
          ) : ceQuery.data ? (
            <>
              <div className="grid grid-cols-2 gap-6">
                <div className="rounded-lg border bg-card p-4">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
                    Ricavi
                  </h3>
                  <AccountTable
                    rows={ceQuery.data.ricavi.voci}
                    total={ceQuery.data.ricavi.totale}
                    totalLabel="Totale Ricavi"
                  />
                </div>
                <div className="rounded-lg border bg-card p-4">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-3">
                    Costi
                  </h3>
                  <AccountTable
                    rows={ceQuery.data.costi.voci}
                    total={ceQuery.data.costi.totale}
                    totalLabel="Totale Costi"
                  />
                </div>
              </div>

              <div className="rounded-lg border bg-card p-6 flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">
                  {isProfit ? 'Utile di Esercizio' : 'Perdita di Esercizio'}
                </span>
                <span
                  className={cn(
                    'text-3xl font-bold tabular-nums',
                    isProfit ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400',
                  )}
                >
                  {formatCurrency(ceQuery.data.utile_perdita)}
                </span>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">
              Seleziona un esercizio per visualizzare il conto economico.
            </p>
          )}
        </TabsContent>

        {/* Cespiti */}
        <TabsContent value="cespiti" className="mt-4 space-y-4">
          <div className="flex justify-end">
            <Button onClick={() => setAssetDialogOpen(true)} disabled={!activeFyId}>
              <Plus className="h-4 w-4" />
              Nuovo Cespite
            </Button>
          </div>
          <DataTable
            columns={assetColumns}
            data={assetsQuery.data ?? []}
            isLoading={assetsQuery.isLoading}
            searchPlaceholder="Cerca per codice o descrizione..."
          />
        </TabsContent>

        {/* Chiusura Esercizio */}
        <TabsContent value="chiusura" className="mt-4">
          {!activeFyId ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              Seleziona un esercizio per procedere con la chiusura.
            </p>
          ) : activeFy?.stato !== 'aperto' || yearClosing ? (
            <div className="rounded-lg border bg-card p-6 space-y-4">
              <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                <CheckCircle2 className="h-5 w-5" />
                <span className="font-semibold">Esercizio chiuso</span>
              </div>
              {yearClosing && (
                <dl className="grid grid-cols-2 gap-3 text-sm mt-4">
                  <div>
                    <dt className="text-muted-foreground">Totale Attivo</dt>
                    <dd className="font-medium tabular-nums">{formatCurrency(yearClosing.totale_attivo)}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Totale Passivo</dt>
                    <dd className="font-medium tabular-nums">{formatCurrency(yearClosing.totale_passivo)}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Totale Ricavi</dt>
                    <dd className="font-medium tabular-nums">{formatCurrency(yearClosing.totale_ricavi)}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Totale Costi</dt>
                    <dd className="font-medium tabular-nums">{formatCurrency(yearClosing.totale_costi)}</dd>
                  </div>
                  <div className="col-span-2 pt-2 border-t">
                    <dt className="text-muted-foreground">Utile / Perdita</dt>
                    <dd
                      className={cn(
                        'text-xl font-bold tabular-nums mt-1',
                        parseFloat(yearClosing.utile_perdita ?? '0') >= 0
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400',
                      )}
                    >
                      {formatCurrency(yearClosing.utile_perdita)}
                    </dd>
                  </div>
                </dl>
              )}
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-6 space-y-4">
              <p className="text-sm text-muted-foreground">
                La chiusura dell&apos;esercizio {activeFy?.anno} genera le scritture di assestamento
                e blocca ulteriori registrazioni. L&apos;operazione non è reversibile.
              </p>
              <Button
                variant="destructive"
                onClick={() => setCloseDialogOpen(true)}
                disabled={closeYear.isPending}
              >
                <Lock className="h-4 w-4" />
                Chiudi Esercizio {activeFy?.anno}
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* New asset dialog */}
      <Dialog open={assetDialogOpen} onOpenChange={setAssetDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Nuovo Cespite</DialogTitle>
          </DialogHeader>
          <FixedAssetForm
            onSubmit={handleCreateAsset}
            isLoading={createAsset.isPending}
          />
        </DialogContent>
      </Dialog>

      {/* Close year confirmation dialog */}
      <Dialog open={closeDialogOpen} onOpenChange={setCloseDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Conferma Chiusura Esercizio</DialogTitle>
            <DialogDescription>
              Stai per chiudere l&apos;esercizio {activeFy?.anno}. Questa operazione è
              definitiva e non può essere annullata. Tutti i saldi verranno consolidati.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCloseDialogOpen(false)}>
              Annulla
            </Button>
            <Button
              variant="destructive"
              onClick={handleCloseYear}
              disabled={closeYear.isPending}
            >
              {closeYear.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Conferma Chiusura
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
