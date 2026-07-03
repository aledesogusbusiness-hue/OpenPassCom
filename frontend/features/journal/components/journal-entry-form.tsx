'use client'

import { useFieldArray, useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2, Plus, Trash2 } from 'lucide-react'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

const CAUSALE_OPTIONS = [
  { value: 'FV', label: 'FV — Fattura Vendita' },
  { value: 'FA', label: 'FA — Fattura Acquisto' },
  { value: 'IN', label: 'IN — Incasso' },
  { value: 'PG', label: 'PG — Pagamento' },
  { value: 'PN', label: 'PN — Prima Nota' },
] as const

const lineSchema = z.object({
  account_id: z.string().min(1, 'Conto obbligatorio'),
  dare: z
    .string()
    .regex(/^\d+(\.\d{0,2})?$/, 'Importo non valido')
    .default('0.00'),
  avere: z
    .string()
    .regex(/^\d+(\.\d{0,2})?$/, 'Importo non valido')
    .default('0.00'),
  descrizione: z.string().optional(),
})

const journalEntrySchema = z
  .object({
    data_registrazione: z.string().min(1, 'Data obbligatoria'),
    descrizione: z.string().min(1, 'Descrizione obbligatoria'),
    causale: z.string().min(1, 'Causale obbligatoria'),
    lines: z
      .array(lineSchema)
      .min(1, 'Inserire almeno una riga'),
  })
  .superRefine((val, ctx) => {
    const totalDare = val.lines.reduce(
      (sum, l) => sum + parseFloat(l.dare || '0'),
      0,
    )
    const totalAvere = val.lines.reduce(
      (sum, l) => sum + parseFloat(l.avere || '0'),
      0,
    )
    if (Math.abs(totalDare - totalAvere) >= 0.01) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Il totale Dare deve essere uguale al totale Avere',
        path: ['lines'],
      })
    }
  })

export type JournalEntryFormValues = z.infer<typeof journalEntrySchema>

interface JournalEntryFormProps {
  onSubmit: (data: JournalEntryFormValues) => Promise<void>
  isLoading?: boolean
}

function toFixed2(val: string): number {
  return Math.round(parseFloat(val || '0') * 100) / 100
}

