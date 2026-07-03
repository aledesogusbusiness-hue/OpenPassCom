'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { useAuth } from '@/providers/auth-provider'
import { Loader2 } from 'lucide-react'

const loginSchema = z.object({
  email: z.string().email('Inserisci un indirizzo email valido').min(1, 'Email obbligatoria'),
  password: z.string().min(1, 'Password obbligatoria'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  async function onSubmit(data: LoginFormValues) {
    setIsSubmitting(true)
    try {
      await login(data.email, data.password)
      router.push('/dashboard')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Errore durante il login')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="w-full max-w-[400px] mx-auto">
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-8">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg mb-3"
            style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #7c3aed 100%)' }}
          >
            OP
          </div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
            OpenPassCom
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Gestionale per commercialisti
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              {...register('email')}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent text-sm transition-colors"
              placeholder="nome@studio.it"
              disabled={isSubmitting}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                {errors.email.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register('password')}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent text-sm transition-colors"
              placeholder="••••••••"
              disabled={isSubmitting}
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                {errors.password.message}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium text-white transition-opacity disabled:opacity-70"
            style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #7c3aed 100%)' }}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Accesso in corso...
              </>
            ) : (
              'Accedi'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
