'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Check, Copy } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatDateTime } from '@/lib/utils'
import type { Message } from '../types'

interface CodeBlockProps {
  children?: React.ReactNode
  className?: string
}

function CodeBlock({ children, className }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)
  const code = String(children).replace(/\n$/, '')
  const isBlock = className?.startsWith('language-')

  if (!isBlock) {
    return (
      <code className="rounded bg-muted px-1 py-0.5 font-mono text-sm">
        {children}
      </code>
    )
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative my-2 rounded-md bg-zinc-900 dark:bg-zinc-950">
      <button
        onClick={handleCopy}
        className="absolute right-2 top-2 rounded p-1 text-zinc-400 transition-colors hover:bg-zinc-700 hover:text-zinc-100"
        aria-label="Copia codice"
      >
        {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      </button>
      <pre className="overflow-x-auto p-4 pr-10 font-mono text-sm text-zinc-100">
        <code>{code}</code>
      </pre>
    </div>
  )
}

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex w-full gap-2', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[85%] rounded-2xl px-3 py-2 text-sm',
          isUser
            ? 'rounded-br-sm bg-blue-600 text-white'
            : 'rounded-bl-sm bg-muted text-foreground'
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none break-words">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code: ({ className, children }) => (
                  <CodeBlock className={className}>{children}</CodeBlock>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        <p
          className={cn(
            'mt-1 text-[10px]',
            isUser ? 'text-blue-200' : 'text-muted-foreground'
          )}
        >
          {formatDateTime(message.timestamp.toISOString())}
        </p>
      </div>
    </div>
  )
}
