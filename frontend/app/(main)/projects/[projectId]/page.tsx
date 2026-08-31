"use client"
import { ProjectsSidebar } from "@/components/main/projects-sidebar"
import { AIChatSidebar } from "@/components/main/ai-chat-sidebar"
import { Separator } from "@/components/ui/separator"
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"
import { useGetProject } from "@/hooks/query/use-get-project"
import { use, useEffect } from "react"
import { ChartsPanel } from "@/components/main/charts-panel"
import { useChat } from "@/context/chat-store"

type Props = {
  params: Promise<{
    projectId: string
  }>
}

export default function Page({ params }: Props) {
  const { projectId } = use(params)

  const { data: project } = useGetProject(projectId)

  const { resetMessages } = useChat()

  useEffect(() => {
    resetMessages(projectId)
  }, [projectId])

  return (
    <>
      <ProjectsSidebar />
      <AIChatSidebar projectId={projectId} />
      <SidebarInset>
        <header className="sticky top-0 flex h-14 shrink-0 items-center gap-2 bg-background">
          <div className="flex flex-1 items-center gap-2 px-3">
            <span className="hidden font-semibold md:block">AI Analyst</span>
            <SidebarTrigger className="md:hidden" />
            <Separator orientation="vertical" className="mr-2" />
            <span>{project?.name}</span>
          </div>
        </header>
        <ChartsPanel />
      </SidebarInset>
    </>
  )
}
