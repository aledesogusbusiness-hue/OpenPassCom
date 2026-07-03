'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { Download, FileCode2, Loader2, Plus, Send, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDate } from '@/lib/utils'
import {
  useCreateFatturaPaExport,
  useDownloadFatturaPaXml,
  useFatturePaExport,
  useGenerateFatturaPaXml,
  useMarkFatturaPaEsito,
  useMarkFatturaPaInviata,
} from '@/hooks/use-fattura-pa-export'
import type { CreateFatturaPAExportInput, FatturaPAExport } from '@/services/fattura-pa-export'

const STATO_BADGE: Record<
  FatturaPAExport['stato'],
  { label: string; variant: 'default' | 'secondary' | 'warning' | 'success' | 'destructive' | 'outline' }
> = {
  bozza: { label: 'Bozza', variant: 'secondary' },
  generata: { label: 'XML Generato', variant: 'default' },
  inviata: { label: 'Inviata', variant: 'warning' },
  accettata: { label: 'Accettata', variant: 'success' },
  scartata: { label: 'Scartata', variant: 'destructive' },
  consegnata: { label: 'Consegnata', variant: 'success' },
  errore: { label: 'Errore', variant: 'destructive' },
}

const ALIQUOTE = [0, 4, 5, 10, 22]

interface LineDraft {
  descrizione: string
  quantita: string
  prezzo_unitario: string
  aliquota_iva: number
}

const EMPTY_LINE: LineDraft = { descrizione: '', quantita: '1', prezzo_unitario: '', aliquota_iva: 22 }

