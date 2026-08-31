// api/chat.ts

import { client } from "@/api/axios-client"
import { endpoints } from "@/api/endpoints"
import { useMutation } from "@tanstack/react-query"

type ChatRequest = {
  question: string
  project_id?: string
  project_name?: string
}

export type ChatResponse = {
  project: {
    id: string
    name: string
  }
  id: string
  role: "user" | "assistant"
  content: string
  generated_code?: string
  route?: string
  execution_result?: string
  chart?: Record<string, unknown>
  created_at?: string
}

async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const { data } = await client.post<ChatResponse>(`${endpoints.chat}`, request)

  return data
}

export function useSendMessage() {
  return useMutation({
    mutationFn: (request: ChatRequest) => sendMessage(request),
  })
}
