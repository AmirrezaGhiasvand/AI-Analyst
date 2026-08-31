// components/main/chat-store.tsx
"use client"

import { createContext, useContext, useState, type ReactNode } from "react"
import { useSendMessage } from "@/hooks/query/use-send-message"
import { deriveProjectName } from "@/lib/utils"

export type ChatMessage = {
  id: string
  role: "user" | "assistant"
  content: string
  generated_code?: string
  route?: string
  execution_result?: string
  chart?: Record<string, unknown>
  created_at?: string
}

type ChatContextValue = {
  messages: ChatMessage[]
  isBusy: boolean
  sendMessage: (
    question: string,
    projectId?: string
  ) => Promise<{
    project: {
      id: string
    }
  }>
  resetMessages: (projectId: string) => void
}

const ChatContext = createContext<ChatContextValue | null>(null)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null)
  const sendMessageMutation = useSendMessage()

  async function sendMessage(question: string, projectId?: string) {
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: question },
    ])

    const response = await sendMessageMutation.mutateAsync({
      question,
      project_id: projectId,
      ...(projectId ? {} : { project_name: deriveProjectName(question) }), // generate project name when there is no project id
    })

    const resolvedProjectId = projectId ?? response.project.id

    setMessages((prev) => [
      ...prev,
      {
        id: response.id,
        role: "assistant",
        content: response.content,
        generated_code: response.generated_code,
        route: response.route,
        execution_result: response.execution_result,
        chart: response.chart,
        created_at: response.created_at,
      },
    ])

    setCurrentProjectId(resolvedProjectId)

    return response
  }

  function resetMessages(projectId: string) {
    // idempotent: safe to call more than once with the same projectId
    // (e.g. React Strict Mode double-invoking effects in dev)
    if (currentProjectId === projectId) {
      return
    }
    setMessages([])
    setCurrentProjectId(projectId)
  }

  return (
    <ChatContext.Provider
      value={{
        messages,
        isBusy: sendMessageMutation.isPending,
        sendMessage,
        resetMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  )
}

export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error("useChat must be used within a ChatProvider")
  return ctx
}
