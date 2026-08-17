import { ProjectsSidebar } from "@/components/main/projects-sidebar"
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"

export default function Page() {
  return (
    <>
      <ProjectsSidebar />
      <SidebarInset>
        <header className="sticky top-0 flex h-14 shrink-0 items-center gap-2 bg-background">
          <div className="flex flex-1 items-center gap-2 px-3">
            <SidebarTrigger />
          </div>
        </header>
        <div className="flex h-[50%] w-full items-center justify-center text-xl">
          Start by selecting a project.
        </div>
      </SidebarInset>
    </>
  )
}
