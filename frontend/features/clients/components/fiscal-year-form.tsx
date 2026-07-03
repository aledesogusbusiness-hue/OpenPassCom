'use client'

import { useEffect } from 'react'
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

const fiscalYearSchema = z.object({
  anno: z.coerce
    .number()
    .int()
    .min(2000, 'Anno non valido')
    .max(2100, 'Anno non valido'),
  data_inizio: z.string().min(1, 'Data inizio obbligatoria'),
  data_fine: z.string().min(1, 'Data fine obbligatoria'),
})

type FiscalYearFormValues = z.infer<typeof fiscalYearSchema>

interface FiscalYearFormProps {
  onSubmit: (data: FiscalYearFormValues) => Promise<void>
  isLoading?: boolean
}

export function FiscalYearForm({ onSubmit, isLoading }: FiscalYearFormProps) {
  const currentYear = new Date().getFullYear()

  const form = useForm<FiscalYearFormValues>({
    resolver: zodResolver(fiscalYearSchema),
    defaultValues: {
      anno: currentYear,
      data_inizio: `${currentYear}-01-01`,
      data_fine: `${currentYear}-12-31`,
    },
  })

  const anno = form.watch('anno')

  useEffect(() => {
    const y = Number(anno)
    if (Number.isInteger(y) && y >= 2000 && y <= 2100) {
      form.setValue('data_inizio', `${y}-01-01`)
      form.setValue('data_fine', `${y}-12-31`)
    }
  }, [anno, form])

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="anno"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Anno *</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  placeholder={String(currentYear)}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <FormField
            control={form.control}
            name="data_inizio"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Data Inizio</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="data_fine"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Data Fine</FormLabel>
                <FormControl>
                  <Input type="date" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="flex justify-end pt-2">
          <Button type="submit" disabled={isLoading}>
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Crea Esercizio
          </Button>
        </div>
      </form>
    </Form>
  )
}
