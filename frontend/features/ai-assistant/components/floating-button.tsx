'use client'

import { useEffect, useState } from 'react'
import { Bot } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetTitle,
} from '@/components/ui/sheet'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { useAIChat } from '../hooks/use-ai-chat'
import { ChatPanel } from './chat-panel'

export function AIAssistantButton() {
  const [open, setOpen] = useState(false)
  const { isLoading } = useAIChat()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'K') {
        e.preventDefault()
        setOpen(prev => !prev)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <>
      <Sheet open={open} onOpenChange={setOpen}>
        <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={() => setOpen(true)}
              aria-label="Apri Assistente AI"
              className={cn(
                'fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full',
                'bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-lg',
                'transition-transform hover:scale-110 focus:outline-none focus-visible:ring-2',
                'focus-visible:ring-blue-500 focus-visible:ring-offset-2'
              )}
            >
              {isLoading && (
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-40" />
              )}
              <Bot className="h-6 w-6" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="left">
            <p>Assistente AI (Ctrl+Shift+K)</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

        <SheetContent
          side="right"
          className="flex w-[420px] flex-col p-0 sm:max-w-[420px]"
        >
          <SheetTitle className="sr-only">Assistente AI OpenPassCom</SheetTitle>
          <ChatPanel />
        </SheetContent>
      </Sheet>
    </>
  )
}

export { AIAssistantButton as FloatingAIButton }
