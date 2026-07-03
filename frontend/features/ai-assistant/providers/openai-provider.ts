import type { AIProvider, Message } from '../types'

export class OpenAIProvider implements AIProvider {
  name = 'OpenAI'

  private get baseUrl(): string {
    return (process.env.NEXT_PUBLIC_AI_API_URL ?? '').replace(/\/$/, '')
  }

  private get apiKey(): string {
    return process.env.NEXT_PUBLIC_AI_API_KEY ?? ''
  }

  private get model(): string {
    return process.env.NEXT_PUBLIC_AI_MODEL ?? 'gpt-4o-mini'
  }

  isConfigured(): boolean {
    return !!process.env.NEXT_PUBLIC_AI_API_URL
  }

  async sendMessage(
    messages: Message[],
    onChunk: (chunk: string) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey ? { Authorization: `Bearer ${this.apiKey}` } : {}),
      },
      body: JSON.stringify({
        model: this.model,
        messages: messages.map(m => ({ role: m.role, content: m.content })),
        stream: true,
      }),
      signal,
    })

    if (!response.ok) {
      const text = await response.text().catch(() => response.statusText)
      throw new Error(`AI request failed (${response.status}): ${text}`)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No response body')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data:')) continue
        const data = trimmed.slice(5).trim()
        if (data === '[DONE]') return

        try {
          const json = JSON.parse(data)
          const delta = json.choices?.[0]?.delta?.content
          if (delta) onChunk(delta)
        } catch {
          // ignore malformed SSE lines
        }
      }
    }
  }
}
