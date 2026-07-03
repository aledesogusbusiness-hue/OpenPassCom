'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import {
  BookOpen,
  CheckCircle,
  Loader2,
  Plus,
  RotateCcw,
} from 'lucide-react'
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { JournalEntryForm } from '@/features/journal/components/journal-entry-form'
import type { JournalEntryFormValues } from '@/features/journal/components/journal-entry-form'
import { useClient, useFiscalYears } from '@/hooks/use-clients'
import {
  useBilancioVerifica,
  useCreateJournalEntry,
  useJournalEntries,
  usePostJournalEntry,
  useReverseJournalEntry,
} from '@/hooks/use-journal'
import type { JournalEntry } from '@/types'

const CAUSALE_LABELS: Record<string, string> = {
  FV: 'Fattura Vendita',
  FA: 'Fattura Acquisto',
  IN: 'Incasso',
  PG: 'Pagamento',
  PN: 'Prima Nota',
}

const STATO_VARIANT: Record<
  string,
  'default' | 'secondary' | 'warning' | 'success' | 'destructive' | 'outline'
> = {
  draft: 'warning',
  posted: 'success',
  reversed: 'secondary',
}

const STATO_LABEL: Record<string, string> = {
  draft: 'Bozza',
  posted: 'Contabilizzata',
  reversed: 'Stornata',
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('it-IT')
}

