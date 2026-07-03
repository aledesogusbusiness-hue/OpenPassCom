'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import { ChevronDown, ChevronRight, Upload, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { PageHeader } from '@/components/shared/page-header'
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
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { formatCurrency, formatDate } from '@/lib/utils'
import {
  useBankStatements,
  useCreateBankStatement,
  useBankTransactions,
  useReconcileTransaction,
} from '@/hooks/use-bank'
import type { BankStatement, BankTransaction } from '@/types'
import type { ReconcileInput } from '@/services/bank'

const STATO_RICONCILIAZIONE_MAP = {
  da_riconciliare: { label: 'Da riconciliare', variant: 'warning' as const },
  riconciliata: { label: 'Riconciliata', variant: 'success' as const },
  irrilevante: { label: 'Irrilevante', variant: 'secondary' as const },
}

function TransactionRow({
  tx,
  clientId,
  statementId,
}: {
  tx: BankTransaction
  clientId: string
  statementId: string
}) {
  const [reconcileOpen, setReconcileOpen] = useState(false)
  const [reconcileStato, setReconcileStato] = useState<'riconciliata' | 'irrilevante'>('riconciliata')
  const [journalEntryId, setJournalEntryId] = useState('')

  const reconcile = useReconcileTransaction(clientId, statementId)

  async function handleReconcile() {
    const data: ReconcileInput = {
      stato: reconcileStato,
      ...(journalEntryId ? { journal_entry_id: journalEntryId } : {}),
    }
    await reconcile.mutateAsync({ transactionId: tx.id, data })
    setReconcileOpen(false)
    toast.success('Transazione riconciliata')
  }

  const statoInfo = STATO_RICONCILIAZIONE_MAP[tx.stato_riconciliazione]
  const isPositive = tx.tipo === 'entrata'

  return (
    <tr className="border-b last:border-0 hover:bg-muted/40">
      <td className="p-3 tabular-nums text-sm">{formatDate(tx.data_valuta)}</td>
      <td className="p-3 text-sm max-w-xs truncate">{tx.descrizione}</td>
      <td
        className={cn(
          'p-3 text-sm tabular-nums text-right font-medium',
          isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400',
        )}
      >
        {isPositive ? '+' : '-'}{formatCurrency(tx.importo)}
      </td>
      <td className="p-3">
        <Badge variant={statoInfo.variant}>{statoInfo.label}</Badge>
      </td>
      <td className="p-3">
        {tx.stato_riconciliazione === 'da_riconciliare' && (
          <>
            <Button variant="outline" size="sm" onClick={() => setReconcileOpen(true)}>
              Riconcilia
            </Button>
            <Dialog open={reconcileOpen} onOpenChange={setReconcileOpen}>
              <DialogContent className="sm:max-w-sm">
                <DialogHeader>
                  <DialogTitle>Riconcilia Transazione</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <Label>Stato</Label>
                    <Select
                      value={reconcileStato}
                      onValueChange={(v) => setReconcileStato(v as 'riconciliata' | 'irrilevante')}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="riconciliata">Riconciliata</SelectItem>
                        <SelectItem value="irrilevante">Irrilevante</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {reconcileStato === 'riconciliata' && (
                    <div className="space-y-1.5">
                      <Label>Registrazione contabile (opzionale)</Label>
                      <Input
                        placeholder="ID registrazione..."
                        value={journalEntryId}
                        onChange={(e) => setJournalEntryId(e.target.value)}
                      />
                    </div>
                  )}
                  <div className="flex justify-end gap-2 pt-1">
                    <Button variant="outline" onClick={() => setReconcileOpen(false)}>
                      Annulla
                    </Button>
                    <Button onClick={handleReconcile} disabled={reconcile.isPending}>
                      {reconcile.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                      Conferma
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </>
        )}
      </td>
    </tr>
  )
}

function StatementCard({ statement, clientId }: { statement: BankStatement; clientId: string }) {
  const [expanded, setExpanded] = useState(false)
  const { data: transactions = [], isLoading } = useBankTransactions(
    clientId,
    expanded ? statement.id : '',
  )

  return (
    <div className="rounded-lg border bg-card">
      <button
        className="w-full flex items-center justify-between p-4 text-left hover:bg-muted/40 transition-colors rounded-lg"
        onClick={() => setExpanded((p) => !p)}
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-4">
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
          )}
          <div>
            <p className="font-medium font-mono text-sm">{statement.iban}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              {formatDate(statement.data_inizio)} — {formatDate(statement.data_fine)}
            </p>
          </div>
        </div>
        <div className="text-right text-sm">
          <p className="text-muted-foreground text-xs">Saldo iniziale → finale</p>
          <p className="tabular-nums font-medium">
            {formatCurrency(statement.saldo_iniziale)}{' '}
            <span className="text-muted-foreground">→</span>{' '}
            {formatCurrency(statement.saldo_finale)}
          </p>
        </div>
      </button>

      {expanded && (
        <div className="border-t">
          {isLoading ? (
            <div className="p-4 space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : transactions.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground text-center">
              Nessuna transazione disponibile.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/30 text-muted-foreground">
                    <th className="p-3 text-left font-medium">Data Valuta</th>
                    <th className="p-3 text-left font-medium">Descrizione</th>
                    <th className="p-3 text-right font-medium">Importo</th>
                    <th className="p-3 text-left font-medium">Stato</th>
                    <th className="p-3" />
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((tx) => (
                    <TransactionRow
                      key={tx.id}
                      tx={tx}
                      clientId={clientId}
                      statementId={statement.id}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ImportStatementDialog({
  open,
  onOpenChange,
  clientId,
}: {
  open: boolean
  onOpenChange: (v: boolean) => void
  clientId: string
}) {
  const createStatement = useCreateBankStatement(clientId)
  const [form, setForm] = useState({
    iban: '',
    data_inizio: '',
    data_fine: '',
    saldo_iniziale: '',
    saldo_finale: '',
  })

  function handleChange(field: keyof typeof form, value: string) {
    setForm((p) => ({ ...p, [field]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    await createStatement.mutateAsync(form)
    onOpenChange(false)
    setForm({ iban: '', data_inizio: '', data_fine: '', saldo_iniziale: '', saldo_finale: '' })
    toast.success('Estratto conto importato')
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Importa Estratto Conto</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="iban">IBAN *</Label>
            <Input
              id="iban"
              placeholder="IT60 X054 2811 1010 0000 0123 456"
              value={form.iban}
              onChange={(e) => handleChange('iban', e.target.value)}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="data_inizio">Data Inizio *</Label>
              <Input
                id="data_inizio"
                type="date"
                value={form.data_inizio}
                onChange={(e) => handleChange('data_inizio', e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="data_fine">Data Fine *</Label>
              <Input
                id="data_fine"
                type="date"
                value={form.data_fine}
                onChange={(e) => handleChange('data_fine', e.target.value)}
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="saldo_iniziale">Saldo Iniziale (€) *</Label>
              <Input
                id="saldo_iniziale"
                type="number"
                step="0.01"
                placeholder="0.00"
                value={form.saldo_iniziale}
                onChange={(e) => handleChange('saldo_iniziale', e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="saldo_finale">Saldo Finale (€) *</Label>
              <Input
                id="saldo_finale"
                type="number"
                step="0.01"
                placeholder="0.00"
                value={form.saldo_finale}
                onChange={(e) => handleChange('saldo_finale', e.target.value)}
                required
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={createStatement.isPending}>
              {createStatement.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Importa
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function BankPage() {
  const { id } = useParams<{ id: string }>()
  const [importOpen, setImportOpen] = useState(false)

  const { data: statements = [], isLoading } = useBankStatements(id)

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Riconciliazione Bancaria"
        description="Estratti conto e riconciliazione delle transazioni"
        actions={
          <Button onClick={() => setImportOpen(true)}>
            <Upload className="h-4 w-4" />
            Importa Estratto
          </Button>
        }
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : statements.length === 0 ? (
        <div className="rounded-lg border bg-card p-10 text-center">
          <p className="text-sm font-medium text-muted-foreground">
            Nessun estratto conto disponibile.
          </p>
          <Button className="mt-4" onClick={() => setImportOpen(true)}>
            <Upload className="h-4 w-4" />
            Importa il primo estratto
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {statements.map((s) => (
            <StatementCard key={s.id} statement={s} clientId={id} />
          ))}
        </div>
      )}

      <ImportStatementDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        clientId={id}
      />
    </div>
  )
}