export function JournalEntryForm({ onSubmit, isLoading }: JournalEntryFormProps) {
  const today = new Date().toISOString().split('T')[0]

  const form = useForm<JournalEntryFormValues>({
    resolver: zodResolver(journalEntrySchema),
    defaultValues: {
      data_registrazione: today,
      descrizione: '',
      causale: '',
      lines: [{ account_id: '', dare: '0.00', avere: '0.00', descrizione: '' }],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'lines',
  })

  const watchedLines = useWatch({ control: form.control, name: 'lines' })

  const totalDare = (watchedLines ?? []).reduce(
    (sum, l) => sum + toFixed2(l.dare),
    0,
  )
  const totalAvere = (watchedLines ?? []).reduce(
    (sum, l) => sum + toFixed2(l.avere),
    0,
  )
  const isBalanced = Math.abs(totalDare - totalAvere) < 0.01

  const fmtCurrency = (n: number) =>
    n.toLocaleString('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-5">
        {/* Header fields */}
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="data_registrazione"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Data *</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="causale"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Causale *</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleziona..." />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {CAUSALE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
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
          name="descrizione"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Descrizione *</FormLabel>
              <FormControl>
                <Input placeholder="Es. Fattura n. 123 del fornitore ABC" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Lines */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Righe contabili</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                append({ account_id: '', dare: '0.00', avere: '0.00', descrizione: '' })
              }
            >
              <Plus className="mr-1.5 h-3.5 w-3.5" />
              Aggiungi Riga
            </Button>
          </div>

          <div className="rounded-md border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-muted/50 border-b">
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground w-[30%]">
                      Conto
                    </th>
                    <th className="px-3 py-2 text-right font-medium text-muted-foreground w-[18%]">
                      Dare
                    </th>
                    <th className="px-3 py-2 text-right font-medium text-muted-foreground w-[18%]">
                      Avere
                    </th>
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">
                      Descrizione
                    </th>
                    <th className="px-3 py-2 w-10" />
                  </tr>
                </thead>
                <tbody>
                  {fields.map((field, index) => (
                    <tr key={field.id} className="border-b last:border-0 hover:bg-muted/25">
                      <td className="px-2 py-1.5">
                        <FormField
                          control={form.control}
                          name={`lines.${index}.account_id`}
                          render={({ field }) => (
                            <FormItem className="space-y-0">
                              <FormControl>
                                <Input
                                  placeholder="Codice conto"
                                  className="h-8 font-mono text-xs"
                                  {...field}
                                />
                              </FormControl>
                              <FormMessage className="text-xs" />
                            </FormItem>
                          )}
                        />
                      </td>
                      <td className="px-2 py-1.5">
                        <FormField
                          control={form.control}
                          name={`lines.${index}.dare`}
                          render={({ field }) => (
                            <FormItem className="space-y-0">
                              <FormControl>
                                <Input
                                  placeholder="0.00"
                                  className="h-8 text-right tabular-nums font-mono text-xs"
                                  {...field}
                                />
                              </FormControl>
                              <FormMessage className="text-xs" />
                            </FormItem>
                          )}
                        />
                      </td>
                      <td className="px-2 py-1.5">
                        <FormField
                          control={form.control}
                          name={`lines.${index}.avere`}
                          render={({ field }) => (
                            <FormItem className="space-y-0">
                              <FormControl>
                                <Input
                                  placeholder="0.00"
                                  className="h-8 text-right tabular-nums font-mono text-xs"
                                  {...field}
                                />
                              </FormControl>
                              <FormMessage className="text-xs" />
                            </FormItem>
                          )}
                        />
                      </td>
                      <td className="px-2 py-1.5">
                        <FormField
                          control={form.control}
                          name={`lines.${index}.descrizione`}
                          render={({ field }) => (
                            <FormItem className="space-y-0">
                              <FormControl>
                                <Input
                                  placeholder="Opzionale"
                                  className="h-8 text-xs"
                                  {...field}
                                />
                              </FormControl>
                            </FormItem>
                          )}
                        />
                      </td>
                      <td className="px-2 py-1.5 text-center">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-muted-foreground hover:text-destructive"
                          onClick={() => remove(index)}
                          disabled={fields.length === 1}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          <span className="sr-only">Rimuovi riga</span>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t bg-muted/30">
                    <td className="px-3 py-2 text-sm font-medium text-muted-foreground">
                      Totali
                    </td>
                    <td
                      className={cn(
                        'px-3 py-2 text-right text-sm font-semibold tabular-nums font-mono',
                        !isBalanced && 'text-destructive',
                      )}
                    >
                      {fmtCurrency(totalDare)}
                    </td>
                    <td
                      className={cn(
                        'px-3 py-2 text-right text-sm font-semibold tabular-nums font-mono',
                        !isBalanced && 'text-destructive',
                      )}
                    >
                      {fmtCurrency(totalAvere)}
                    </td>
                    <td colSpan={2}>
                      {!isBalanced && (
                        <span className="text-xs text-destructive px-2">
                          Sbilancio: {fmtCurrency(Math.abs(totalDare - totalAvere))}
                        </span>
                      )}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          {form.formState.errors.lines?.root?.message && (
            <p className="text-sm text-destructive">
              {form.formState.errors.lines.root.message}
            </p>
          )}
          {(form.formState.errors.lines as { message?: string })?.message && (
            <p className="text-sm text-destructive">
              {(form.formState.errors.lines as { message?: string }).message}
            </p>
          )}
        </div>

        <div className="flex justify-end pt-1">
          <Button type="submit" disabled={isLoading || !isBalanced}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Salva Registrazione
          </Button>
        </div>
      </form>
    </Form>
  )
}
