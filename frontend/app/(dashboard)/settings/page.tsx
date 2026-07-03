'use client'

import { useState } from 'react'
import { Copy, Check, ExternalLink } from 'lucide-react'
import { PageHeader } from '@/components/shared/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/theme-toggle'

const APP_VERSION = '0.1.0'
const GITHUB_URL = 'https://github.com/openpasscom/registro-contabilita'

const ENV_VARS = [
  {
    name: 'NEXT_PUBLIC_AI_PROVIDER',
    description: 'Provider AI da utilizzare (es. openai, anthropic)',
    example: 'openai',
  },
  {
    name: 'NEXT_PUBLIC_AI_API_URL',
    description: 'URL base delle API del provider',
    example: 'https://api.openai.com/v1',
  },
  {
    name: 'NEXT_PUBLIC_AI_API_KEY',
    description: "Chiave API per l'autenticazione",
    example: 'sk-...',
  },
] as const

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      className="h-7 w-7 shrink-0"
      onClick={handleCopy}
      aria-label={`Copia ${text}`}
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-green-600" />
      ) : (
        <Copy className="h-3.5 w-3.5" />
      )}
    </Button>
  )
}

export default function SettingsPage() {
  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title="Impostazioni"
        description="Configurazione dell'applicazione OpenPassCom"
      />

      <Tabs defaultValue="generale">
        <TabsList>
          <TabsTrigger value="generale">Generale</TabsTrigger>
          <TabsTrigger value="ai">Assistente AI</TabsTrigger>
          <TabsTrigger value="info">Informazioni</TabsTrigger>
        </TabsList>

        {/* Generale */}
        <TabsContent value="generale" className="mt-4 space-y-6">
          <div className="rounded-lg border bg-card p-6 space-y-5">
            <div>
              <h2 className="text-sm font-semibold mb-1">Tema</h2>
              <p className="text-sm text-muted-foreground mb-3">
                Scegli tra tema chiaro, scuro o automatico in base alle preferenze di sistema.
              </p>
              <div className="flex items-center gap-3">
                <ThemeToggle />
                <span className="text-sm text-muted-foreground">
                  Clicca l&apos;icona per ciclare tra chiaro, scuro e sistema
                </span>
              </div>
            </div>

            <Separator />

            <div>
              <h2 className="text-sm font-semibold mb-1">Studio</h2>
              <p className="text-sm text-muted-foreground">
                Le informazioni dello studio si configurano nella sezione{' '}
                <span className="font-medium text-foreground">Studio</span> dal menu laterale.
              </p>
            </div>
          </div>
        </TabsContent>

        {/* Assistente AI */}
        <TabsContent value="ai" className="mt-4 space-y-4">
          <div className="rounded-lg border bg-card p-6 space-y-4">
            <div>
              <h2 className="text-sm font-semibold">Configurazione Assistente AI</h2>
              <p className="text-sm text-muted-foreground mt-1">
                L&apos;assistente AI si configura tramite variabili d&apos;ambiente nel file{' '}
                <code className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">.env.local</code>{' '}
                nella root del progetto. Riavvia il server dopo aver apportato modifiche.
              </p>
            </div>

            <Separator />

            <div className="space-y-3">
              {ENV_VARS.map((v) => (
                <div
                  key={v.name}
                  className="flex items-start gap-3 rounded-md border bg-muted/30 p-3"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <code className="text-sm font-mono font-semibold">{v.name}</code>
                      <CopyButton text={v.name} />
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{v.description}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Esempio:{' '}
                      <code className="font-mono text-xs bg-muted px-1 rounded">
                        {v.example}
                      </code>
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="rounded-md border border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-950 p-3 text-sm text-yellow-800 dark:text-yellow-200">
              Imposta queste variabili nel file{' '}
              <code className="font-mono text-xs">.env.local</code> e riavvia il server di
              sviluppo. Non includere il file <code className="font-mono text-xs">.env.local</code>{' '}
              nel controllo versione.
            </div>
          </div>
        </TabsContent>

        {/* Informazioni */}
        <TabsContent value="info" className="mt-4">
          <div className="rounded-lg border bg-card p-6 space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold">OpenPassCom</h2>
                <p className="text-sm text-muted-foreground mt-0.5">
                  Software di contabilità per studi professionali
                </p>
              </div>
              <Badge variant="outline" className="font-mono text-xs">
                v{APP_VERSION}
              </Badge>
            </div>

            <Separator />

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Versione</span>
                <span className="font-mono tabular-nums">{APP_VERSION}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Licenza</span>
                <span>MIT</span>
              </div>
            </div>

            <Separator />

            <div>
              <Button variant="outline" size="sm" asChild>
                <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="h-3.5 w-3.5" />
                  Apri su GitHub
                </a>
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
