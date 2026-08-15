import { ProjectsSidebar } from "@/components/main/projects-sidebar"
import { AIChatSidebar } from "@/components/main/ai-chat-sidebar"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"

export default function Page() {
  return (
    <SidebarProvider>
      <ProjectsSidebar />
      <SidebarInset>
        <header className="sticky top-0 flex h-14 shrink-0 items-center gap-2 bg-background">
          <div className="flex flex-1 items-center gap-2 px-3">
            <SidebarTrigger />
            <Separator orientation="vertical" className="mr-2" />
            <span>Sample Project</span>
          </div>
        </header>
        <div className="flex h-[50%] w-full items-center justify-center text-xl">
          Ask the AI to generate some charts.
        </div>
      </SidebarInset>
      <AIChatSidebar />
    </SidebarProvider>
  )
}