function fmtCurrency(val: string) {
  return parseFloat(val).toLocaleString('it-IT', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export default function JournalPage() {
  const { id } = useParams<{ id: string }>()
  const searchParams = useSearchParams()
  const router = useRouter()

  const fyParam = searchParams.get('fy') ?? ''
  const [selectedFyId, setSelectedFyId] = useState(fyParam)

  const [sheetOpen, setSheetOpen] = useState(false)
  const [confirmAction, setConfirmAction] = useState<{
    type: 'post' | 'reverse'
    entry: JournalEntry
  } | null>(null)

  const { data: client, isLoading: clientLoading } = useClient(id)
  const { data: fiscalYears = [], isLoading: fyLoading } = useFiscalYears(id)

  const fiscalYearId = selectedFyId || ''

  const { data: entries = [], isLoading: entriesLoading } = useJournalEntries(
    id,
    fiscalYearId,
  )
  const { data: bilancio, isLoading: bilancioLoading } = useBilancioVerifica(
    id,
    fiscalYearId,
  )

  const createEntry = useCreateJournalEntry(id, fiscalYearId)
  const postEntry = usePostJournalEntry(id, fiscalYearId)
  const reverseEntry = useReverseJournalEntry(id, fiscalYearId)

  function handleFyChange(value: string) {
    setSelectedFyId(value)
    router.replace(`/clients/${id}/journal?fy=${value}`)
  }

  async function handleCreate(data: JournalEntryFormValues) {
    await createEntry.mutateAsync(data)
    setSheetOpen(false)
    toast.success('Registrazione salvata')
  }

  async function handleConfirmAction() {
    if (!confirmAction) return
    try {
      if (confirmAction.type === 'post') {
        await postEntry.mutateAsync(confirmAction.entry.id)
        toast.success('Registrazione contabilizzata')
      } else {
        await reverseEntry.mutateAsync(confirmAction.entry.id)
        toast.success('Registrazione stornata')
      }
    } catch {
      toast.error('Operazione non riuscita')
    } finally {
      setConfirmAction(null)
    }
  }

  const columns = useMemo<ColumnDef<JournalEntry>[]>(
    () => [
      {
        accessorKey: 'numero_registrazione',
        header: 'N.',
        cell: ({ row }) => (
          <span className="tabular-nums font-mono text-xs text-muted-foreground">
            {row.original.numero_registrazione}
          </span>
        ),
      },
      {
        accessorKey: 'data_registrazione',
        header: 'Data',
        cell: ({ row }) => (
          <span className="tabular-nums text-sm">
            {fmtDate(row.original.data_registrazione)}
          </span>
        ),
      },
      {
        accessorKey: 'descrizione',
        header: 'Descrizione',
        cell: ({ row }) => (
          <span className="text-sm max-w-xs block truncate">
            {row.original.descrizione}
          </span>
        ),
      },
      {
        accessorKey: 'causale',
        header: 'Causale',
        cell: ({ row }) => (
          <Badge variant="outline" className="text-xs font-mono">
            {row.original.causale}
            {CAUSALE_LABELS[row.original.causale]
              ? ` — ${CAUSALE_LABELS[row.original.causale]}`
              : ''}
          </Badge>
        ),
      },
      {
        accessorKey: 'stato',
        header: 'Stato',
        cell: ({ row }) => (
          <Badge variant={STATO_VARIANT[row.original.stato] ?? 'secondary'}>
            {STATO_LABEL[row.original.stato] ?? row.original.stato}
          </Badge>
        ),
      },
      {
        id: 'azioni',
        header: '',
        cell: ({ row }) => {
          const entry = row.original
          return (
            <div className="flex items-center gap-2 justify-end">
              {entry.stato === 'draft' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setConfirmAction({ type: 'post', entry })}
                >
                  <CheckCircle className="mr-1.5 h-3.5 w-3.5" />
                  Contabilizza
                </Button>
              )}
              {entry.stato === 'posted' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setConfirmAction({ type: 'reverse', entry })}
                >
                  <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
                  Storna
                </Button>
              )}
              <Button size="sm" variant="ghost" asChild>
                <Link
                  href={`/clients/${id}/journal/${entry.id}?fy=${fiscalYearId}`}
                >
                  Dettaglio
                </Link>
              </Button>
            </div>
          )
        },
      },
    ],
    [id, fiscalYearId],
  )

  if (clientLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!client) {
    return (
      <div className="p-6">
        <ErrorState
          title="Cliente non trovato"
          description="Il cliente richiesto non esiste o non sei autorizzato."
        />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Prima Nota"
        description={client.ragione_sociale}
        actions={
          <Button
            onClick={() => setSheetOpen(true)}
            disabled={!fiscalYearId}
          >
            <Plus className="mr-2 h-4 w-4" />
            Nuova Registrazione
          </Button>
        }
      />

      {/* Fiscal Year Selector */}
      <div className="flex items-center gap-3">
        <BookOpen className="h-4 w-4 text-muted-foreground shrink-0" />
        <span className="text-sm font-medium text-muted-foreground">
          Esercizio
        </span>
        {fyLoading ? (
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        ) : (
          <Select value={selectedFyId} onValueChange={handleFyChange}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Seleziona esercizio..." />
            </SelectTrigger>
            <SelectContent>
              {fiscalYears.map((fy) => (
                <SelectItem key={fy.id} value={fy.id}>
                  {fy.anno} — {fy.stato}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {!fiscalYearId && (
        <p className="text-sm text-muted-foreground py-8 text-center">
          Seleziona un esercizio fiscale per visualizzare le registrazioni.
        </p>
      )}

      {fiscalYearId && (
        <Tabs defaultValue="registrazioni">
          <TabsList>
            <TabsTrigger value="registrazioni">Registrazioni</TabsTrigger>
            <TabsTrigger value="bilancio">Bilancio di Verifica</TabsTrigger>
          </TabsList>

          {/* Registrazioni */}
          <TabsContent value="registrazioni" className="mt-4">
            <DataTable
              columns={columns}
              data={entries}
              isLoading={entriesLoading}
              searchPlaceholder="Cerca per descrizione, causale..."
            />
          </TabsContent>

          {/* Bilancio di Verifica */}
          <TabsContent value="bilancio" className="mt-4">
            {bilancioLoading ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : !bilancio ? (
              <p className="text-sm text-muted-foreground py-8 text-center">
                Nessun dato disponibile.
              </p>
            ) : (
              <div className="rounded-md border overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="h-10 px-4 text-left font-medium text-muted-foreground">
                        Codice
                      </th>
                      <th className="h-10 px-4 text-left font-medium text-muted-foreground">
                        Conto
                      </th>
                      <th className="h-10 px-4 text-right font-medium text-muted-foreground tabular-nums">
                        Dare
                      </th>
                      <th className="h-10 px-4 text-right font-medium text-muted-foreground tabular-nums">
                        Avere
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {bilancio.righe.map((riga, i) => (
                      <tr
                        key={i}
                        className="border-b last:border-0 hover:bg-muted/25 transition-colors"
                      >
                        <td className="px-4 py-3 font-mono text-xs text-muted-foreground tabular-nums">
                          {riga.codice}
                        </td>
                        <td className="px-4 py-3">{riga.nome}</td>
                        <td className="px-4 py-3 text-right tabular-nums font-mono text-xs">
                          {fmtCurrency(riga.dare_totale)}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums font-mono text-xs">
                          {fmtCurrency(riga.avere_totale)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t bg-muted/30 font-semibold">
                      <td colSpan={2} className="px-4 py-3 text-sm">
                        Totale
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums font-mono text-sm">
                        {fmtCurrency(bilancio.totale_dare)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums font-mono text-sm">
                        {fmtCurrency(bilancio.totale_avere)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}

      {/* New Entry Sheet */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent
          side="right"
          className="w-full sm:max-w-2xl overflow-y-auto"
        >
          <SheetHeader className="mb-6">
            <SheetTitle>Nuova Registrazione</SheetTitle>
          </SheetHeader>
          <JournalEntryForm
            onSubmit={handleCreate}
            isLoading={createEntry.isPending}
          />
        </SheetContent>
      </Sheet>

      {/* Confirm Dialog */}
      <Dialog
        open={!!confirmAction}
        onOpenChange={(open) => !open && setConfirmAction(null)}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {confirmAction?.type === 'post'
                ? 'Contabilizza Registrazione'
                : 'Storna Registrazione'}
            </DialogTitle>
            <DialogDescription>
              {confirmAction?.type === 'post'
                ? 'La registrazione verrà contabilizzata e non sarà più modificabile. Procedere?'
                : 'Verrà creata una registrazione di storno. Procedere?'}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmAction(null)}>
              Annulla
            </Button>
            <Button
              variant={confirmAction?.type === 'reverse' ? 'destructive' : 'default'}
              onClick={handleConfirmAction}
              disabled={postEntry.isPending || reverseEntry.isPending}
            >
              {(postEntry.isPending || reverseEntry.isPending) && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {confirmAction?.type === 'post' ? 'Contabilizza' : 'Storna'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
