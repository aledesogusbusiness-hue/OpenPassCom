import { NullProvider } from './providers/null-provider'
import { OpenAIProvider } from './providers/openai-provider'
import type { AIProvider } from './types'

let _provider: AIProvider | null = null

export function getAIProvider(): AIProvider {
  if (_provider) return _provider

  const providerName = process.env.NEXT_PUBLIC_AI_PROVIDER ?? 'null'

  if (
    providerName === 'openai' ||
    providerName === 'azure' ||
    providerName === 'ollama' ||
    providerName === 'openrouter' ||
    providerName === 'lmstudio'
  ) {
    _provider = new OpenAIProvider()
  } else {
    _provider = new NullProvider()
  }

  return _provider
}
