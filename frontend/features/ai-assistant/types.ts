export type MessageRole = 'user' | 'assistant' | 'system'

export interface Message {
  id: string
  role: MessageRole
  content: string
  timestamp: Date
}

export interface AITool {
  name: string
  description: string
  parameters: Record<string, unknown>
}

export interface AIProvider {
  name: string
  isConfigured(): boolean
  sendMessage(messages: Message[], onChunk: (chunk: string) => void, signal?: AbortSignal): Promise<void>
  listTools?(): AITool[]
}
