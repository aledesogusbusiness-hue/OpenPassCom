import type { AIProvider, Message } from '../types'

export class NullProvider implements AIProvider {
  name = 'Non configurato'

  isConfigured() {
    return false
  }

  async sendMessage(_messages: Message[], onChunk: (chunk: string) => void): Promise<void> {
    const msg =
      "Assistente AI non configurato. Per attivarlo, imposta le seguenti variabili in **.env.local** e riavvia il server:\n\n```\nNEXT_PUBLIC_AI_PROVIDER=openai\nNEXT_PUBLIC_AI_API_URL=https://api.openai.com/v1\nNEXT_PUBLIC_AI_API_KEY=sk-...\n```\n\nProvider supportati: OpenAI, Azure OpenAI, Ollama, LM Studio, OpenRouter."
    for (const ch of msg) {
      onChunk(ch)
      await new Promise(r => setTimeout(r, 8))
    }
  }
}
