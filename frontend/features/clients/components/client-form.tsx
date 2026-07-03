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
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { REGIME_FISCALE_OPTIONS } from '@/lib/constants'
import type { ClientEntity } from '@/types'
import type { CreateClientInput } from '@/services/clients'

const clientSchema = z.object({
  ragione_sociale: z.string().min(1, 'Ragione sociale obbligatoria'),
  codice_fiscale: z
    .string()
    .length(16, 'Il codice fiscale deve essere di 16 caratteri'),
  partita_iva: z
    .string()
    .regex(/^\d{11}$/, 'La partita IVA deve essere di 11 cifre'),
  regime_fiscale: z.enum(['ordinario', 'semplificato', 'forfettario']),
  email: z.string().email('Email non valida').optional().or(z.literal('')),
  pec: z.string().email('PEC non valida').optional().or(z.literal('')),
  telefono: z.string().optional(),
  indirizzo: z.string().optional(),
  cap: z.string().optional(),
  citta: z.string().optional(),
  provincia: z
    .string()
    .max(2, 'Inserire la sigla di 2 caratteri')
    .optional()
    .or(z.literal('')),
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
      regime_fiscale: defaultValues?.regime_fiscale ?? 'ordinario',
      email: defaultValues?.email ?? '',
      pec: defaultValues?.pec ?? '',
      telefono: defaultValues?.telefono ?? '',
      indirizzo: defaultValues?.indirizzo ?? '',
      cap: defaultValues?.cap ?? '',
      citta: defaultValues?.citta ?? '',
      provincia: defaultValues?.provincia ?? '',
    },
  })

  async function handleSubmit(values: ClientFormValues) {
    const payload: CreateClientInput = {
      ragione_sociale: values.ragione_sociale,
      codice_fiscale: values.codice_fiscale,
      partita_iva: values.partita_iva,
      regime_fiscale: values.regime_fiscale,
      email: values.email || undefined,
      pec: values.pec || undefined,
      telefono: values.telefono || undefined,
      indirizzo: values.indirizzo || undefined,
      cap: values.cap || undefined,
      citta: values.citta || undefined,
      provincia: values.provincia || undefined,
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
                <FormLabel>Codice Fiscale *</FormLabel>
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
                <FormLabel>Partita IVA *</FormLabel>
                <FormControl>
                  <Input placeholder="12345678901" maxLength={11} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="regime_fiscale"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Regime Fiscale *</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
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

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input type="email" placeholder="info@azienda.it" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="pec"
            render={({ field }) => (
              <FormItem>
                <FormLabel>PEC</FormLabel>
                <FormControl>
                  <Input type="email" placeholder="azienda@pec.it" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="telefono"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Telefono</FormLabel>
              <FormControl>
                <Input placeholder="+39 02 1234567" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="indirizzo"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Indirizzo</FormLabel>
              <FormControl>
                <Input placeholder="Via Roma 1" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-3 gap-4">
          <FormField
            control={form.control}
            name="cap"
            render={({ field }) => (
              <FormItem>
                <FormLabel>CAP</FormLabel>
                <FormControl>
                  <Input placeholder="20100" maxLength={5} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="citta"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Città</FormLabel>
                <FormControl>
                  <Input placeholder="Milano" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="provincia"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Provincia</FormLabel>
                <FormControl>
                  <Input
                    placeholder="MI"
                    maxLength={2}
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
        </div>

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
