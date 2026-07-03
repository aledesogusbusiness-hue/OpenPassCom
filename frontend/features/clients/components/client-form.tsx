'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2 } from 'lucide-react'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { REGIME_FISCALE_OPTIONS, PERIODICITA_IVA_OPTIONS } from '@/lib/constants'
import type { ClientEntity } from '@/types'
import type { CreateClientInput } from '@/services/clients'

const clientSchema = z
  .object({
    ragione_sociale: z.string().min(1, 'Ragione sociale obbligatoria'),
    codice_fiscale: z.string().max(16).optional().or(z.literal('')),
    partita_iva: z
      .string()
      .regex(/^\d{11}$/, 'La partita IVA deve essere di 11 cifre')
      .optional()
      .or(z.literal('')),
    fiscal_regime: z.enum(['ordinario', 'semplificato', 'forfettario']),
    periodicita_iva: z.enum(['mensile', 'trimestrale']).optional().or(z.literal('')),
    note: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.fiscal_regime === 'forfettario' && data.periodicita_iva) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Il regime forfettario non prevede periodicità IVA',
        path: ['periodicita_iva'],
      })
    }
    if (data.fiscal_regime !== 'forfettario' && !data.periodicita_iva) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'I regimi ordinario e semplificato richiedono la periodicità IVA',
        path: ['periodicita_iva'],
      })
    }
  })

type ClientFormValues = z.infer<typeof clientSchema>

interface ClientFormProps {
  defaultValues?: Partial<ClientEntity>
  onSubmit: (data: CreateClientInput) => Promise<void>
  isLoading?: boolean
}

export function ClientForm({ defaultValues, onSubmit, isLoading }: ClientFormProps) {
  const form = useForm<ClientFormValues>({
    resolver: zodResolver(clientSchema),
    defaultValues: {
      ragione_sociale: defaultValues?.ragione_sociale ?? '',
      codice_fiscale: defaultValues?.codice_fiscale ?? '',
      partita_iva: defaultValues?.partita_iva ?? '',
      fiscal_regime: defaultValues?.fiscal_regime ?? 'ordinario',
      periodicita_iva: defaultValues?.periodicita_iva ?? '',
      note: defaultValues?.note ?? '',
    },
  })

  const fiscalRegime = form.watch('fiscal_regime')

  async function handleSubmit(values: ClientFormValues) {
    const payload: CreateClientInput = {
      ragione_sociale: values.ragione_sociale,
      codice_fiscale: values.codice_fiscale || undefined,
      partita_iva: values.partita_iva || undefined,
      fiscal_regime: values.fiscal_regime,
      periodicita_iva: values.periodicita_iva || undefined,
      note: values.note || undefined,
    }
    await onSubmit(payload)
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="ragione_sociale"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Ragione Sociale *</FormLabel>
              <FormControl>
                <Input placeholder="Es. Rossi Mario SRL" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="codice_fiscale"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Codice Fiscale</FormLabel>
                <FormControl>
                  <Input
                    placeholder="RSSMRA80A01H501X"
                    maxLength={16}
                    {...field}
                    onChange={(e) =>
                      field.onChange(e.target.value.toUpperCase())
                    }
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="partita_iva"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Partita IVA</FormLabel>
                <FormControl>
                  <Input placeholder="12345678901" maxLength={11} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="fiscal_regime"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Regime Fiscale *</FormLabel>
                <Select
                  onValueChange={(value) => {
                    field.onChange(value)
                    if (value === 'forfettario') {
                      form.setValue('periodicita_iva', '')
                    }
                  }}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleziona regime" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {REGIME_FISCALE_OPTIONS.map((opt) => (
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

          <FormField
            control={form.control}
            name="periodicita_iva"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Periodicità IVA{fiscalRegime !== 'forfettario' && ' *'}</FormLabel>
                <Select
                  onValueChange={field.onChange}
                  value={field.value}
                  disabled={fiscalRegime === 'forfettario'}
                >
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleziona periodicità" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {PERIODICITA_IVA_OPTIONS.map((opt) => (
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
          name="note"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Note</FormLabel>
              <FormControl>
                <Textarea placeholder="Note opzionali..." rows={3} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end pt-2">
          <Button type="submit" disabled={isLoading}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {defaultValues?.id ? 'Aggiorna cliente' : 'Crea cliente'}
          </Button>
        </div>
      </form>
    </Form>
  )
}
