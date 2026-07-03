'use client'

import { useEffect, useRef, useState, KeyboardEvent } from 'react'
import { AlertCircle, Info, Send, Square, Trash2 } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useAIChat } from '../hooks/use-ai-chat'
import { getAIProvider } from '../adapter'
import { ChatMessage } from './chat-message'

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3 py-2">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="h-2 w-2 rounded-full bg-muted-foreground/50 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  )
}

export function ChatPanel() {
  const { messages, isLoading, error, sendMessage, clearChat, stopGeneration } = useAIChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const provider = getAIProvider()
  const configured = provider.isConfigured()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return
    setInput('')
    textareaRef.current?.focus()
    await sendMessage(trimmed)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Escape') {
      stopGeneration()
      return
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 96)}px`
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold">Assistente AI</h2>
          <Badge variant="secondary" className="text-[10px]">
            {provider.name}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={clearChat}
          title="Cancella conversazione"
          disabled={messages.length === 0}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      {/* Setup info card */}
      {!configured && messages.length === 0 && (
        <div className="mx-4 mt-4 flex gap-2 rounded-lg border border-blue-200 bg-blue-50 p-3 text-xs text-blue-800 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300">
          <Info className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            Scrivi un messaggio per vedere le istruzioni di configurazione del provider AI.
          </p>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-3 p-4">
          {messages.map(msg => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
          {isLoading && messages.at(-1)?.content === '' && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {/* Error banner */}
      {error && (
        <div className="mx-4 mb-2 flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Input */}
      <div className="border-t p-3">
        <div className="flex items-end gap-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={e => {
              setInput(e.target.value)
              handleInput()
            }}
            onKeyDown={handleKeyDown}
            placeholder="Scrivi un messaggio… (Invio per inviare, Shift+Invio per andare a capo)"
            className="min-h-[40px] resize-none text-sm"
            rows={1}
            style={{ height: '40px' }}
            disabled={isLoading && !configured}
          />
          {isLoading ? (
            <Button
              size="icon"
              variant="outline"
              className="h-10 w-10 shrink-0"
              onClick={stopGeneration}
              title="Interrompi generazione (Esc)"
            >
              <Square className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              size="icon"
              className="h-10 w-10 shrink-0"
              onClick={handleSend}
              disabled={!input.trim()}
              title="Invia messaggio"
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
        <p className="mt-1.5 text-center text-[10px] text-muted-foreground">
          Invio per inviare · Shift+Invio per andare a capo · Esc per interrompere
        </p>
      </div>
    </div>
  )
}
