'use client'

import { useRef, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import {
  BookOpen,
  Loader2,
  Receipt,
  Upload,
} from 'lucide-react'
import { toast } from 'sonner'
import type { ColumnDef } from '@tanstack/react-table'
import { useMemo } from 'react'
import { PageHeader } from '@/components/shared/page-header'
import { ErrorState } from '@/components/shared/error-state'
import DataTable from '@/components/shared/data-table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useClient, useFiscalYears } from '@/hooks/use-clients'
import {
  useElaborateFatturaPA,
  useFatturePa,
  useMarkSettlementVersata,
  useMarkWithholdingVersata,
  useUploadFatturaPA,
  useVatEntries,
  useVatSettlements,
  useWithholdingTaxes,
} from '@/hooks/use-vat'
import type { FatturaPAImport, VatEntry, VatSettlement, WithholdingTax } from '@/types'

type VatEntryRow = VatEntry & { tipo: 'vendite' | 'acquisti' }

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString('it-IT')
}

function fmtCurrency(val: string) {
  const n = parseFloat(val)
  if (isNaN(n)) return '—'
  return n.toLocaleString('it-IT', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function fmtPct(val: string | number) {
  const n = typeof val === 'string' ? parseFloat(val) : val
  return `${n}%`
}

const STATO_VERSAMENTO_VARIANT: Record<
  string,
  'default' | 'secondary' | 'warning' | 'success' | 'destructive' | 'outline'
> = {
  da_versare: 'warning',
  versata: 'success',
  credito: 'outline',
}

export default function VatPage() {
  const { id } = useParams<{ id: string }>()
  const searchParams = useSearchParams()
  const router = useRouter()

  const fyParam = searchParams.get('fy') ?? ''
  const [selectedFyId, setSelectedFyId] = useState(fyParam)

  const [markVersataTarget, setMarkVersataTarget] = useState<{
    type: 'settlement' | 'withholding'
    id: string
    label: string
  } | null>(null)

  const [elaborateTarget, setElaborateTarget] = useState<string | null>(null)
  const [elaborateForm, setElaborateForm] = useState({
    account_id_fornitore: '',
    account_id_iva: '',
    account_id_debito: '',
  })

  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: client, isLoading: clientLoading } = useClient(id)
  const { data: fiscalYears = [], isLoading: fyLoading } = useFiscalYears(id)

  const fiscalYearId = selectedFyId || ''

  const { data: vatEntries = [], isLoading: vatLoading } = useVatEntries(id, fiscalYearId)
  const { data: settlements = [], isLoading: settlementsLoading } = useVatSettlements(
    id,
    fiscalYearId,
  )
  const { data: withholdings = [], isLoading: withholdingsLoading } =
    useWithholdingTaxes(id, fiscalYearId)
  const { data: fatturePa = [], isLoading: fatturePaLoading } = useFatturePa(
    id,
    fiscalYearId,
  )

  const markSettlement = useMarkSettlementVersata(id, fiscalYearId)
  const markWithholding = useMarkWithholdingVersata(id, fiscalYearId)
  const uploadFatturaPA = useUploadFatturaPA(id, fiscalYearId)
  const elaborateFatturaPA = useElaborateFatturaPA(id, fiscalYearId)

  function handleFyChange(value: string) {
    setSelectedFyId(value)
    router.replace(`/clients/${id}/vat?fy=${value}`)
  }

  async function handleMarkVersata() {
    if (!markVersataTarget) return
    const today = new Date().toISOString().split('T')[0]
    try {
      if (markVersataTarget.type === 'settlement') {
        await markSettlement.mutateAsync({
          settlementId: markVersataTarget.id,
          data: { data_versamento: today },
        })
        toast.success('Liquidazione marcata come versata')
      } else {
        await markWithholding.mutateAsync({
          withholdingId: markVersataTarget.id,
          data: { data_versamento: today },
        })
        toast.success('Ritenuta marcata come versata')
      }
    } catch {
      toast.error('Operazione non riuscita')
    } finally {
      setMarkVersataTarget(null)
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      await uploadFatturaPA.mutateAsync(file)
      toast.success(`${file.name} caricato`)
    } catch {
      toast.error('Errore durante il caricamento')
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  async function handleElaborate() {
    if (!elaborateTarget) return
    try {
      await elaborateFatturaPA.mutateAsync({ importId: elaborateTarget, data: elaborateForm })
      toast.success('Fattura elaborata')
      setElaborateTarget(null)
      setElaborateForm({ account_id_fornitore: '', account_id_iva: '', account_id_debito: '' })
    } catch {
      toast.error('Elaborazione non riuscita')
    }
  }

  const vatColumns = useMemo<ColumnDef<VatEntryRow>[]>(
    () => [
      {
        accessorKey: 'tipo',
        header: 'Tipo',
        cell: ({ row }) => (
          <Badge variant={row.original.tipo === 'vendite' ? 'default' : 'secondary'}>
            {row.original.tipo === 'vendite' ? 'Vendita' : 'Acquisto'}
          </Badge>
        ),
      },
      {
        accessorKey: 'data_documento',
        header: 'Data',
        cell: ({ row }) => (
          <span className="tabular-nums text-sm">
            {fmtDate(row.original.data_documento)}
          </span>
        ),
      },
      {
        accessorKey: 'numero_documento',
        header: 'Documento',
        cell: ({ row }) => (
          <span className="tabular-nums font-mono text-xs">
            {row.original.numero_documento ?? '—'}
          </span>
        ),
      },
      {
        accessorKey: 'controparte',
        header: 'Controparte',
        cell: ({ row }) => (
          <span className="text-sm">{row.original.controparte ?? '—'}</span>
        ),
      },
      {
        accessorKey: 'imponibile',
        header: 'Imponibile',
        cell: ({ row }) => (
          <span className="tabular-nums font-mono text-xs text-right block">
            {fmtCurrency(row.original.imponibile)}
          </span>
        ),
      },
      {
        accessorKey: 'aliquota',
        header: 'Aliquota%',
        cell: ({ row }) => (
          <span className="tabular-nums text-sm text-right block">
            {fmtPct(row.original.aliquota)}
          </span>
        ),
      },
      {
        accessorKey: 'imposta',
        header: 'IVA',
        cell: ({ row }) => (
          <span className="tabular-nums font-mono text-xs text-right block">
            {fmtCurrency(row.original.imposta)}
          </span>
        ),
      },
    ],
    [],
  )

  const withholdingColumns = useMemo<ColumnDef<WithholdingTax>[]>(
    () => [
      {
        accessorKey: 'tipo',
        header: 'Tipo',
        cell: ({ row }) => (
          <Badge variant="outline" className="font-mono text-xs">
            {row.original.tipo}
          </Badge>
        ),
      },
      {
        accessorKey: 'imponibile',
        header: 'Imponibile',
        cell: ({ row }) => (
          <span className="tabular-nums font-mono text-xs text-right block">
            {fmtCurrency(row.original.imponibile)}
          </span>
        ),
      },
      {
        accessorKey: 'aliquota_pct',
        header: 'Aliquota%',
        cell: ({ row }) => (
          <span className="tabular-nums text-sm text-right block">
            {fmtPct(row.original.aliquota_pct)}
          </span>
        ),
      },
      {
        accessorKey: 'importo_ritenuta',
        header: 'Ritenuta',
        cell: ({ row }) => (
          <span className="tabular-nums font-mono text-xs text-right block">
            {fmtCurrency(row.original.importo_ritenuta)}
          </span>
        ),
      },
      {
        id: 'periodo',
        header: 'Mese/Anno',
        cell: ({ row }) => (
          <span className="tabular-nums text-sm">
            {String(row.original.mese_competenza).padStart(2, '0')}/
            {row.original.anno_competenza}
          </span>
        ),
      },
      {
        accessorKey: 'stato',
        header: 'Stato',
        cell: ({ row }) => (
          <Badge
            variant={
              STATO_VERSAMENTO_VARIANT[row.original.stato] ?? 'secondary'
            }
          >
            {row.original.stato}
          </Badge>
        ),
      },
      {
        id: 'azioni',
        header: '',
        cell: ({ row }) => {
          const w = row.original
          return w.stato !== 'versata' ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() =>
                setMarkVersataTarget({
                  type: 'withholding',
                  id: w.id,
                  label: `ritenuta ${fmtCurrency(w.importo_ritenuta)}`,
                })
              }
            >
              Marca Versata
            </Button>
          ) : null
        },
      },
    ],
    [],
  )

  const fatturaColumns = useMemo<ColumnDef<FatturaPAImport>[]>(
    () => [
      {
        accessorKey: 'filename',
        header: 'Filename',
        cell: ({ row }) => (
          <span className="font-mono text-xs">{row.original.filename}</span>
        ),
      },
      {
        accessorKey: 'stato',
        header: 'Stato',
        cell: ({ row }) => (
          <Badge
            variant={
              row.original.stato === 'elaborata'
                ? 'success'
                : row.original.stato === 'errore'
                ? 'destructive'
                : 'warning'
            }
          >
            {row.original.stato}
          </Badge>
        ),
      },
      {
        accessorKey: 'errore_msg',
        header: 'Errore',
        cell: ({ row }) => (
          <span className="text-xs text-destructive">
            {row.original.errore_msg ?? '—'}
          </span>
        ),
      },
      {
        id: 'azioni',
        header: '',
        cell: ({ row }) => {
          const f = row.original
          return f.stato === 'importata' ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setElaborateTarget(f.id)}
              disabled={elaborateFatturaPA.isPending}
            >
              Elabora
            </Button>
          ) : null
        },
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [elaborateFatturaPA.isPending],
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
        title="Gestione IVA"
        description={client.ragione_sociale}
        actions={
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".xml,.p7m"
              className="hidden"
              onChange={handleFileUpload}
            />
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              disabled={!fiscalYearId || uploadFatturaPA.isPending}
            >
              {uploadFatturaPA.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Upload className="mr-2 h-4 w-4" />
              )}
              Carica Fattura PA
            </Button>
          </div>
        }
      />

      {/* Fiscal Year Selector */}
      <div className="flex items-center gap-3">
        <Receipt className="h-4 w-4 text-muted-foreground shrink-0" />
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
          Seleziona un esercizio fiscale per visualizzare i dati IVA.
        </p>
      )}

      {fiscalYearId && (
        <Tabs defaultValue="registro">
          <TabsList>
            <TabsTrigger value="registro">Registro IVA</TabsTrigger>
            <TabsTrigger value="liquidazione">Liquidazione IVA</TabsTrigger>
            <TabsTrigger value="ritenute">Ritenute d&apos;Acconto</TabsTrigger>
            <TabsTrigger value="fatture-pa">Fatture PA</TabsTrigger>
          </TabsList>

          {/* Registro IVA */}
          <TabsContent value="registro" className="mt-4">
            <DataTable
              columns={vatColumns}
              data={vatEntries}
              isLoading={vatLoading}
              searchPlaceholder="Cerca per controparte o documento..."
            />
          </TabsContent>

          {/* Liquidazione IVA */}
          <TabsContent value="liquidazione" className="mt-4">
            {settlementsLoading ? (
              <div className="flex items-center justify-center h-40">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : settlements.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">
                Nessuna liquidazione disponibile.
              </p>
            ) : (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {settlements.map((s) => (
                  <SettlementCard
                    key={s.id}
                    settlement={s}
                    onMarkVersata={() =>
                      setMarkVersataTarget({
                        type: 'settlement',
                        id: s.id,
                        label: `liquidazione ${s.periodo}`,
                      })
                    }
                    isLoading={markSettlement.isPending}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          {/* Ritenute d'Acconto */}
          <TabsContent value="ritenute" className="mt-4">
            <DataTable
              columns={withholdingColumns}
              data={withholdings}
              isLoading={withholdingsLoading}
              searchPlaceholder="Cerca per tipo o anno..."
            />
          </TabsContent>

          {/* Fatture PA */}
          <TabsContent value="fatture-pa" className="mt-4">
            <DataTable
              columns={fatturaColumns}
              data={fatturePa}
              isLoading={fatturePaLoading}
              searchPlaceholder="Cerca per filename o stato..."
            />
          </TabsContent>
        </Tabs>
      )}

      {/* Confirm Mark Versata Dialog */}
      <Dialog
        open={!!markVersataTarget}
        onOpenChange={(open) => !open && setMarkVersataTarget(null)}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Marca come versata</DialogTitle>
            <DialogDescription>
              Verrà registrata la data odierna come data di versamento per la{' '}
              {markVersataTarget?.label}. Procedere?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setMarkVersataTarget(null)}
            >
              Annulla
            </Button>
            <Button
              onClick={handleMarkVersata}
              disabled={
                markSettlement.isPending || markWithholding.isPending
              }
            >
              {(markSettlement.isPending || markWithholding.isPending) && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Conferma
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Elabora Fattura PA Dialog */}
      <Dialog
        open={!!elaborateTarget}
        onOpenChange={(open) => !open && setElaborateTarget(null)}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Elabora Fattura PA</DialogTitle>
            <DialogDescription>
              Indica i conti da usare per la registrazione contabile generata dalla fattura.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>Conto Fornitore</Label>
              <Input
                placeholder="ID conto fornitore..."
                value={elaborateForm.account_id_fornitore}
                onChange={(e) =>
                  setElaborateForm((p) => ({ ...p, account_id_fornitore: e.target.value }))
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label>Conto IVA</Label>
              <Input
                placeholder="ID conto IVA..."
                value={elaborateForm.account_id_iva}
                onChange={(e) =>
                  setElaborateForm((p) => ({ ...p, account_id_iva: e.target.value }))
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label>Conto Debito</Label>
              <Input
                placeholder="ID conto debito..."
                value={elaborateForm.account_id_debito}
                onChange={(e) =>
                  setElaborateForm((p) => ({ ...p, account_id_debito: e.target.value }))
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setElaborateTarget(null)}>
              Annulla
            </Button>
            <Button onClick={handleElaborate} disabled={elaborateFatturaPA.isPending}>
              {elaborateFatturaPA.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Elabora
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

interface SettlementCardProps {
  settlement: VatSettlement
  onMarkVersata: () => void
  isLoading: boolean
}

function SettlementCard({
  settlement: s,
  onMarkVersata,
  isLoading,
}: SettlementCardProps) {
  const debito = parseFloat(s.debito_versare)
  const credito = parseFloat(s.credito_periodo)
  const hasDebito = debito > 0

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base font-semibold tabular-nums">
            {s.periodo}
          </CardTitle>
          <Badge
            variant={
              STATO_VERSAMENTO_VARIANT[s.stato] ?? 'secondary'
            }
          >
            {s.stato}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground uppercase tracking-wide">
          {s.tipo_periodo}
        </p>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <span className="text-muted-foreground">IVA Vendite</span>
          <span className="text-right tabular-nums font-mono text-xs">
            {fmtCurrency(s.iva_vendite)}
          </span>
          <span className="text-muted-foreground">IVA Acquisti</span>
          <span className="text-right tabular-nums font-mono text-xs">
            {fmtCurrency(s.iva_acquisti)}
          </span>
        </div>

        <div className="pt-1 border-t">
          {hasDebito ? (
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Debito</span>
              <span className="tabular-nums font-semibold font-mono text-sm">
                {fmtCurrency(s.debito_versare)}
              </span>
            </div>
          ) : (
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-muted-foreground">
                Credito
              </span>
              <span className="tabular-nums font-mono text-sm">
                {fmtCurrency(s.credito_periodo)}
              </span>
            </div>
          )}
        </div>

        {s.stato !== 'versata' && hasDebito && (
          <Button
            size="sm"
            variant="outline"
            className="w-full mt-1"
            onClick={onMarkVersata}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : null}
            Marca Versata
          </Button>
        )}

        {s.data_versamento && (
          <p className="text-xs text-muted-foreground">
            Versata il {fmtDate(s.data_versamento)}
            {s.f24_riferimento ? ` — F24 ${s.f24_riferimento}` : ''}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
