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

const CATEGORIE = ['Attrezzature', 'Software', 'Autoveicoli', 'Mobili e Arredi', 'Immobili', 'Altro'] as const

const fixedAssetSchema = z.object({
  codice: z.string().min(1, 'Codice obbligatorio').max(20, 'Max 20 caratteri'),
  descrizione: z.string().min(1, 'Descrizione obbligatoria'),
  categoria: z.string().min(1, 'Categoria obbligatoria'),
  costo_storico: z.string().min(1, 'Costo storico obbligatorio'),
  data_acquisto: z.string().min(1, 'Data acquisto obbligatoria'),
  aliquota_ammortamento: z.string().min(1, 'Aliquota obbligatoria'),
  metodo: z.enum(['quote_costanti', 'decrescente']).default('quote_costanti'),
})

export type FixedAssetFormValues = z.infer<typeof fixedAssetSchema>

interface FixedAssetFormProps {
  onSubmit: (data: FixedAssetFormValues) => Promise<void>
  isLoading?: boolean
}

export function FixedAssetForm({ onSubmit, isLoading }: FixedAssetFormProps) {
  const form = useForm<FixedAssetFormValues>({
    resolver: zodResolver(fixedAssetSchema),
    defaultValues: {
      codice: '',
      descrizione: '',
      categoria: '',
      costo_storico: '',
      data_acquisto: new Date().toISOString().split('T')[0],
      aliquota_ammortamento: '',
      metodo: 'quote_costanti',
    },
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="codice"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Codice *</FormLabel>
                <FormControl>
                  <Input placeholder="es. ATT-001" maxLength={20} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="categoria"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Categoria *</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleziona..." />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {CATEGORIE.map((c) => (
                      <SelectItem key={c} value={c}>
                        {c}
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
                <Input placeholder="Descrizione del cespite" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="costo_storico"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Costo Storico (€) *</FormLabel>
                <FormControl>
                  <Input type="number" step="0.01" min="0" placeholder="0.00" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="data_acquisto"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Data Acquisto *</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="aliquota_ammortamento"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Aliquota Ammortamento (%) *</FormLabel>
                <FormControl>
                  <Input type="number" step="0.01" min="0" max="100" placeholder="es. 20" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="metodo"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Metodo</FormLabel>
                <Select onValueChange={field.onChange} value={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="quote_costanti">Quote Costanti</SelectItem>
                    <SelectItem value="decrescente">Decrescente</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" disabled={isLoading}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Salva Cespite
          </Button>
        </div>
      </form>
    </Form>
  )
}
