'use client'

import { useState, useCallback, useRef } from 'react'
import { getAIProvider } from '../adapter'
import type { Message } from '../types'

export function useAIChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(
    async (content: string) => {
      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        timestamp: new Date(),
      }
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, userMsg, assistantMsg])
      setIsLoading(true)
      setError(null)

      abortRef.current = new AbortController()
      const provider = getAIProvider()

      try {
        await provider.sendMessage(
          [...messages, userMsg],
          chunk => {
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMsg.id ? { ...m, content: m.content + chunk } : m
              )
            )
          },
          abortRef.current.signal
        )
      } catch (e) {
        if (e instanceof Error && e.name !== 'AbortError') {
          setError(e.message)
        }
      } finally {
        setIsLoading(false)
      }
    },
    [messages]
  )

  const clearChat = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  return { messages, isLoading, error, sendMessage, clearChat, stopGeneration }
}
