'use client'

import { useMemo, useState } from 'react'
import { useParams } from 'next/navigation'
import { Send, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { formatDateTime } from '@/lib/utils'
import { studioService } from '@/services/studio'
import { useFiscalYears } from '@/hooks/use-clients'
import type { ConservatoreLog } from '@/types'
import type { CreateConservatoreInput } from '@/services/studio'

const TIPI_DOCUMENTO = [
  'Dichiarazione IVA',
  'Dichiarazione dei Redditi',
  'Libro Giornale',
  'Registro IVA Acquisti',
  'Registro IVA Vendite',
  'Libro Inventari',
  'Bilancio',
  'Fatture Emesse',
  'Fatture Ricevute',
  'Altro',
] as const

const STATO_MAP: Record<string, { label: string; variant: 'warning' | 'default' | 'success' | 'destructive' }> = {
  da_inviare: { label: 'Da inviare', variant: 'warning' },
  inviato: { label: 'Inviato', variant: 'default' },
  confermato: { label: 'Confermato', variant: 'success' },
  errore: { label: 'Errore', variant: 'destructive' },
}

function useConservatore(clientId: string) {
  return useQuery({
    queryKey: ['conservatore', clientId],
    queryFn: () => studioService.listConservatore(clientId),
    enabled: !!clientId,
  })
}

function useCreateConservatore(clientId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateConservatoreInput) =>
      studioService.createConservatore(clientId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conservatore', clientId] })
    },
  })
}

function InviaDocumentoDialog({
  open,
  onOpenChange,
  clientId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  clientId: string
}) {
  const { data: fiscalYears = [] } = useFiscalYears(clientId)
  const createConservatore = useCreateConservatore(clientId)

  const [tipoDocumento, setTipoDocumento] = useState('')
  const [periodo, setPeriodo] = useState('')
  const [note, setNote] = useState('')
  const [fiscalYearId, setFiscalYearId] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!tipoDocumento) return
    await createConservatore.mutateAsync({
      tipo_documento: tipoDocumento,
      ...(periodo ? { periodo } : {}),
      ...(note ? { note } : {}),
      ...(fiscalYearId ? { fiscal_year_id: fiscalYearId } : {}),
    })
    onOpenChange(false)
    setTipoDocumento('')
    setPeriodo('')
    setNote('')
    setFiscalYearId('')
    toast.success('Documento inviato per la conservazione')
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Invia Documento in Conservazione</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="tipo_documento">Tipo Documento *</Label>
            <Select value={tipoDocumento} onValueChange={setTipoDocumento} required>
              <SelectTrigger id="tipo_documento">
                <SelectValue placeholder="Seleziona tipo..." />
              </SelectTrigger>
              <SelectContent>
                {TIPI_DOCUMENTO.map((t) => (
                  <SelectItem key={t} value={t}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="fiscal_year">Esercizio (opzionale)</Label>
            <Select value={fiscalYearId} onValueChange={setFiscalYearId}>
              <SelectTrigger id="fiscal_year">
                <SelectValue placeholder="Tutti gli esercizi" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Tutti gli esercizi</SelectItem>
                {fiscalYears.map((fy) => (
                  <SelectItem key={fy.id} value={fy.id}>
                    {fy.anno}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="periodo">Periodo (opzionale)</Label>
            <Input
              id="periodo"
              placeholder="es. 2024-Q1, Gennaio 2024..."
              value={periodo}
              onChange={(e) => setPeriodo(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="note">Note (opzionale)</Label>
            <Textarea
              id="note"
              placeholder="Note aggiuntive sul documento..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
            />
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={!tipoDocumento || createConservatore.isPending}>
              {createConservatore.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Invia
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function ConservatorePage() {
  const { id } = useParams<{ id: string }>()
  const [dialogOpen, setDialogOpen] = useState(false)

  const { data: logs = [], isLoading } = useConservatore(id)

  const columns = useMemo<ColumnDef<ConservatoreLog>[]>(
    () => [
      {
        accessorKey: 'tipo_documento',
        header: 'Tipo Documento',
        cell: ({ row }) => (
          <span className="font-medium">{row.original.tipo_documento}</span>
        ),
      },
      {
        accessorKey: 'periodo',
        header: 'Periodo',
        cell: ({ row }) => (
          <span className="text-muted-foreground">{row.original.periodo || '—'}</span>
        ),
      },
      {
        accessorKey: 'stato',
        header: 'Stato',
        cell: ({ row }) => {
          const info = STATO_MAP[row.original.stato] ?? { label: row.original.stato, variant: 'outline' as const }
          return <Badge variant={info.variant}>{info.label}</Badge>
        },
      },
      {
        accessorKey: 'data_invio',
        header: 'Data Invio',
        cell: ({ row }) => (
          <span className="tabular-nums text-sm">
            {row.original.data_invio ? formatDateTime(row.original.data_invio) : '—'}
          </span>
        ),
      },
      {
        accessorKey: 'riferimento_esterno',
        header: 'Rif. Esterno',
        cell: ({ row }) => (
          <span className="font-mono text-xs text-muted-foreground">
            {row.original.riferimento_esterno || '—'}
          </span>
        ),
      },
    ],
    [],
  )

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Conservazione Digitale"
        description="Gestione e invio dei documenti fiscali in conservazione sostitutiva"
        actions={
          <Button onClick={() => setDialogOpen(true)}>
            <Send className="h-4 w-4" />
            Invia Documento
          </Button>
        }
      />

      <DataTable
        columns={columns}
        data={logs}
        isLoading={isLoading}
        searchPlaceholder="Cerca per tipo documento o riferimento..."
      />

      <InviaDocumentoDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        clientId={id}
      />
    </div>
  )
}
