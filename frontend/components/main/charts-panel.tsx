// components/main/charts-panel.tsx
"use client"

import { useChat } from "@/context/chat-store"
import { ChartSpec, DynamicChart } from "./dynamic-chart"

export function ChartsPanel() {
  const { messages } = useChat()

  const charts = messages
    .filter((m) => m.role === "assistant" && m.chart)
    .map((m) => ({ id: m.id, spec: m.chart as ChartSpec }))

  if (charts.length === 0) {
    return (
      <div className="flex h-[50%] w-full items-center justify-center text-xl text-muted-foreground">
        Ask the AI to generate some charts.
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 overflow-y-auto p-4">
      {charts.map((c) => (
        <DynamicChart key={c.id} spec={c.spec} />
      ))}
    </div>
  )
}
