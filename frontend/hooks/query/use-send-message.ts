// api/chat.ts

import { client } from "@/api/axios-client"
import { endpoints } from "@/api/endpoints"
import { useMutation } from "@tanstack/react-query"

type ChatRequest = {
  question: string
}

type ChatResponse = {
  message_id: string
  role: string
  content: string
  generated_code: string
  route: string
  execution_result: string
  chart: Record<string, unknown>
  created_at: string
}

async function sendMessage(
  request: ChatRequest,
  projectId?: string
): Promise<ChatResponse> {
  const { data } = await client.post<ChatResponse>(
    `${endpoints.projects}/${projectId}/chat`,
    request
  )

  return data
}

export function useSendMessage(projectId?: string) {
  return useMutation({
    mutationFn: (request: ChatRequest) => sendMessage(request, projectId),
  })
}