function NewExportDialog({
  open,
  onOpenChange,
  clientId,
  fiscalYearId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  clientId: string
  fiscalYearId: string
}) {
  const createExport = useCreateFatturaPaExport(clientId, fiscalYearId)

  const [form, setForm] = useState({
    numero_fattura: '',
    data_fattura: '',
    cedente_indirizzo: '',
    cedente_cap: '',
    cedente_comune: '',
    cedente_provincia: '',
    destinatario_denominazione: '',
    destinatario_partita_iva: '',
    destinatario_codice_fiscale: '',
    destinatario_indirizzo: '',
    destinatario_cap: '',
    destinatario_comune: '',
    destinatario_provincia: '',
    destinatario_codice_sdi: '0000000',
    destinatario_pec: '',
  })
  const [righe, setRighe] = useState<LineDraft[]>([{ ...EMPTY_LINE }])

  function updateField<K extends keyof typeof form>(field: K, value: (typeof form)[K]) {
    setForm((p) => ({ ...p, [field]: value }))
  }

  function updateLine(index: number, field: keyof LineDraft, value: string | number) {
    setRighe((prev) => prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)))
  }

  function reset() {
    setForm({
      numero_fattura: '',
      data_fattura: '',
      cedente_indirizzo: '',
      cedente_cap: '',
      cedente_comune: '',
      cedente_provincia: '',
      destinatario_denominazione: '',
      destinatario_partita_iva: '',
      destinatario_codice_fiscale: '',
      destinatario_indirizzo: '',
      destinatario_cap: '',
      destinatario_comune: '',
      destinatario_provincia: '',
      destinatario_codice_sdi: '0000000',
      destinatario_pec: '',
    })
    setRighe([{ ...EMPTY_LINE }])
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const payload: CreateFatturaPAExportInput = {
      tipo_documento: 'TD01',
      ...form,
      righe: righe.map((r) => ({
        descrizione: r.descrizione,
        quantita: r.quantita,
        prezzo_unitario: r.prezzo_unitario,
        aliquota_iva: r.aliquota_iva,
      })),
    }
    try {
      await createExport.mutateAsync(payload)
      toast.success('Fattura creata in bozza')
      onOpenChange(false)
      reset()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Errore durante la creazione')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Nuova Fattura Elettronica</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Numero Fattura *</Label>
              <Input
                value={form.numero_fattura}
                onChange={(e) => updateField('numero_fattura', e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label>Data Fattura *</Label>
              <Input
                type="date"
                value={form.data_fattura}
                onChange={(e) => updateField('data_fattura', e.target.value)}
                required
              />
            </div>
          </div>

          <div className="rounded-md border p-3 space-y-3">
            <p className="text-sm font-medium">Sede Cedente (studio/cliente emittente)</p>
            <Input
              placeholder="Indirizzo"
              value={form.cedente_indirizzo}
              onChange={(e) => updateField('cedente_indirizzo', e.target.value)}
              required
            />
            <div className="grid grid-cols-3 gap-2">
              <Input
                placeholder="CAP"
                maxLength={5}
                value={form.cedente_cap}
                onChange={(e) => updateField('cedente_cap', e.target.value)}
                required
              />
              <Input
                placeholder="Comune"
                value={form.cedente_comune}
                onChange={(e) => updateField('cedente_comune', e.target.value)}
                required
              />
              <Input
                placeholder="Provincia"
                maxLength={2}
                value={form.cedente_provincia}
                onChange={(e) => updateField('cedente_provincia', e.target.value.toUpperCase())}
                required
              />
            </div>
          </div>

          <div className="rounded-md border p-3 space-y-3">
            <p className="text-sm font-medium">Destinatario</p>
            <Input
              placeholder="Denominazione / Ragione Sociale"
              value={form.destinatario_denominazione}
              onChange={(e) => updateField('destinatario_denominazione', e.target.value)}
              required
            />
            <div className="grid grid-cols-2 gap-2">
              <Input
                placeholder="Partita IVA"
                maxLength={11}
                value={form.destinatario_partita_iva}
                onChange={(e) => updateField('destinatario_partita_iva', e.target.value)}
              />
              <Input
                placeholder="Codice Fiscale"
                maxLength={16}
                value={form.destinatario_codice_fiscale}
                onChange={(e) => updateField('destinatario_codice_fiscale', e.target.value)}
              />
            </div>
            <Input
              placeholder="Indirizzo"
              value={form.destinatario_indirizzo}
              onChange={(e) => updateField('destinatario_indirizzo', e.target.value)}
              required
            />
            <div className="grid grid-cols-3 gap-2">
              <Input
                placeholder="CAP"
                maxLength={5}
                value={form.destinatario_cap}
                onChange={(e) => updateField('destinatario_cap', e.target.value)}
                required
              />
              <Input
                placeholder="Comune"
                value={form.destinatario_comune}
                onChange={(e) => updateField('destinatario_comune', e.target.value)}
                required
              />
              <Input
                placeholder="Provincia"
                maxLength={2}
                value={form.destinatario_provincia}
                onChange={(e) => updateField('destinatario_provincia', e.target.value.toUpperCase())}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Input
                placeholder="Codice Destinatario SDI (7 caratteri)"
                maxLength={7}
                value={form.destinatario_codice_sdi}
                onChange={(e) => updateField('destinatario_codice_sdi', e.target.value)}
              />
              <Input
                placeholder="PEC (se Codice Destinatario = 0000000)"
                value={form.destinatario_pec}
                onChange={(e) => updateField('destinatario_pec', e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">Righe Fattura</p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setRighe((p) => [...p, { ...EMPTY_LINE }])}
              >
                <Plus className="mr-1.5 h-3.5 w-3.5" />
                Aggiungi Riga
              </Button>
            </div>
            {righe.map((riga, i) => (
              <div key={i} className="grid grid-cols-12 gap-2 items-center">
                <Input
                  className="col-span-5"
                  placeholder="Descrizione"
                  value={riga.descrizione}
                  onChange={(e) => updateLine(i, 'descrizione', e.target.value)}
                  required
                />
                <Input
                  className="col-span-2"
                  type="number"
                  step="0.01"
                  placeholder="Qta"
                  value={riga.quantita}
                  onChange={(e) => updateLine(i, 'quantita', e.target.value)}
                  required
                />
                <Input
                  className="col-span-2"
                  type="number"
                  step="0.01"
                  placeholder="Prezzo"
                  value={riga.prezzo_unitario}
                  onChange={(e) => updateLine(i, 'prezzo_unitario', e.target.value)}
                  required
                />
                <Select
                  value={String(riga.aliquota_iva)}
                  onValueChange={(v) => updateLine(i, 'aliquota_iva', Number(v))}
                >
                  <SelectTrigger className="col-span-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ALIQUOTE.map((a) => (
                      <SelectItem key={a} value={String(a)}>
                        {a}%
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="col-span-1 text-muted-foreground hover:text-destructive"
                  onClick={() => setRighe((p) => p.filter((_, idx) => idx !== i))}
                  disabled={righe.length === 1}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={createExport.isPending}>
              {createExport.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Crea Bozza
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function EsitoDialog({
  exportId,
  onOpenChange,
  clientId,
  fiscalYearId,
}: {
  exportId: string | null
  onOpenChange: (v: boolean) => void
  clientId: string
  fiscalYearId: string
}) {
  const markEsito = useMarkFatturaPaEsito(clientId, fiscalYearId)
  const [esito, setEsito] = useState<'accettata' | 'scartata' | 'consegnata'>('accettata')
  const [messaggio, setMessaggio] = useState('')

  async function handleSubmit() {
    if (!exportId) return
    try {
      await markEsito.mutateAsync({ exportId, esito, messaggio: messaggio || undefined })
      toast.success('Esito registrato')
      onOpenChange(false)
      setMessaggio('')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Errore durante la registrazione')
    }
  }

  return (
    <Dialog open={!!exportId} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Registra Esito SDI</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>Esito</Label>
            <Select value={esito} onValueChange={(v) => setEsito(v as typeof esito)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="accettata">Accettata</SelectItem>
                <SelectItem value="scartata">Scartata</SelectItem>
                <SelectItem value="consegnata">Consegnata</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Messaggio (opzionale)</Label>
            <Input value={messaggio} onChange={(e) => setMessaggio(e.target.value)} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annulla
          </Button>
          <Button onClick={handleSubmit} disabled={markEsito.isPending}>
            {markEsito.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Conferma
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function FatturaPaExportPanel({
  clientId,
  fiscalYearId,
}: {
  clientId: string
  fiscalYearId: string
}) {
  const [newOpen, setNewOpen] = useState(false)
  const [esitoTarget, setEsitoTarget] = useState<string | null>(null)

  const { data: exports = [], isLoading } = useFatturePaExport(clientId, fiscalYearId)
  const generateXml = useGenerateFatturaPaXml(clientId, fiscalYearId)
  const downloadXml = useDownloadFatturaPaXml(clientId, fiscalYearId)
  const markInviata = useMarkFatturaPaInviata(clientId, fiscalYearId)

  async function handleGenerate(id: string) {
    try {
      await generateXml.mutateAsync(id)
      toast.success('XML generato')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Errore nella generazione')
    }
  }

  async function handleMarkInviata(id: string) {
    try {
      await markInviata.mutateAsync({ exportId: id })
      toast.success('Fattura marcata come inviata')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Errore durante l\'operazione')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setNewOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Nuova Fattura
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : exports.length === 0 ? (
        <p className="text-sm text-muted-foreground py-8 text-center">
          Nessuna fattura emessa. Crea la prima con &quot;Nuova Fattura&quot;.
        </p>
      ) : (
        <div className="rounded-md border overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50 text-muted-foreground">
                <th className="p-3 text-left font-medium">Numero</th>
                <th className="p-3 text-left font-medium">Data</th>
                <th className="p-3 text-left font-medium">Destinatario</th>
                <th className="p-3 text-left font-medium">Stato</th>
                <th className="p-3 text-left font-medium">Progressivo</th>
                <th className="p-3" />
              </tr>
            </thead>
            <tbody>
              {exports.map((exp) => {
                const badge = STATO_BADGE[exp.stato]
                return (
                  <tr key={exp.id} className="border-b last:border-0 hover:bg-muted/25">
                    <td className="p-3 font-mono text-xs">{exp.numero_fattura}</td>
                    <td className="p-3 tabular-nums">{formatDate(exp.data_fattura)}</td>
                    <td className="p-3">{exp.destinatario_denominazione}</td>
                    <td className="p-3">
                      <Badge variant={badge.variant}>{badge.label}</Badge>
                    </td>
                    <td className="p-3 font-mono text-xs text-muted-foreground">
                      {exp.progressivo_invio ?? '—'}
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-1.5 justify-end">
                        {exp.stato === 'bozza' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleGenerate(exp.id)}
                            disabled={generateXml.isPending}
                          >
                            <FileCode2 className="mr-1.5 h-3.5 w-3.5" />
                            Genera XML
                          </Button>
                        )}
                        {(exp.stato === 'generata' ||
                          exp.stato === 'inviata' ||
                          exp.stato === 'accettata' ||
                          exp.stato === 'scartata' ||
                          exp.stato === 'consegnata') && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => downloadXml.mutate(exp.id)}
                            disabled={downloadXml.isPending}
                          >
                            <Download className="mr-1.5 h-3.5 w-3.5" />
                            Scarica
                          </Button>
                        )}
                        {exp.stato === 'generata' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleMarkInviata(exp.id)}
                            disabled={markInviata.isPending}
                          >
                            <Send className="mr-1.5 h-3.5 w-3.5" />
                            Segna Inviata
                          </Button>
                        )}
                        {exp.stato === 'inviata' && (
                          <Button size="sm" variant="outline" onClick={() => setEsitoTarget(exp.id)}>
                            Registra Esito
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <NewExportDialog
        open={newOpen}
        onOpenChange={setNewOpen}
        clientId={clientId}
        fiscalYearId={fiscalYearId}
      />
      <EsitoDialog
        exportId={esitoTarget}
        onOpenChange={(open) => !open && setEsitoTarget(null)}
        clientId={clientId}
        fiscalYearId={fiscalYearId}
      />
    </div>
  )
}
